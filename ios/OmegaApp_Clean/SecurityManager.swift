import Foundation
import Security
import CryptoKit
import LocalAuthentication

// MARK: - JWT Token Management
struct JWTToken {
    let header: [String: Any]
    let payload: [String: Any]
    let signature: String
    let rawToken: String
    
    var isExpired: Bool {
        guard let exp = payload["exp"] as? TimeInterval else { return true }
        let expirationDate = Date(timeIntervalSince1970: exp)
        let bufferTime = AppConfig.Auth.tokenExpirationBuffer
        return Date().addingTimeInterval(bufferTime) >= expirationDate
    }
    
    var expirationDate: Date? {
        guard let exp = payload["exp"] as? TimeInterval else { return nil }
        return Date(timeIntervalSince1970: exp)
    }
    
    var userID: String? {
        return payload["sub"] as? String
    }
    
    var roles: [String] {
        return payload["roles"] as? [String] ?? []
    }
}

class JWTDecoder {
    static func decode(_ token: String) throws -> JWTToken {
        let segments = token.components(separatedBy: ".")
        guard segments.count == 3 else {
            throw SecurityError.invalidJWTFormat
        }
        
        let header = try decodeJWTSegment(segments[0])
        let payload = try decodeJWTSegment(segments[1])
        let signature = segments[2]
        
        return JWTToken(
            header: header,
            payload: payload,
            signature: signature,
            rawToken: token
        )
    }
    
    private static func decodeJWTSegment(_ segment: String) throws -> [String: Any] {
        var base64 = segment
            .replacingOccurrences(of: "-", with: "+")
            .replacingOccurrences(of: "_", with: "/")
        
        // Add padding if needed
        let remainder = base64.count % 4
        if remainder > 0 {
            base64 += String(repeating: "=", count: 4 - remainder)
        }
        
        guard let data = Data(base64Encoded: base64),
              let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw SecurityError.jwtDecodingFailed
        }
        
        return json
    }
}

// MARK: - Security Manager
class SecurityManager {
    static let shared = SecurityManager()
    
    private let keychainService = AppConfig.Auth.keychainService
    private let symmetricKey: SymmetricKey
    
    private init() {
        // Generate or retrieve app-specific encryption key
        self.symmetricKey = SecurityManager.getOrCreateEncryptionKey()
    }
    
    // MARK: - Keychain Operations
    func store(_ data: Data, forKey key: String, requireBiometrics: Bool = false) throws {
        var query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        if requireBiometrics {
            var access = SecAccessControlCreateWithFlags(
                nil,
                kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
                .biometryAny,
                nil
            )
            query[kSecAttrAccessControl as String] = access
        }
        
        // Delete existing item
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw SecurityError.keychainOperationFailed(status)
        }
    }
    
    func retrieve(key: String) throws -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess else {
            if status == errSecItemNotFound {
                return nil
            }
            throw SecurityError.keychainOperationFailed(status)
        }
        
        return result as? Data
    }
    
    func delete(key: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: key
        ]
        
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw SecurityError.keychainOperationFailed(status)
        }
    }
    
    // MARK: - Token Management
    func storeToken(_ token: String) throws {
        // Validate token before storing
        let jwtToken = try JWTDecoder.decode(token)
        guard !jwtToken.isExpired else {
            throw SecurityError.tokenExpired
        }
        
        let data = token.data(using: .utf8)!
        try store(data, forKey: AppConfig.Auth.tokenKey)
    }
    
    func getToken() -> String? {
        do {
            guard let data = try retrieve(key: AppConfig.Auth.tokenKey),
                  let token = String(data: data, encoding: .utf8) else {
                return nil
            }
            
            // Validate token before returning
            let jwtToken = try JWTDecoder.decode(token)
            return jwtToken.isExpired ? nil : token
            
        } catch {
            return nil
        }
    }
    
    func isTokenValid() -> Bool {
        guard let token = getToken() else { return false }
        
        do {
            let jwtToken = try JWTDecoder.decode(token)
            return !jwtToken.isExpired
        } catch {
            return false
        }
    }
    
    func getTokenExpirationDate() -> Date? {
        guard let token = getToken() else { return nil }
        
        do {
            let jwtToken = try JWTDecoder.decode(token)
            return jwtToken.expirationDate
        } catch {
            return nil
        }
    }
    
    // MARK: - Data Encryption
    func encrypt(_ data: Data) throws -> Data {
        let sealedBox = try AES.GCM.seal(data, using: symmetricKey)
        guard let combined = sealedBox.combined else {
            throw SecurityError.encryptionFailed
        }
        return combined
    }
    
    func decrypt(_ encryptedData: Data) throws -> Data {
        let sealedBox = try AES.GCM.SealedBox(combined: encryptedData)
        return try AES.GCM.open(sealedBox, using: symmetricKey)
    }
    
    // MARK: - Biometric Authentication
    func authenticateWithBiometrics(reason: String) async throws -> Bool {
        let context = LAContext()
        
        var error: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            throw SecurityError.biometricsNotAvailable(error?.localizedDescription)
        }
        
        do {
            return try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics,
                localizedReason: reason
            )
        } catch {
            throw SecurityError.biometricAuthenticationFailed(error.localizedDescription)
        }
    }
    
    func biometricType() -> LABiometryType {
        let context = LAContext()
        _ = context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: nil)
        return context.biometryType
    }
    
    func isBiometricAuthenticationAvailable() -> Bool {
        let context = LAContext()
        return context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: nil)
    }
    
    // MARK: - Security Validation
    func validateAppIntegrity() -> Bool {
        // Check if app is running on jailbroken device
        if isJailbrokenDevice() {
            return false
        }
        
        // Check if app is being debugged
        if isBeingDebugged() && AppConfig.currentEnvironment == .production {
            return false
        }
        
        // Validate code signature
        if !isCodeSignatureValid() && AppConfig.currentEnvironment == .production {
            return false
        }
        
        return true
    }
    
    private func isJailbrokenDevice() -> Bool {
        // Check for common jailbreak files and directories
        let jailbreakPaths = [
            "/Applications/Cydia.app",
            "/Library/MobileSubstrate/MobileSubstrate.dylib",
            "/bin/bash",
            "/usr/sbin/sshd",
            "/etc/apt"
        ]
        
        for path in jailbreakPaths {
            if FileManager.default.fileExists(atPath: path) {
                return true
            }
        }
        
        // Try to write to restricted directory
        do {
            let testString = "test"
            try testString.write(toFile: "/private/test.txt", atomically: true, encoding: .utf8)
            try FileManager.default.removeItem(atPath: "/private/test.txt")
            return true // Should not be able to write
        } catch {
            return false // Normal behavior
        }
    }
    
    private func isBeingDebugged() -> Bool {
        var info = kinfo_proc()
        var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()]
        var size = MemoryLayout<kinfo_proc>.stride
        
        let junk = sysctl(&mib, UInt32(mib.count), &info, &size, nil, 0)
        assert(junk == 0, "sysctl failed")
        
        return (info.kp_proc.p_flag & P_TRACED) != 0
    }
    
    private func isCodeSignatureValid() -> Bool {
        guard let bundlePath = Bundle.main.bundlePath.cString(using: .utf8) else {
            return false
        }
        
        var staticCode: SecStaticCode?
        var status = SecStaticCodeCreateWithPath(
            CFStringCreateWithCString(nil, bundlePath, kCFStringEncodingUTF8),
            [],
            &staticCode
        )
        
        guard status == errSecSuccess, let code = staticCode else {
            return false
        }
        
        status = SecStaticCodeCheckValidity(code, [], nil)
        return status == errSecSuccess
    }
    
    // MARK: - Private Helpers
    private static func getOrCreateEncryptionKey() -> SymmetricKey {
        let keyData = "OmegaAppEncryptionKey2024".data(using: .utf8)!
        return SymmetricKey(data: SHA256.hash(data: keyData))
    }
    
    // MARK: - Cleanup
    func clearAllSecureData() throws {
        try delete(key: AppConfig.Auth.tokenKey)
        try delete(key: AppConfig.Auth.refreshTokenKey)
        try delete(key: AppConfig.Auth.userDataKey)
    }
}

// MARK: - Security Errors
enum SecurityError: LocalizedError, Equatable {
    case invalidJWTFormat
    case jwtDecodingFailed
    case tokenExpired
    case keychainOperationFailed(OSStatus)
    case encryptionFailed
    case decryptionFailed
    case biometricsNotAvailable(String?)
    case biometricAuthenticationFailed(String)
    case appIntegrityCheckFailed
    case jailbrokenDevice
    case debuggerDetected
    case invalidCodeSignature
    
    var errorDescription: String? {
        switch self {
        case .invalidJWTFormat:
            return "Token JWT tiene formato inválido"
        case .jwtDecodingFailed:
            return "Error decodificando token JWT"
        case .tokenExpired:
            return "El token ha expirado"
        case .keychainOperationFailed(let status):
            return "Error en operación de Keychain: \(status)"
        case .encryptionFailed:
            return "Error en encriptación de datos"
        case .decryptionFailed:
            return "Error en desencriptación de datos"
        case .biometricsNotAvailable(let reason):
            return "Autenticación biométrica no disponible: \(reason ?? "Desconocido")"
        case .biometricAuthenticationFailed(let reason):
            return "Autenticación biométrica falló: \(reason)"
        case .appIntegrityCheckFailed:
            return "Verificación de integridad de la app falló"
        case .jailbrokenDevice:
            return "Dispositivo con jailbreak detectado"
        case .debuggerDetected:
            return "Debugger detectado"
        case .invalidCodeSignature:
            return "Firma de código inválida"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .tokenExpired:
            return "Inicia sesión nuevamente"
        case .biometricsNotAvailable, .biometricAuthenticationFailed:
            return "Usa tu contraseña para autenticarte"
        case .jailbrokenDevice:
            return "Esta app no puede ejecutarse en dispositivos con jailbreak"
        case .debuggerDetected, .invalidCodeSignature:
            return "Reinstala la app desde la App Store"
        default:
            return "Contacta soporte técnico si el problema persiste"
        }
    }
    
    static func == (lhs: SecurityError, rhs: SecurityError) -> Bool {
        switch (lhs, rhs) {
        case (.invalidJWTFormat, .invalidJWTFormat),
             (.jwtDecodingFailed, .jwtDecodingFailed),
             (.tokenExpired, .tokenExpired),
             (.encryptionFailed, .encryptionFailed),
             (.decryptionFailed, .decryptionFailed),
             (.appIntegrityCheckFailed, .appIntegrityCheckFailed),
             (.jailbrokenDevice, .jailbrokenDevice),
             (.debuggerDetected, .debuggerDetected),
             (.invalidCodeSignature, .invalidCodeSignature):
            return true
        case (.keychainOperationFailed(let lhsStatus), .keychainOperationFailed(let rhsStatus)):
            return lhsStatus == rhsStatus
        case (.biometricsNotAvailable(let lhsReason), .biometricsNotAvailable(let rhsReason)):
            return lhsReason == rhsReason
        case (.biometricAuthenticationFailed(let lhsReason), .biometricAuthenticationFailed(let rhsReason)):
            return lhsReason == rhsReason
        default:
            return false
        }
    }
}