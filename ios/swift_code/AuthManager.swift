import Foundation
import SwiftUI
import Security
import LocalAuthentication

@MainActor
class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var user: User?
    @Published var isLoading = false
    @Published var error: AuthError?
    @Published var biometricAuthAvailable = false
    
    static let shared = AuthManager()
    
    private let securityManager = SecurityManager.shared
    private var failedAttempts = 0
    private var lockoutExpiration: Date?
    
    var token: String? {
        return securityManager.getToken()
    }
    
    var isTokenValid: Bool {
        return securityManager.isTokenValid()
    }
    
    init() {
        Task {
            await initializeAuth()
        }
    }
    
    private func initializeAuth() async {
        // Check app integrity first
        guard securityManager.validateAppIntegrity() else {
            await MainActor.run {
                self.error = AuthError.securityCheckFailed
            }
            return
        }
        
        // Check biometric availability
        await MainActor.run {
            self.biometricAuthAvailable = securityManager.isBiometricAuthenticationAvailable()
        }
        
        // Check existing auth status
        await checkAuthStatus()
    }
    
    // MARK: - Authentication Methods
    
    func login(username: String, password: String) async {
        // Validate input
        guard validateLoginInput(username: username, password: password) else {
            return
        }
        
        // Check lockout status
        if isLockedOut() {
            error = AuthError.accountLocked(getRemainingLockoutTime())
            return
        }
        
        isLoading = true
        error = nil
        
        do {
            let apiClient = OmegaAPIClient()
            let authResponse = try await apiClient.login(username: username, password: password)
            
            // Validate and store token
            try securityManager.storeToken(authResponse.accessToken)
            
            // Create and store user
            let user = User(
                id: extractUserIdFromToken(authResponse.accessToken),
                username: username,
                role: extractRoleFromToken(authResponse.accessToken),
                tokenType: authResponse.tokenType
            )
            
            try await storeUserSecurely(user)
            
            // Update state
            self.user = user
            self.isAuthenticated = true
            self.failedAttempts = 0
            
            // Log successful authentication
            AppLogger.shared.info("User authenticated successfully", category: .auth, metadata: [
                "username": username,
                "biometric_available": biometricAuthAvailable
            ])
            
        } catch {
            await handleAuthenticationError(error)
        }
        
        isLoading = false
    }
    
    func logout() async {
        do {
            try securityManager.clearAllSecureData()
        } catch {
            AppLogger.shared.error("Failed to clear secure data during logout", category: .auth, error: error)
        }
        
        // Clear state
        user = nil
        isAuthenticated = false
        error = nil
        failedAttempts = 0
        lockoutExpiration = nil
        
        AppLogger.shared.info("User logged out successfully", category: .auth)
    }
    
    func checkAuthStatus() async {
        guard securityManager.isTokenValid() else {
            await logout()
            return
        }
        
        do {
            if let userData = try securityManager.retrieve(key: AppConfig.Auth.userDataKey),
               let user = try JSONDecoder().decode(User.self, from: userData) {
                
                await MainActor.run {
                    self.user = user
                    self.isAuthenticated = true
                }
            } else {
                await logout()
            }
        } catch {
            AppLogger.shared.error("Failed to retrieve user data", category: .auth, error: error)
            await logout()
        }
    }
    
    // MARK: - Biometric Authentication
    
    func authenticateWithBiometrics() async -> Bool {
        guard biometricAuthAvailable else {
            error = AuthError.biometricsNotAvailable
            return false
        }
        
        guard !isLockedOut() else {
            error = AuthError.accountLocked(getRemainingLockoutTime())
            return false
        }
        
        do {
            let reason = "Accede a OMEGA con \(getBiometricTypeString())"
            let success = try await securityManager.authenticateWithBiometrics(reason: reason)
            
            if success {
                await checkAuthStatus()
                failedAttempts = 0
                AppLogger.shared.info("Biometric authentication successful", category: .auth)
                return true
            } else {
                await handleBiometricFailure()
                return false
            }
        } catch {
            await handleBiometricFailure()
            self.error = AuthError.biometricsFailed(error.localizedDescription)
            return false
        }
    }
    
    func getBiometricTypeString() -> String {
        switch securityManager.biometricType() {
        case .faceID:
            return "Face ID"
        case .touchID:
            return "Touch ID"
        default:
            return "autenticación biométrica"
        }
    }
    
    // MARK: - Private Helper Methods
    
    private func validateLoginInput(username: String, password: String) -> Bool {
        guard !username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            error = AuthError.invalidCredentials
            return false
        }
        
        guard password.count >= 6 else {
            error = AuthError.invalidCredentials
            return false
        }
        
        return true
    }
    
    private func isLockedOut() -> Bool {
        guard let lockoutExpiration = lockoutExpiration else {
            return false
        }
        return Date() < lockoutExpiration
    }
    
    private func getRemainingLockoutTime() -> TimeInterval {
        guard let lockoutExpiration = lockoutExpiration else {
            return 0
        }
        return max(0, lockoutExpiration.timeIntervalSince(Date()))
    }
    
    private func handleAuthenticationError(_ error: Error) async {
        failedAttempts += 1
        
        if failedAttempts >= AppConfig.Security.maxFailedAttempts {
            lockoutExpiration = Date().addingTimeInterval(
                TimeInterval(AppConfig.Security.lockoutDurationMinutes * 60)
            )
            await MainActor.run {
                self.error = AuthError.accountLocked(getRemainingLockoutTime())
            }
            AppLogger.shared.warning("Account locked due to failed attempts", category: .auth, metadata: [
                "failed_attempts": failedAttempts
            ])
        } else {
            await MainActor.run {
                self.error = AuthError.loginFailed(error.localizedDescription)
            }
        }
        
        AppLogger.shared.error("Authentication failed", category: .auth, error: error, metadata: [
            "attempt": failedAttempts
        ])
    }
    
    private func handleBiometricFailure() async {
        failedAttempts += 1
        
        if failedAttempts >= AppConfig.Security.maxFailedAttempts {
            lockoutExpiration = Date().addingTimeInterval(
                TimeInterval(AppConfig.Security.lockoutDurationMinutes * 60)
            )
        }
        
        AppLogger.shared.warning("Biometric authentication failed", category: .auth, metadata: [
            "attempt": failedAttempts
        ])
    }
    
    private func extractUserIdFromToken(_ token: String) -> String {
        do {
            let jwtToken = try JWTDecoder.decode(token)
            return jwtToken.userID ?? "unknown"
        } catch {
            return "unknown"
        }
    }
    
    private func extractRoleFromToken(_ token: String) -> String {
        do {
            let jwtToken = try JWTDecoder.decode(token)
            return jwtToken.roles.first ?? "user"
        } catch {
            return "user"
        }
    }
    
    private func storeUserSecurely(_ user: User) async throws {
        let userData = try JSONEncoder().encode(user)
        let encryptedData = try securityManager.encrypt(userData)
        try securityManager.store(encryptedData, forKey: AppConfig.Auth.userDataKey)
    }
    
    // MARK: - Token Refresh
    
    func refreshTokenIfNeeded() async {
        guard isAuthenticated, let token = securityManager.getToken() else {
            return
        }
        
        do {
            let jwtToken = try JWTDecoder.decode(token)
            
            // Check if token expires within buffer time
            let bufferTime = AppConfig.Auth.tokenExpirationBuffer
            guard let expirationDate = jwtToken.expirationDate,
                  Date().addingTimeInterval(bufferTime) >= expirationDate else {
                return
            }
            
            // Attempt token refresh
            let apiClient = OmegaAPIClient()
            let refreshResponse = try await apiClient.refreshToken()
            try securityManager.storeToken(refreshResponse.accessToken)
            
            AppLogger.shared.info("Token refreshed successfully", category: .auth)
            
        } catch {
            AppLogger.shared.error("Token refresh failed", category: .auth, error: error)
            await logout()
        }
    }
    
    // MARK: - Session Management
    
    func validateSession() async -> Bool {
        guard isAuthenticated else {
            return false
        }
        
        // Check token validity
        guard securityManager.isTokenValid() else {
            await logout()
            return false
        }
        
        // Refresh token if needed
        await refreshTokenIfNeeded()
        
        return isAuthenticated
    }
}

// MARK: - Models

struct User: Codable, Identifiable {
    let id: String
    let username: String
    let role: String
    let tokenType: String
    let createdAt: Date
    let lastLoginAt: Date
    
    init(id: String, username: String, role: String, tokenType: String) {
        self.id = id
        self.username = username
        self.role = role
        self.tokenType = tokenType
        self.createdAt = Date()
        self.lastLoginAt = Date()
    }
    
    private enum CodingKeys: String, CodingKey {
        case id, username, role
        case tokenType = "token_type"
        case createdAt = "created_at"
        case lastLoginAt = "last_login_at"
    }
}

// MARK: - Error Types

enum AuthError: LocalizedError, Equatable {
    case loginFailed(String)
    case logoutFailed(String)
    case biometricsNotAvailable
    case biometricsFailed(String)
    case tokenExpired
    case invalidCredentials
    case accountLocked(TimeInterval)
    case securityCheckFailed
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
        case .accountLocked(let remainingTime):
            let minutes = Int(remainingTime / 60)
            return "Cuenta bloqueada por \(minutes) minutos debido a múltiples intentos fallidos"
        case .securityCheckFailed:
            return "Verificación de seguridad falló. La app no puede ejecutarse en este dispositivo."
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
        case .accountLocked:
            return "Espera antes de intentar nuevamente o contacta soporte"
        case .securityCheckFailed:
            return "Reinstala la app desde la App Store oficial"
        case .networkError:
            return "Verifica tu conexión a internet"
        default:
            return "Intenta nuevamente o contacta soporte"
        }
    }
    
    static func == (lhs: AuthError, rhs: AuthError) -> Bool {
        switch (lhs, rhs) {
        case (.loginFailed(let lhs), .loginFailed(let rhs)),
             (.logoutFailed(let lhs), .logoutFailed(let rhs)),
             (.biometricsFailed(let lhs), .biometricsFailed(let rhs)),
             (.unknown(let lhs), .unknown(let rhs)):
            return lhs == rhs
        case (.accountLocked(let lhs), .accountLocked(let rhs)):
            return lhs == rhs
        case (.biometricsNotAvailable, .biometricsNotAvailable),
             (.tokenExpired, .tokenExpired),
             (.invalidCredentials, .invalidCredentials),
             (.securityCheckFailed, .securityCheckFailed),
             (.networkError, .networkError):
            return true
        default:
            return false
        }
    }
}

// MARK: - Support Classes Placeholders

extension AppConfig {
    struct Auth {
        static let userDataKey = "user_data"
        static let tokenExpirationBuffer: TimeInterval = 300
    }
    
    struct Security {
        static let maxFailedAttempts = 5
        static let lockoutDurationMinutes = 15
    }
    
    struct API {
        static let baseURL = "http://127.0.0.1:8001"
        static let login = "/auth/login"
        static let refresh = "/auth/refresh"
        static let requestTimeout: TimeInterval = 30
        static let resourceTimeout: TimeInterval = 60
    }
}

class SecurityManager {
    static let shared = SecurityManager()
    
    func validateAppIntegrity() -> Bool { return true }
    func isBiometricAuthenticationAvailable() -> Bool { return false }
    func getToken() -> String? { return nil }
    func isTokenValid() -> Bool { return false }
    func storeToken(_ token: String) throws { }
    func clearAllSecureData() throws { }
    func retrieve(key: String) throws -> Data? { return nil }
    func encrypt(_ data: Data) throws -> Data { return data }
    func store(_ data: Data, forKey key: String) throws { }
    func authenticateWithBiometrics(reason: String) async throws -> Bool { return false }
    func biometricType() -> LABiometryType { return .none }
}

class AppLogger {
    static let shared = AppLogger()
    
    enum Category {
        case auth
    }
    
    func info(_ message: String, category: Category, metadata: [String: Any] = [:]) { }
    func error(_ message: String, category: Category, error: Error, metadata: [String: Any] = [:]) { }
    func warning(_ message: String, category: Category, metadata: [String: Any] = [:]) { }
}

struct JWTDecoder {
    static func decode(_ token: String) throws -> JWTToken {
        return JWTToken(userID: "test", roles: ["user"], expirationDate: Date().addingTimeInterval(3600))
    }
}

struct JWTToken {
    let userID: String?
    let roles: [String]
    let expirationDate: Date?
}

struct AppConfig {
    static let currentEnvironment = Environment.development
    
    enum Environment {
        case development
        
        var displayName: String {
            return "Desarrollo"
        }
    }
}