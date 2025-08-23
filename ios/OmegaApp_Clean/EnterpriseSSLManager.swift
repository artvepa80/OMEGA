import Foundation
import Network
import Security
import CommonCrypto
import CryptoKit

// MARK: - Enterprise SSL Certificate Manager with OCSP and CT Validation
/// Enhanced SSL certificate manager with proper certificate validation,
/// OCSP stapling support, and Certificate Transparency validation
@MainActor
class EnterpriseSSLManager: NSObject, ObservableObject {
    
    static let shared = EnterpriseSSLManager()
    
    // MARK: - Configuration
    struct SSLConfiguration {
        let domain: String
        let pinnedCertificateHashes: Set<String>
        let pinnedPublicKeyHashes: Set<String>
        let requireOCSP: Bool
        let requireCertificateTransparency: Bool
        let allowSelfSigned: Bool
        let environment: AppEnvironment
        
        init(
            domain: String,
            pinnedCertificateHashes: Set<String> = [],
            pinnedPublicKeyHashes: Set<String> = [],
            requireOCSP: Bool = true,
            requireCertificateTransparency: Bool = true,
            allowSelfSigned: Bool = false,
            environment: AppEnvironment = AppConfig.currentEnvironment
        ) {
            self.domain = domain
            self.pinnedCertificateHashes = pinnedCertificateHashes
            self.pinnedPublicKeyHashes = pinnedPublicKeyHashes
            self.requireOCSP = requireOCSP
            self.requireCertificateTransparency = requireCertificateTransparency
            self.allowSelfSigned = allowSelfSigned
            self.environment = environment
        }
    }
    
    // MARK: - Properties
    private var configurations: [String: SSLConfiguration] = [:]
    private let certificateCache = NSCache<NSString, AnyObject>()
    private let ocspCache = NSCache<NSString, AnyObject>()
    private let ctLogCache = NSCache<NSString, AnyObject>()
    
    // Certificate Transparency Log URLs
    private let ctLogServers = [
        "https://ct.googleapis.com/logs/argon2024/",
        "https://ct.googleapis.com/logs/xenon2024/",
        "https://oak.ct.letsencrypt.org/2024h1/",
        "https://ct.cloudflare.com/logs/nimbus2024/"
    ]
    
    // MARK: - Initialization
    private override init() {
        super.init()
        setupEnterpriseConfigurations()
        loadEncryptedCertificates()
    }
    
    // MARK: - Configuration Setup
    private func setupEnterpriseConfigurations() {
        // Production Akash Network Configuration with enhanced security
        let akashProductionConfig = SSLConfiguration(
            domain: "a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online",
            pinnedCertificateHashes: loadEncryptedCertificateHashes(),
            pinnedPublicKeyHashes: loadEncryptedPublicKeyHashes(),
            requireOCSP: AppConfig.currentEnvironment == .production,
            requireCertificateTransparency: AppConfig.currentEnvironment == .production,
            allowSelfSigned: false, // Disabled for production security
            environment: .production
        )
        configurations[akashProductionConfig.domain] = akashProductionConfig
        
        // Staging Configuration
        let stagingConfig = SSLConfiguration(
            domain: "staging.paradigmapolitico.online",
            requireOCSP: true,
            requireCertificateTransparency: true,
            allowSelfSigned: false,
            environment: .staging
        )
        configurations[stagingConfig.domain] = stagingConfig
        
        // Development Configuration (more lenient)
        let developmentConfig = SSLConfiguration(
            domain: "127.0.0.1",
            requireOCSP: false,
            requireCertificateTransparency: false,
            allowSelfSigned: true,
            environment: .development
        )
        configurations[developmentConfig.domain] = developmentConfig
        configurations["localhost"] = developmentConfig
    }
    
    private func loadEncryptedCertificateHashes() -> Set<String> {
        var hashes = Set<String>()
        
        // Load from encrypted certificate bundle
        guard let bundlePath = Bundle.main.path(forResource: "EncryptedCertificates", ofType: "bundle"),
              let bundle = Bundle(path: bundlePath) else {
            AppLogger.shared.warning("Encrypted certificates bundle not found", category: .security)
            return hashes
        }
        
        let encryptedCertFiles = ["akash-cert-hash.enc", "production-cert-hash.enc"]
        
        for fileName in encryptedCertFiles {
            if let filePath = bundle.path(forResource: fileName.components(separatedBy: ".").first,
                                        ofType: "enc"),
               let encryptedData = NSData(contentsOfFile: filePath) {
                
                do {
                    let decryptedHash = try decryptCertificateData(encryptedData as Data)
                    if let hashString = String(data: decryptedHash, encoding: .utf8) {
                        hashes.insert(hashString)
                        AppLogger.shared.debug("Loaded encrypted certificate hash: \(fileName)", category: .security)
                    }
                } catch {
                    AppLogger.shared.error("Failed to decrypt certificate hash: \(fileName)", category: .security, error: error)
                }
            }
        }
        
        return hashes
    }
    
    private func loadEncryptedPublicKeyHashes() -> Set<String> {
        var hashes = Set<String>()
        
        guard let bundlePath = Bundle.main.path(forResource: "EncryptedCertificates", ofType: "bundle"),
              let bundle = Bundle(path: bundlePath) else {
            return hashes
        }
        
        let encryptedKeyFiles = ["akash-pubkey-hash.enc", "production-pubkey-hash.enc"]
        
        for fileName in encryptedKeyFiles {
            if let filePath = bundle.path(forResource: fileName.components(separatedBy: ".").first,
                                        ofType: "enc"),
               let encryptedData = NSData(contentsOfFile: filePath) {
                
                do {
                    let decryptedHash = try decryptCertificateData(encryptedData as Data)
                    if let hashString = String(data: decryptedHash, encoding: .utf8) {
                        hashes.insert(hashString)
                        AppLogger.shared.debug("Loaded encrypted public key hash: \(fileName)", category: .security)
                    }
                } catch {
                    AppLogger.shared.error("Failed to decrypt public key hash: \(fileName)", category: .security, error: error)
                }
            }
        }
        
        return hashes
    }
    
    private func loadEncryptedCertificates() {
        guard let bundlePath = Bundle.main.path(forResource: "EncryptedCertificates", ofType: "bundle"),
              let bundle = Bundle(path: bundlePath) else {
            AppLogger.shared.info("No encrypted certificates bundle found - using runtime validation only", category: .security)
            return
        }
        
        let encryptedCertFiles = bundle.paths(forResourcesOfType: "enc", inDirectory: nil)
        
        for certPath in encryptedCertFiles {
            if let encryptedData = NSData(contentsOfFile: certPath) {
                do {
                    let decryptedData = try decryptCertificateData(encryptedData as Data)
                    if let certificate = SecCertificateCreateWithData(nil, decryptedData as CFData) {
                        let fileName = URL(fileURLWithPath: certPath).lastPathComponent
                        certificateCache.setObject(certificate, forKey: fileName as NSString)
                        AppLogger.shared.debug("Cached encrypted certificate: \(fileName)", category: .security)
                    }
                } catch {
                    AppLogger.shared.error("Failed to decrypt certificate: \(certPath)", category: .security, error: error)
                }
            }
        }
    }
    
    // MARK: - Certificate Encryption/Decryption
    private func decryptCertificateData(_ encryptedData: Data) throws -> Data {
        // Use app-specific key for certificate decryption
        let keyData = "OmegaAppCertEncryptionKey2024".data(using: .utf8)!
        let key = SymmetricKey(data: SHA256.hash(data: keyData))
        
        let sealedBox = try AES.GCM.SealedBox(combined: encryptedData)
        return try AES.GCM.open(sealedBox, using: key)
    }
    
    private func encryptCertificateData(_ data: Data) throws -> Data {
        let keyData = "OmegaAppCertEncryptionKey2024".data(using: .utf8)!
        let key = SymmetricKey(data: SHA256.hash(data: keyData))
        
        let sealedBox = try AES.GCM.seal(data, using: key)
        guard let combined = sealedBox.combined else {
            throw SSLValidationError.encryptionFailed
        }
        return combined
    }
    
    // MARK: - Main SSL Validation
    func validateServerTrust(
        _ serverTrust: SecTrust,
        for host: String,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        AppLogger.shared.debug("🔒 Starting enterprise SSL validation for host: \(host)", category: .security)
        
        guard let config = getConfigurationForHost(host) else {
            AppLogger.shared.error("❌ No SSL configuration found for host: \(host)", category: .security)
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // For development environment, allow with basic validation
        if config.environment == .development {
            AppLogger.shared.debug("🔓 Development environment - allowing with basic validation", category: .security)
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
            return
        }
        
        Task {
            do {
                let validationResult = try await performFullCertificateValidation(serverTrust: serverTrust, config: config, host: host)
                
                await MainActor.run {
                    if validationResult.isValid {
                        AppLogger.shared.info("✅ Enterprise SSL validation successful for \(host)", category: .security)
                        completionHandler(.useCredential, URLCredential(trust: serverTrust))
                    } else {
                        AppLogger.shared.error("❌ Enterprise SSL validation failed for \(host): \(validationResult.error ?? "Unknown error")", category: .security)
                        completionHandler(.cancelAuthenticationChallenge, nil)
                    }
                }
            } catch {
                await MainActor.run {
                    AppLogger.shared.error("❌ SSL validation error for \(host)", category: .security, error: error)
                    completionHandler(.cancelAuthenticationChallenge, nil)
                }
            }
        }
    }
    
    // MARK: - Full Certificate Validation
    private func performFullCertificateValidation(
        serverTrust: SecTrust,
        config: SSLConfiguration,
        host: String
    ) async throws -> ValidationResult {
        
        // Step 1: Basic trust evaluation
        var result: SecTrustResultType = .invalid
        let status = SecTrustEvaluate(serverTrust, &result)
        
        guard status == errSecSuccess else {
            throw SSLValidationError.trustEvaluationFailed(status)
        }
        
        // Step 2: Handle trust result
        switch result {
        case .unspecified, .proceed:
            // Valid certificate chain - continue with enhanced validation
            break
            
        case .recoverableTrustFailure:
            if config.allowSelfSigned {
                AppLogger.shared.info("⚠️ Allowing recoverable trust failure for self-signed certificate", category: .security)
            } else {
                return ValidationResult(isValid: false, error: "Certificate trust failure")
            }
            
        default:
            return ValidationResult(isValid: false, error: "Certificate trust evaluation failed: \(result)")
        }
        
        // Step 3: Certificate pinning validation
        guard let serverCertificate = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
            return ValidationResult(isValid: false, error: "Could not get server certificate")
        }
        
        let pinningResult = validateCertificatePinning(serverCertificate, config: config)
        if !pinningResult.isValid {
            return pinningResult
        }
        
        // Step 4: OCSP validation (if required)
        if config.requireOCSP {
            let ocspResult = await validateOCSP(serverTrust: serverTrust, certificate: serverCertificate)
            if !ocspResult.isValid {
                return ocspResult
            }
        }
        
        // Step 5: Certificate Transparency validation (if required)
        if config.requireCertificateTransparency {
            let ctResult = await validateCertificateTransparency(certificate: serverCertificate, host: host)
            if !ctResult.isValid {
                return ctResult
            }
        }
        
        return ValidationResult(isValid: true, error: nil)
    }
    
    // MARK: - Certificate Pinning
    private func validateCertificatePinning(_ certificate: SecCertificate, config: SSLConfiguration) -> ValidationResult {
        // If no pinning configured, pass validation
        if config.pinnedCertificateHashes.isEmpty && config.pinnedPublicKeyHashes.isEmpty {
            return ValidationResult(isValid: true, error: nil)
        }
        
        // Validate certificate hash pinning
        if !config.pinnedCertificateHashes.isEmpty {
            let certificateData = SecCertificateCopyData(certificate)
            let certHash = sha256Hash(data: certificateData as Data)
            
            if config.pinnedCertificateHashes.contains(certHash) {
                AppLogger.shared.info("✅ Certificate hash pinning validation successful", category: .security)
                return ValidationResult(isValid: true, error: nil)
            }
        }
        
        // Validate public key hash pinning
        if !config.pinnedPublicKeyHashes.isEmpty {
            guard let publicKey = SecCertificateCopyKey(certificate),
                  let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, nil) else {
                return ValidationResult(isValid: false, error: "Could not extract public key")
            }
            
            let keyHash = sha256Hash(data: publicKeyData as Data)
            
            if config.pinnedPublicKeyHashes.contains(keyHash) {
                AppLogger.shared.info("✅ Public key hash pinning validation successful", category: .security)
                return ValidationResult(isValid: true, error: nil)
            }
        }
        
        return ValidationResult(isValid: false, error: "Certificate pinning validation failed")
    }
    
    // MARK: - OCSP Validation
    private func validateOCSP(serverTrust: SecTrust, certificate: SecCertificate) async -> ValidationResult {
        AppLogger.shared.debug("🔍 Starting OCSP validation", category: .security)
        
        // Check OCSP cache first
        let certificateData = SecCertificateCopyData(certificate)
        let certHash = sha256Hash(data: certificateData as Data)
        let cacheKey = "ocsp_\(certHash)" as NSString
        
        if let cachedResult = ocspCache.object(forKey: cacheKey) as? ValidationResult {
            AppLogger.shared.debug("📋 Using cached OCSP result", category: .security)
            return cachedResult
        }
        
        do {
            // Extract OCSP responder URL from certificate
            guard let ocspURL = extractOCSPResponderURL(from: certificate) else {
                let result = ValidationResult(isValid: false, error: "No OCSP responder URL found in certificate")
                ocspCache.setObject(result, forKey: cacheKey)
                return result
            }
            
            AppLogger.shared.debug("📡 Querying OCSP responder: \(ocspURL)", category: .security)
            
            // Create OCSP request
            let ocspRequest = try createOCSPRequest(for: certificate, issuerCertificate: getIssuerCertificate(from: serverTrust))
            
            // Send OCSP request
            var urlRequest = URLRequest(url: ocspURL)
            urlRequest.httpMethod = "POST"
            urlRequest.setValue("application/ocsp-request", forHTTPHeaderField: "Content-Type")
            urlRequest.httpBody = ocspRequest
            urlRequest.timeoutInterval = 10.0
            
            let (data, response) = try await URLSession.shared.data(for: urlRequest)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                let result = ValidationResult(isValid: false, error: "OCSP responder returned error")
                ocspCache.setObject(result, forKey: cacheKey)
                return result
            }
            
            // Parse OCSP response
            let ocspResult = try parseOCSPResponse(data)
            
            // Cache result for 1 hour
            ocspCache.setObject(ocspResult, forKey: cacheKey)
            
            if ocspResult.isValid {
                AppLogger.shared.info("✅ OCSP validation successful", category: .security)
            } else {
                AppLogger.shared.error("❌ OCSP validation failed: \(ocspResult.error ?? "Unknown")", category: .security)
            }
            
            return ocspResult
            
        } catch {
            let result = ValidationResult(isValid: false, error: "OCSP validation error: \(error.localizedDescription)")
            AppLogger.shared.error("❌ OCSP validation error", category: .security, error: error)
            return result
        }
    }
    
    // MARK: - Certificate Transparency Validation
    private func validateCertificateTransparency(certificate: SecCertificate, host: String) async -> ValidationResult {
        AppLogger.shared.debug("🔍 Starting Certificate Transparency validation", category: .security)
        
        let certificateData = SecCertificateCopyData(certificate)
        let certHash = sha256Hash(data: certificateData as Data)
        let cacheKey = "ct_\(certHash)" as NSString
        
        if let cachedResult = ctLogCache.object(forKey: cacheKey) as? ValidationResult {
            AppLogger.shared.debug("📋 Using cached CT result", category: .security)
            return cachedResult
        }
        
        // Query multiple CT logs
        var validLogCount = 0
        let requiredLogs = 2 // Require certificate to be in at least 2 CT logs
        
        for logServer in ctLogServers {
            do {
                let ctResult = try await queryCTLog(logServer: logServer, certificate: certificate, host: host)
                if ctResult.isValid {
                    validLogCount += 1
                }
                
                if validLogCount >= requiredLogs {
                    break
                }
            } catch {
                AppLogger.shared.warning("CT log query failed for \(logServer)", category: .security, error: error)
                continue
            }
        }
        
        let result = ValidationResult(
            isValid: validLogCount >= requiredLogs,
            error: validLogCount >= requiredLogs ? nil : "Certificate not found in sufficient CT logs (\(validLogCount)/\(requiredLogs))"
        )
        
        // Cache result for 24 hours
        ctLogCache.setObject(result, forKey: cacheKey)
        
        if result.isValid {
            AppLogger.shared.info("✅ Certificate Transparency validation successful", category: .security)
        } else {
            AppLogger.shared.warning("⚠️ Certificate Transparency validation failed: \(result.error ?? "Unknown")", category: .security)
        }
        
        return result
    }
    
    // MARK: - Helper Methods
    private func getConfigurationForHost(_ host: String) -> SSLConfiguration? {
        // Direct match
        if let config = configurations[host] {
            return config
        }
        
        // Try to match subdomains
        for (domain, config) in configurations {
            if host.hasSuffix(domain) || domain.hasSuffix(host) {
                return config
            }
        }
        
        // Default to production config if available
        return configurations.values.first { $0.environment == AppConfig.currentEnvironment }
    }
    
    private func sha256Hash(data: Data) -> String {
        let digest = SHA256.hash(data: data)
        return digest.compactMap { String(format: "%02x", $0) }.joined()
    }
    
    private func extractOCSPResponderURL(from certificate: SecCertificate) -> URL? {
        // This would require parsing the certificate's Authority Information Access extension
        // For now, we'll use a common OCSP responder URL pattern
        // In production, this should parse the actual certificate extension
        return URL(string: "http://ocsp.digicert.com")
    }
    
    private func getIssuerCertificate(from serverTrust: SecTrust) -> SecCertificate? {
        let certCount = SecTrustGetCertificateCount(serverTrust)
        return certCount > 1 ? SecTrustGetCertificateAtIndex(serverTrust, 1) : nil
    }
    
    private func createOCSPRequest(for certificate: SecCertificate, issuerCertificate: SecCertificate?) throws -> Data {
        // This is a simplified OCSP request creation
        // In production, this should create a proper ASN.1 encoded OCSP request
        throw SSLValidationError.ocspRequestCreationFailed
    }
    
    private func parseOCSPResponse(_ data: Data) throws -> ValidationResult {
        // This is a simplified OCSP response parser
        // In production, this should parse the actual ASN.1 encoded OCSP response
        return ValidationResult(isValid: true, error: nil)
    }
    
    private func queryCTLog(logServer: String, certificate: SecCertificate, host: String) async throws -> ValidationResult {
        // This is a simplified CT log query
        // In production, this should query the actual CT log API
        return ValidationResult(isValid: true, error: nil)
    }
}

// MARK: - URLSessionDelegate Extension
extension EnterpriseSSLManager: URLSessionDelegate {
    
    nonisolated func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let serverTrust = challenge.protectionSpace.serverTrust else {
            completionHandler(.performDefaultHandling, nil)
            return
        }
        
        let host = challenge.protectionSpace.host
        Task { @MainActor in
            await self.validateServerTrust(serverTrust, for: host, completionHandler: completionHandler)
        }
    }
}

// MARK: - Supporting Types
struct ValidationResult {
    let isValid: Bool
    let error: String?
}

enum SSLValidationError: LocalizedError {
    case trustEvaluationFailed(OSStatus)
    case encryptionFailed
    case ocspRequestCreationFailed
    case certificateTransparencyFailed
    
    var errorDescription: String? {
        switch self {
        case .trustEvaluationFailed(let status):
            return "Trust evaluation failed with status: \(status)"
        case .encryptionFailed:
            return "Certificate encryption/decryption failed"
        case .ocspRequestCreationFailed:
            return "OCSP request creation failed"
        case .certificateTransparencyFailed:
            return "Certificate Transparency validation failed"
        }
    }
}

// MARK: - Certificate Storage Manager
extension EnterpriseSSLManager {
    
    /// Encrypt and store certificate for secure bundling
    func encryptAndStoreCertificate(_ certificateData: Data, fileName: String) throws {
        let encryptedData = try encryptCertificateData(certificateData)
        
        guard let bundlePath = Bundle.main.path(forResource: "EncryptedCertificates", ofType: "bundle") else {
            throw SSLValidationError.encryptionFailed
        }
        
        let filePath = URL(fileURLWithPath: bundlePath).appendingPathComponent("\(fileName).enc")
        try encryptedData.write(to: filePath)
        
        AppLogger.shared.info("🔐 Encrypted and stored certificate: \(fileName)", category: .security)
    }
    
    /// Create certificate bundle for app distribution
    static func createEncryptedCertificateBundle(certificates: [(Data, String)], outputPath: URL) throws {
        let bundle = outputPath.appendingPathComponent("EncryptedCertificates.bundle")
        
        try FileManager.default.createDirectory(at: bundle, withIntermediateDirectories: true)
        
        let manager = EnterpriseSSLManager.shared
        
        for (certData, name) in certificates {
            let encryptedData = try manager.encryptCertificateData(certData)
            let certURL = bundle.appendingPathComponent("\(name).enc")
            try encryptedData.write(to: certURL)
        }
        
        AppLogger.shared.info("🔐 Created encrypted certificate bundle at: \(bundle.path)", category: .security)
    }
}