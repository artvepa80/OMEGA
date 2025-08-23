import Foundation
import Network
import Security
import CommonCrypto

// MARK: - SSL Certificate Pinning Manager
/// Manages SSL certificate pinning for OMEGA iOS app with support for Akash Network SSL infrastructure
class SSLCertificatePinningManager: NSObject {
    
    static let shared = SSLCertificatePinningManager()
    
    // MARK: - Configuration
    struct PinningConfiguration {
        let domain: String
        let publicKeyHashes: Set<String>
        let certificateHashes: Set<String>
        let allowSelfSigned: Bool
        let requireCertificatePinning: Bool
        let environment: AppEnvironment
        
        init(
            domain: String,
            publicKeyHashes: Set<String> = [],
            certificateHashes: Set<String> = [],
            allowSelfSigned: Bool = false,
            requireCertificatePinning: Bool = true,
            environment: AppEnvironment = AppConfig.currentEnvironment
        ) {
            self.domain = domain
            self.publicKeyHashes = publicKeyHashes
            self.certificateHashes = certificateHashes
            self.allowSelfSigned = allowSelfSigned
            self.requireCertificatePinning = requireCertificatePinning
            self.environment = environment
        }
    }
    
    // MARK: - Properties
    private var pinningConfigurations: [String: PinningConfiguration] = [:]
    private let certificateCache = NSCache<NSString, AnyObject>()
    
    // MARK: - Initialization
    private override init() {
        super.init()
        setupDefaultConfigurations()
        loadPinnedCertificates()
    }
    
    // MARK: - Configuration Setup
    private func setupDefaultConfigurations() {
        // Production Akash Network Configuration
        let akashProductionConfig = PinningConfiguration(
            domain: "a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online",
            publicKeyHashes: loadPinnedPublicKeys(),
            certificateHashes: loadPinnedCertificateHashes(),
            allowSelfSigned: true, // Akash Network may use self-signed certificates
            requireCertificatePinning: AppConfig.currentEnvironment == .production,
            environment: .production
        )
        pinningConfigurations[akashProductionConfig.domain] = akashProductionConfig
        
        // Staging Configuration
        let stagingConfig = PinningConfiguration(
            domain: "a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online",
            allowSelfSigned: true,
            requireCertificatePinning: false,
            environment: .staging
        )
        pinningConfigurations[stagingConfig.domain] = stagingConfig
        
        // Development Configuration
        let developmentConfig = PinningConfiguration(
            domain: "127.0.0.1",
            allowSelfSigned: true,
            requireCertificatePinning: false,
            environment: .development
        )
        pinningConfigurations[developmentConfig.domain] = developmentConfig
        
        // Add localhost variants
        pinningConfigurations["localhost"] = developmentConfig
        pinningConfigurations["192.168.18.238"] = developmentConfig
    }
    
    private func loadPinnedPublicKeys() -> Set<String> {
        var keys = Set<String>()
        
        // Load pinned public keys from bundle
        guard let bundlePath = Bundle.main.path(forResource: "PinnedCertificates", ofType: "bundle"),
              let bundle = Bundle(path: bundlePath) else {
            AppLogger.shared.warning("PinnedCertificates bundle not found", category: .security)
            return keys
        }
        
        let publicKeyFiles = ["akash-public-key.pem", "production-public-key.pem"]
        
        for fileName in publicKeyFiles {
            if let filePath = bundle.path(forResource: fileName.components(separatedBy: ".").first,
                                        ofType: fileName.components(separatedBy: ".").last),
               let keyData = NSData(contentsOfFile: filePath) {
                let hash = sha256Hash(data: keyData as Data)
                keys.insert(hash)
                AppLogger.shared.debug("Loaded pinned public key: \(fileName)", category: .security)
            }
        }
        
        return keys
    }
    
    private func loadPinnedCertificateHashes() -> Set<String> {
        var hashes = Set<String>()
        
        // Load pinned certificate hashes from bundle
        guard let bundlePath = Bundle.main.path(forResource: "PinnedCertificates", ofType: "bundle"),
              let bundle = Bundle(path: bundlePath) else {
            return hashes
        }
        
        let certificateFiles = ["akash-cert.pem", "production-cert.pem"]
        
        for fileName in certificateFiles {
            if let filePath = bundle.path(forResource: fileName.components(separatedBy: ".").first,
                                        ofType: fileName.components(separatedBy: ".").last),
               let certData = NSData(contentsOfFile: filePath) {
                let hash = sha256Hash(data: certData as Data)
                hashes.insert(hash)
                AppLogger.shared.debug("Loaded pinned certificate: \(fileName)", category: .security)
            }
        }
        
        return hashes
    }
    
    private func loadPinnedCertificates() {
        guard let bundlePath = Bundle.main.path(forResource: "PinnedCertificates", ofType: "bundle"),
              let bundle = Bundle(path: bundlePath) else {
            AppLogger.shared.info("No pinned certificates bundle found - using runtime validation", category: .security)
            return
        }
        
        // Load certificates into cache
        let certificateFiles = bundle.paths(forResourcesOfType: "pem", inDirectory: nil) +
                              bundle.paths(forResourcesOfType: "cer", inDirectory: nil) +
                              bundle.paths(forResourcesOfType: "crt", inDirectory: nil)
        
        for certPath in certificateFiles {
            if let certData = NSData(contentsOfFile: certPath),
               let certificate = SecCertificateCreateWithData(nil, certData as CFData) {
                let fileName = URL(fileURLWithPath: certPath).lastPathComponent
                certificateCache.setObject(certificate, forKey: fileName as NSString)
                AppLogger.shared.debug("Cached certificate: \(fileName)", category: .security)
            }
        }
    }
    
    // MARK: - Public Methods
    
    /// Add or update pinning configuration for a domain
    func addPinningConfiguration(_ config: PinningConfiguration) {
        pinningConfigurations[config.domain] = config
        AppLogger.shared.info("Added SSL pinning configuration for domain: \(config.domain)", category: .security)
    }
    
    /// Remove pinning configuration for a domain
    func removePinningConfiguration(for domain: String) {
        pinningConfigurations.removeValue(forKey: domain)
    }
    
    /// Get configuration for a domain
    func getConfiguration(for domain: String) -> PinningConfiguration? {
        return pinningConfigurations[domain]
    }
    
    // MARK: - SSL Validation
    
    /// Main SSL validation method compatible with URLSessionDelegate
    func validateServerTrust(
        _ serverTrust: SecTrust,
        for host: String,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        AppLogger.shared.debug("Validating SSL certificate for host: \(host)", category: .security)
        
        guard let config = getConfigurationForHost(host) else {
            AppLogger.shared.error("No SSL configuration found for host: \(host)", category: .security)
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // For development environment, allow all certificates
        if config.environment == .development {
            AppLogger.shared.debug("Development environment - allowing all certificates", category: .security)
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
            return
        }
        
        // Validate certificate chain
        var result: SecTrustResultType = .invalid
        let status = SecTrustEvaluate(serverTrust, &result)
        
        guard status == errSecSuccess else {
            AppLogger.shared.error("SecTrustEvaluate failed with status: \(status)", category: .security)
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Handle different trust results
        switch result {
        case .unspecified, .proceed:
            // Valid certificate chain
            if config.requireCertificatePinning {
                validateCertificatePinning(serverTrust: serverTrust, config: config, completion: completionHandler)
            } else {
                completionHandler(.useCredential, URLCredential(trust: serverTrust))
            }
            
        case .recoverableTrustFailure:
            // Potentially valid but needs additional validation
            if config.allowSelfSigned {
                AppLogger.shared.info("Allowing self-signed certificate for Akash Network", category: .security)
                validateCertificatePinning(serverTrust: serverTrust, config: config, completion: completionHandler)
            } else {
                completionHandler(.cancelAuthenticationChallenge, nil)
            }
            
        default:
            AppLogger.shared.error("Certificate trust evaluation failed: \(result)", category: .security)
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }
    
    private func validateCertificatePinning(
        serverTrust: SecTrust,
        config: PinningConfiguration,
        completion: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        // Get leaf certificate
        guard let serverCertificate = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
            AppLogger.shared.error("Could not get server certificate", category: .security)
            completion(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // Validate certificate pinning
        if validateCertificateHash(serverCertificate, against: config.certificateHashes) ||
           validatePublicKeyHash(serverCertificate, against: config.publicKeyHashes) {
            AppLogger.shared.info("Certificate pinning validation successful", category: .security)
            completion(.useCredential, URLCredential(trust: serverTrust))
        } else {
            AppLogger.shared.error("Certificate pinning validation failed", category: .security)
            completion(.cancelAuthenticationChallenge, nil)
        }
    }
    
    private func validateCertificateHash(_ certificate: SecCertificate, against hashes: Set<String>) -> Bool {
        guard !hashes.isEmpty else { return true }
        
        let certificateData = SecCertificateCopyData(certificate)
        let hash = sha256Hash(data: certificateData as Data)
        
        let isValid = hashes.contains(hash)
        AppLogger.shared.debug("Certificate hash validation: \(isValid)", category: .security, metadata: [
            "hash": hash,
            "expected_hashes": Array(hashes)
        ])
        
        return isValid
    }
    
    private func validatePublicKeyHash(_ certificate: SecCertificate, against hashes: Set<String>) -> Bool {
        guard !hashes.isEmpty else { return true }
        
        guard let publicKey = SecCertificateCopyKey(certificate),
              let publicKeyData = SecKeyCopyExternalRepresentation(publicKey, nil) else {
            AppLogger.shared.error("Could not extract public key from certificate", category: .security)
            return false
        }
        
        let hash = sha256Hash(data: publicKeyData as Data)
        
        let isValid = hashes.contains(hash)
        AppLogger.shared.debug("Public key hash validation: \(isValid)", category: .security, metadata: [
            "hash": hash,
            "expected_hashes": Array(hashes)
        ])
        
        return isValid
    }
    
    private func getConfigurationForHost(_ host: String) -> PinningConfiguration? {
        // Direct match
        if let config = pinningConfigurations[host] {
            return config
        }
        
        // Try to match subdomains
        for (domain, config) in pinningConfigurations {
            if host.hasSuffix(domain) || domain.hasSuffix(host) {
                return config
            }
        }
        
        // Default to production config if available
        return pinningConfigurations.values.first { $0.environment == AppConfig.currentEnvironment }
    }
    
    // MARK: - Certificate Management
    
    /// Update certificate for runtime pinning
    func updateCertificate(_ certificateData: Data, for domain: String) {
        guard let certificate = SecCertificateCreateWithData(nil, certificateData as CFData) else {
            AppLogger.shared.error("Invalid certificate data for domain: \(domain)", category: .security)
            return
        }
        
        // Cache the certificate
        certificateCache.setObject(certificate, forKey: domain as NSString)
        
        // Update configuration with new certificate hash
        let hash = sha256Hash(data: certificateData)
        if var config = pinningConfigurations[domain] {
            var newHashes = config.certificateHashes
            newHashes.insert(hash)
            config = PinningConfiguration(
                domain: config.domain,
                publicKeyHashes: config.publicKeyHashes,
                certificateHashes: newHashes,
                allowSelfSigned: config.allowSelfSigned,
                requireCertificatePinning: config.requireCertificatePinning,
                environment: config.environment
            )
            pinningConfigurations[domain] = config
        }
        
        AppLogger.shared.info("Updated certificate for domain: \(domain)", category: .security)
    }
    
    /// Retrieve cached certificate for domain
    func getCachedCertificate(for domain: String) -> SecCertificate? {
        return certificateCache.object(forKey: domain as NSString) as? SecCertificate
    }
    
    // MARK: - Utility Methods
    
    private func sha256Hash(data: Data) -> String {
        var digest = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes { bytes in
            _ = CC_SHA256(bytes.bindMemory(to: UInt8.self).baseAddress, CC_LONG(data.count), &digest)
        }
        return digest.map { String(format: "%02x", $0) }.joined()
    }
    
    // MARK: - Certificate Validation Helper
    
    /// Validate certificate chain manually (useful for debugging)
    func validateCertificateChain(for domain: String) async -> CertificateValidationResult {
        guard let config = pinningConfigurations[domain] else {
            return .error("No configuration found for domain: \(domain)")
        }
        
        // Create URL for testing
        guard let url = URL(string: "https://\(domain)") else {
            return .error("Invalid URL for domain: \(domain)")
        }
        
        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            
            if let httpResponse = response as? HTTPURLResponse {
                let statusCode = httpResponse.statusCode
                if statusCode == 200 {
                    return .valid("Certificate validation successful")
                } else {
                    return .warning("Received HTTP status code: \(statusCode)")
                }
            }
            
            return .valid("Connection successful")
            
        } catch let error as URLError {
            switch error.code {
            case .serverCertificateUntrusted:
                return .error("Certificate not trusted")
            case .cannotConnectToHost:
                return .error("Cannot connect to host")
            default:
                return .error("Network error: \(error.localizedDescription)")
            }
        } catch {
            return .error("Validation error: \(error.localizedDescription)")
        }
    }
}

// MARK: - URLSessionDelegate Extension
extension SSLCertificatePinningManager: URLSessionDelegate {
    
    func urlSession(
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
        validateServerTrust(serverTrust, for: host, completionHandler: completionHandler)
    }
}

// MARK: - Supporting Types

enum CertificateValidationResult {
    case valid(String)
    case warning(String)
    case error(String)
    
    var isValid: Bool {
        switch self {
        case .valid:
            return true
        case .warning, .error:
            return false
        }
    }
    
    var message: String {
        switch self {
        case .valid(let message), .warning(let message), .error(let message):
            return message
        }
    }
}

// MARK: - Certificate Bundle Helper
extension SSLCertificatePinningManager {
    
    /// Create certificate bundle for app distribution
    static func createCertificateBundle(certificates: [Data], outputPath: URL) throws {
        let bundle = Bundle.main.bundleURL.appendingPathComponent("PinnedCertificates.bundle")
        
        try FileManager.default.createDirectory(at: bundle, withIntermediateDirectories: true)
        
        for (index, certData) in certificates.enumerated() {
            let certURL = bundle.appendingPathComponent("cert-\(index).pem")
            try certData.write(to: certURL)
        }
        
        AppLogger.shared.info("Created certificate bundle at: \(bundle.path)", category: .security)
    }
    
    /// Load certificates from Akash deployment
    static func loadCertificatesFromAkash(domain: String) async throws -> [Data] {
        let certURL = URL(string: "https://\(domain)/ssl/cert.pem")!
        let bundleURL = URL(string: "https://\(domain)/ssl/bundle.pem")!
        
        var certificates: [Data] = []
        
        // Try to load certificate and bundle from Akash deployment
        for url in [certURL, bundleURL] {
            do {
                let (data, _) = try await URLSession.shared.data(from: url)
                certificates.append(data)
                AppLogger.shared.info("Loaded certificate from: \(url)", category: .security)
            } catch {
                AppLogger.shared.warning("Failed to load certificate from: \(url)", category: .security, error: error)
            }
        }
        
        return certificates
    }
}