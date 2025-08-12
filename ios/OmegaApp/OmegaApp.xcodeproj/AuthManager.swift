import Foundation
import SwiftUI
import Security

@MainActor
class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var user: User?
    @Published var isLoading = false
    @Published var error: AuthError?
    
    static let shared = AuthManager()
    
    private let keychainService = "com.omega.OmegaApp"
    private let tokenKey = "auth_token"
    private let userKey = "user_data"
    
    var token: String? {
        return getTokenFromKeychain()
    }
    
    init() {
        checkAuthStatus()
    }
    
    // MARK: - Authentication Methods
    
    func login(username: String, password: String) async {
        isLoading = true
        error = nil
        
        do {
            let apiClient = OmegaAPIClient()
            apiClient.configure(baseURL: "http://127.0.0.1:8001") // FORZAR puerto 8001
            
            let authResponse = try await apiClient.login(username: username, password: password)
            
            // Guardar token en keychain
            saveTokenToKeychain(authResponse.accessToken)
            
            // Crear usuario
            let user = User(
                username: username,
                role: "admin", // Por ahora hardcodeado
                tokenType: authResponse.tokenType
            )
            
            // Guardar usuario
            saveUserToKeychain(user)
            
            // Actualizar estado
            self.user = user
            self.isAuthenticated = true
            
        } catch {
            self.error = AuthError.loginFailed(error.localizedDescription)
        }
        
        isLoading = false
    }
    
    func logout() {
        // Limpiar keychain
        deleteTokenFromKeychain()
        deleteUserFromKeychain()
        
        // Limpiar estado
        user = nil
        isAuthenticated = false
        error = nil
    }
    
    func checkAuthStatus() {
        if let token = getTokenFromKeychain(),
           let user = getUserFromKeychain(),
           !isTokenExpired(token) {
            self.user = user
            self.isAuthenticated = true
        } else {
            logout()
        }
    }
    
    // MARK: - Biometric Authentication
    
    func authenticateWithBiometrics() async -> Bool {
        guard isBiometricsAvailable() else {
            error = AuthError.biometricsNotAvailable
            return false
        }
        
        do {
            let success = try await performBiometricAuthentication()
            if success {
                checkAuthStatus()
            }
            return success
        } catch {
            self.error = AuthError.biometricsFailed(error.localizedDescription)
            return false
        }
    }
    
    private func isBiometricsAvailable() -> Bool {
        // Implementar verificación de Face ID/Touch ID
        // Por ahora retornamos true como placeholder
        return true
    }
    
    private func performBiometricAuthentication() async throws -> Bool {
        // Implementar autenticación biométrica real
        // Por ahora simulamos éxito
        try await Task.sleep(nanoseconds: 1_000_000_000) // 1 segundo
        return true
    }
    
    // MARK: - Token Management
    
    private func isTokenExpired(_ token: String) -> Bool {
        // Decodificar JWT y verificar expiración
        // Por simplicidad, asumimos que los tokens no expiran en desarrollo
        return false
    }
    
    private func saveTokenToKeychain(_ token: String) {
        let data = token.data(using: .utf8)!
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: tokenKey,
            kSecValueData as String: data
        ]
        
        // Eliminar token existente
        SecItemDelete(query as CFDictionary)
        
        // Agregar nuevo token
        SecItemAdd(query as CFDictionary, nil)
    }
    
    private func getTokenFromKeychain() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: tokenKey,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            return nil
        }
        
        return token
    }
    
    private func deleteTokenFromKeychain() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: tokenKey
        ]
        
        SecItemDelete(query as CFDictionary)
    }
    
    // MARK: - User Management
    
    private func saveUserToKeychain(_ user: User) {
        guard let data = try? JSONEncoder().encode(user) else { return }
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: userKey,
            kSecValueData as String: data
        ]
        
        // Eliminar usuario existente
        SecItemDelete(query as CFDictionary)
        
        // Agregar nuevo usuario
        SecItemAdd(query as CFDictionary, nil)
    }
    
    private func getUserFromKeychain() -> User? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: userKey,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
              let data = result as? Data,
              let user = try? JSONDecoder().decode(User.self, from: data) else {
            return nil
        }
        
        return user
    }
    
    private func deleteUserFromKeychain() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: userKey
        ]
        
        SecItemDelete(query as CFDictionary)
    }
}

// MARK: - Models

struct User: Codable {
    let username: String
    let role: String
    let tokenType: String
    
    private enum CodingKeys: String, CodingKey {
        case username, role
        case tokenType = "token_type"
    }
}

// MARK: - Error Types

enum AuthError: LocalizedError {
    case loginFailed(String)
    case logoutFailed(String)
    case biometricsNotAvailable
    case biometricsFailed(String)
    case tokenExpired
    case invalidCredentials
    case networkError
    case unknown(String)
    
    var errorDescription: String? {
        switch self {
        case .loginFailed(let message):
            return "Error de inicio de sesión: \(message)"
        case .logoutFailed(let message):
            return "Error al cerrar sesión: \(message)"
        case .biometricsNotAvailable:
            return "La autenticación biométrica no está disponible"
        case .biometricsFailed(let message):
            return "Error de autenticación biométrica: \(message)"
        case .tokenExpired:
            return "La sesión ha expirado"
        case .invalidCredentials:
            return "Credenciales inválidas"
        case .networkError:
            return "Error de conexión"
        case .unknown(let message):
            return "Error desconocido: \(message)"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .loginFailed, .invalidCredentials:
            return "Verifica tu usuario y contraseña"
        case .biometricsNotAvailable:
            return "Usa tu contraseña para iniciar sesión"
        case .biometricsFailed:
            return "Intenta nuevamente o usa tu contraseña"
        case .tokenExpired:
            return "Inicia sesión nuevamente"
        case .networkError:
            return "Verifica tu conexión a internet"
        default:
            return "Intenta nuevamente o contacta soporte"
        }
    }
}
