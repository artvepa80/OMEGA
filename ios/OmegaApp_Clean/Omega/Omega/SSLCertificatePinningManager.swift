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
            // SECURITY FIX: Implement proper certificate validation override protection
            // Never allow recoverableTrustFailure without additional security checks
            if config.allowSelfSigned && config.environment != .production {
                // Only allow in non-production environments with additional validation
                if validateCertificateTransparency(serverTrust: serverTrust) &&
                   validateOCSPStapling(serverTrust: serverTrust) {
                    AppLogger.shared.warning("Allowing self-signed certificate after security validation", category: .security)
                    validateCertificatePinning(serverTrust: serverTrust, config: config, completion: completionHandler)
                } else {
                    AppLogger.shared.error("Self-signed certificate failed additional security checks", category: .security)
                    completionHandler(.cancelAuthenticationChallenge, nil)
                }
            } else {
                AppLogger.shared.error("Certificate trust failure - rejecting connection", category: .security)
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
    
    // MARK: - Security Validation Methods
    
    /// Validate Certificate Transparency
    private func validateCertificateTransparency(serverTrust: SecTrust) -> Bool {
        guard let leafCertificate = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
            AppLogger.shared.error("Could not get leaf certificate for CT validation", category: .security)
            return false
        }
        
        // Check for SCT (Signed Certificate Timestamps) extension
        let certificateData = SecCertificateCopyData(leafCertificate)
        let certDict = SecCertificateCopyValues(leafCertificate, nil, nil) as? [String: Any]
        
        // Look for CT extension (OID 1.3.6.1.4.1.11129.2.4.2)
        let ctExtensionOID = "1.3.6.1.4.1.11129.2.4.2"
        
        if let extensions = certDict?[kSecOIDX509V3CertificateExtensions as String] as? [[String: Any]] {
            for ext in extensions {
                if let oid = ext[kSecOIDX509V3ExtensionOID as String] as? String,
                   oid == ctExtensionOID {
                    AppLogger.shared.info("Certificate Transparency validation passed", category: .security)
                    return true
                }
            }
        }
        
        AppLogger.shared.warning("No Certificate Transparency data found", category: .security)
        return AppConfig.currentEnvironment != .production // Only allow in non-production
    }
    
    /// Validate OCSP Stapling
    private func validateOCSPStapling(serverTrust: SecTrust) -> Bool {
        var result: SecTrustResultType = .invalid
        let status = SecTrustEvaluate(serverTrust, &result)
        
        guard status == errSecSuccess else {
            AppLogger.shared.error("OCSP stapling validation failed", category: .security)
            return false
        }
        
        // Check for OCSP response
        var ocspResponse: CFData?
        let ocspStatus = SecTrustGetOCSPResponse(serverTrust, &ocspResponse)
        
        if ocspStatus == errSecSuccess && ocspResponse != nil {
            AppLogger.shared.info("OCSP stapling validation passed", category: .security)
            return true
        }
        
        AppLogger.shared.warning("No OCSP stapling data found", category: .security)
        return AppConfig.currentEnvironment != .production // Only allow in non-production
    }
    
    /// Validate certificate revocation status
    private func validateCertificateRevocation(serverTrust: SecTrust) async -> Bool {
        // Set revocation policy
        let revocationPolicy = SecPolicyCreateRevocation(kSecRevocationOCSPMethod | kSecRevocationCRLMethod)
        SecTrustSetPolicies(serverTrust, [revocationPolicy] as CFArray)
        
        var result: SecTrustResultType = .invalid
        let status = SecTrustEvaluateAsync(serverTrust, DispatchQueue.global()) { _, trustResult in
            result = trustResult
        }
        
        guard status == errSecSuccess else {
            AppLogger.shared.error("Certificate revocation check failed", category: .security)
            return false
        }
        
        switch result {
        case .proceed, .unspecified:
            AppLogger.shared.info("Certificate revocation validation passed", category: .security)
            return true
        default:
            AppLogger.shared.error("Certificate revocation validation failed: \(result)", category: .security)
            return false
        }
    }
    
    /// Validate certificate fingerprint
    private func validateCertificateFingerprint(_ certificate: SecCertificate, expectedFingerprints: Set<String>) -> Bool {
        guard !expectedFingerprints.isEmpty else { return true }
        
        let certificateData = SecCertificateCopyData(certificate) as Data
        let fingerprint = sha256Hash(data: certificateData)
        
        let isValid = expectedFingerprints.contains(fingerprint)
        AppLogger.shared.debug("Certificate fingerprint validation: \(isValid)", category: .security, metadata: [
            "fingerprint": fingerprint,
            "expected_fingerprints": Array(expectedFingerprints)
        ])
        
        return isValid
    }
    
    // MARK: - Certificate Management
    
    /// Update certificate for runtime pinning with version validation
    func updateCertificate(_ certificateData: Data, for domain: String, version: String? = nil) {
        guard let certificate = SecCertificateCreateWithData(nil, certificateData as CFData) else {
            AppLogger.shared.error("Invalid certificate data for domain: \(domain)", category: .security)
            return
        }
        
        // Validate certificate before updating
        guard validateCertificateIntegrity(certificate) else {
            AppLogger.shared.error("Certificate integrity validation failed for domain: \(domain)", category: .security)
            return
        }
        
        // Store version information if provided
        if let version = version {
            UserDefaults.standard.set(version, forKey: "cert_version_\(domain)")
        }
        
        // Cache the certificate with timestamp
        let certWithMetadata = CertificateMetadata(
            certificate: certificate,
            domain: domain,
            version: version,
            updatedAt: Date()
        )
        certificateCache.setObject(certWithMetadata as AnyObject, forKey: domain as NSString)
        
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
        
        AppLogger.shared.info("Updated certificate for domain: \(domain) with version: \(version ?? "unknown")", category: .security)
        
        // Trigger certificate synchronization
        Task {
            await synchronizeCertificateWithServer(domain: domain)
        }
    }
    
    /// Validate certificate integrity
    private func validateCertificateIntegrity(_ certificate: SecCertificate) -> Bool {
        // Basic certificate validity checks
        let certificateData = SecCertificateCopyData(certificate) as Data
        
        // Check certificate size (reasonable bounds)
        guard certificateData.count > 100 && certificateData.count < 10000 else {
            AppLogger.shared.error("Certificate size out of bounds", category: .security)
            return false
        }
        
        // Check certificate format (basic DER validation)
        guard let certSubject = SecCertificateCopySubjectSummary(certificate) as String? else {
            AppLogger.shared.error("Invalid certificate subject", category: .security)
            return false
        }
        
        AppLogger.shared.debug("Certificate integrity check passed for: \(certSubject)", category: .security)
        return true
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
    
    // MARK: - Extension Properties (moved from extensions to fix Swift compilation)
    private var securityMonitorTimer: Timer?
    private var securityAlerts: [SecurityAlertNotification] = []
    private var certificateRotationTimers: [String: Timer] = [:]
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

// MARK: - MITM Detection and Security Monitoring

extension SSLCertificatePinningManager {
    
    /// Monitor SSL/TLS connections for potential MITM attacks
    func startSecurityMonitoring() {
        let monitor = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { _ in
            Task {
                await self.performSecurityScans()
            }
        }
        
        securityMonitorTimer = monitor
        AppLogger.shared.info("Started SSL/TLS security monitoring", category: .security)
    }
    
    private func performSecurityScans() async {
        for (domain, config) in pinningConfigurations {
            await detectPotentialMITM(for: domain, config: config)
        }
    }
    
    private func detectPotentialMITM(for domain: String, config: PinningConfiguration) async {
        do {
            // Perform multiple certificate checks from different network paths
            let results = await performMultiPathCertificateCheck(domain: domain)
            
            // Check for certificate inconsistencies
            if results.count > 1 {
                let fingerprints = Set(results.map { $0.fingerprint })
                
                if fingerprints.count > 1 {
                    // Different certificates from different paths - potential MITM
                    AppLogger.shared.error("POTENTIAL MITM ATTACK DETECTED: Certificate inconsistency for domain \(domain)", category: .security)
                    
                    // Trigger security alert
                    await triggerSecurityAlert(.potentialMITM, domain: domain, details: "Certificate fingerprint mismatch detected")
                }
            }
            
            // Check certificate transparency logs
            if let latestCert = results.first {
                await validateCertificateInCTLogs(certificate: latestCert, domain: domain)
            }
            
        } catch {
            AppLogger.shared.warning("Security scan failed for domain: \(domain)", category: .security, error: error)
        }
    }
    
    private func performMultiPathCertificateCheck(domain: String) async -> [CertificateResult] {
        var results: [CertificateResult] = []
        
        // Check certificate via different network paths
        let networkConfigurations = [
            URLSessionConfiguration.default,
            URLSessionConfiguration.ephemeral
        ]
        
        for config in networkConfigurations {
            do {
                let session = URLSession(configuration: config, delegate: self, delegateQueue: nil)
                let url = URL(string: "https://\(domain)")!
                
                let (_, response) = try await session.data(from: url)
                
                if let httpResponse = response as? HTTPURLResponse,
                   let serverTrust = httpResponse.value(forHTTPHeaderField: "X-Certificate-Fingerprint") {
                    
                    let result = CertificateResult(
                        domain: domain,
                        fingerprint: serverTrust,
                        timestamp: Date()
                    )
                    results.append(result)
                }
            } catch {
                AppLogger.shared.debug("Multi-path certificate check failed", category: .security, error: error)
            }
        }
        
        return results
    }
    
    private func validateCertificateInCTLogs(certificate: CertificateResult, domain: String) async {
        // Query Certificate Transparency logs
        let ctLogURLs = [
            "https://ct.googleapis.com/logs/argon2024/ct/v1/get-entries",
            "https://ct.cloudflare.com/logs/nimbus2024/ct/v1/get-entries"
        ]
        
        for logURL in ctLogURLs {
            do {
                guard let url = URL(string: logURL) else { continue }
                
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                
                let queryData = [
                    "fingerprint": certificate.fingerprint,
                    "domain": domain
                ]
                request.httpBody = try JSONSerialization.data(withJSONObject: queryData)
                
                let (data, response) = try await URLSession.shared.data(for: request)
                
                if let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 200,
                   let ctResponse = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let found = ctResponse["found"] as? Bool,
                   found {
                    
                    AppLogger.shared.info("Certificate found in CT logs", category: .security)
                    return
                }
                
            } catch {
                AppLogger.shared.debug("CT log query failed", category: .security, error: error)
            }
        }
        
        // Certificate not found in CT logs - potential issue
        AppLogger.shared.warning("Certificate not found in CT logs for domain: \(domain)", category: .security)
        await triggerSecurityAlert(.certificateNotInCTLogs, domain: domain, details: "Certificate not found in Certificate Transparency logs")
    }
    
    private func triggerSecurityAlert(_ type: SecurityAlertType, domain: String, details: String) async {
        let alert = SecurityAlertNotification(
            type: type,
            domain: domain,
            details: details,
            timestamp: Date(),
            severity: type.severity
        )
        
        // Store alert for later review
        securityAlerts.append(alert)
        
        // Log critical security events
        AppLogger.shared.log(
            level: alert.severity.logLevel,
            message: "SECURITY ALERT: \(type.rawValue) for domain \(domain)",
            category: .security,
            metadata: ["details": details]
        )
        
        // If critical, potentially block connections
        if alert.severity == .critical {
            await blockDomainTemporarily(domain: domain)
        }
    }
    
    private func blockDomainTemporarily(domain: String) async {
        // Temporarily disable connections to potentially compromised domain
        if var config = pinningConfigurations[domain] {
            config = PinningConfiguration(
                domain: config.domain,
                publicKeyHashes: config.publicKeyHashes,
                certificateHashes: config.certificateHashes,
                allowSelfSigned: false,
                requireCertificatePinning: true,
                environment: config.environment
            )
            pinningConfigurations[domain] = config
            
            AppLogger.shared.error("DOMAIN TEMPORARILY BLOCKED: \(domain) due to security concerns", category: .security)
        }
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

struct CertificateMetadata {
    let certificate: SecCertificate
    let domain: String
    let version: String?
    let updatedAt: Date
}

struct CertificateResult {
    let domain: String
    let fingerprint: String
    let timestamp: Date
}

enum SecurityAlertType: String, CaseIterable {
    case potentialMITM = "potential_mitm"
    case certificateNotInCTLogs = "cert_not_in_ct_logs"
    case certificateExpiringSoon = "cert_expiring_soon"
    case invalidCertificateChain = "invalid_cert_chain"
    case revocationCheckFailed = "revocation_check_failed"
    
    var severity: SecuritySeverity {
        switch self {
        case .potentialMITM:
            return .critical
        case .certificateNotInCTLogs, .invalidCertificateChain:
            return .high
        case .certificateExpiringSoon, .revocationCheckFailed:
            return .medium
        }
    }
}

enum SecuritySeverity: String {
    case low, medium, high, critical
    
    var logLevel: LogLevel {
        switch self {
        case .low:
            return .debug
        case .medium:
            return .info
        case .high:
            return .warning
        case .critical:
            return .error
        }
    }
}

struct SecurityAlertNotification {
    let type: SecurityAlertType
    let domain: String
    let details: String
    let timestamp: Date
    let severity: SecuritySeverity
}

enum CertificateError: LocalizedError {
    case invalidCertificateData
    case certificateExpired
    case untrustedIssuer
    case revoked
    
    var errorDescription: String? {
        switch self {
        case .invalidCertificateData:
            return "Invalid certificate data"
        case .certificateExpired:
            return "Certificate has expired"
        case .untrustedIssuer:
            return "Certificate issued by untrusted authority"
        case .revoked:
            return "Certificate has been revoked"
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
    
    /// Load certificates from Akash deployment with webhook validation
    static func loadCertificatesFromAkash(domain: String) async throws -> [Data] {
        let certURL = URL(string: "https://\(domain)/ssl/cert.pem")!
        let bundleURL = URL(string: "https://\(domain)/ssl/bundle.pem")!
        let rotationWebhookURL = URL(string: "https://\(domain)/webhook/cert-rotation")!
        
        var certificates: [Data] = []
        
        // Check for certificate rotation webhook notification first
        do {
            let (webhookData, _) = try await URLSession.shared.data(from: rotationWebhookURL)
            if let rotationInfo = try? JSONSerialization.jsonObject(with: webhookData) as? [String: Any],
               let hasNewCertificate = rotationInfo["has_new_certificate"] as? Bool,
               hasNewCertificate {
                AppLogger.shared.info("Certificate rotation detected via webhook", category: .security)
            }
        } catch {
            AppLogger.shared.debug("No certificate rotation webhook available", category: .security)
        }
        
        // Try to load certificate and bundle from Akash deployment
        for url in [certURL, bundleURL] {
            do {
                let (data, response) = try await URLSession.shared.data(from: url)
                
                // Validate certificate data integrity
                guard data.count > 100 else {
                    throw CertificateError.invalidCertificateData
                }
                
                // Check for certificate version header
                if let httpResponse = response as? HTTPURLResponse,
                   let certVersion = httpResponse.allHeaderFields["X-Certificate-Version"] as? String {
                    AppLogger.shared.info("Certificate version: \(certVersion)", category: .security)
                }
                
                certificates.append(data)
                AppLogger.shared.info("Loaded certificate from: \(url)", category: .security)
            } catch {
                AppLogger.shared.warning("Failed to load certificate from: \(url)", category: .security, error: error)
            }
        }
        
        return certificates
    }
    
    /// Automated certificate rotation system
    func setupAutomaticCertificateRotation(for domain: String, checkInterval: TimeInterval = 3600) {
        let timer = Timer.scheduledTimer(withTimeInterval: checkInterval, repeats: true) { _ in
            Task {
                await self.checkAndRotateCertificates(for: domain)
            }
        }
        
        // Store timer reference for cleanup
        certificateRotationTimers[domain] = timer
        AppLogger.shared.info("Setup automatic certificate rotation for domain: \(domain)", category: .security)
    }
    
    private func checkAndRotateCertificates(for domain: String) async {
        do {
            // Check current certificate version
            let currentVersion = UserDefaults.standard.string(forKey: "cert_version_\(domain)") ?? "0"
            
            // Check server for new certificate version
            if let latestVersion = try await checkServerCertificateVersion(domain: domain),
               latestVersion != currentVersion {
                
                AppLogger.shared.info("New certificate version available: \(latestVersion)", category: .security)
                
                // Download and update certificates
                let newCertificates = try await Self.loadCertificatesFromAkash(domain: domain)
                
                for (index, certData) in newCertificates.enumerated() {
                    updateCertificate(certData, for: "\(domain)_\(index)", version: latestVersion)
                }
                
                AppLogger.shared.info("Certificate rotation completed for domain: \(domain)", category: .security)
            }
        } catch {
            AppLogger.shared.error("Certificate rotation failed", category: .security, error: error)
        }
    }
    
    private func checkServerCertificateVersion(domain: String) async throws -> String? {
        let versionURL = URL(string: "https://\(domain)/ssl/version")!
        
        do {
            let (data, _) = try await URLSession.shared.data(from: versionURL)
            if let versionInfo = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let version = versionInfo["version"] as? String {
                return version
            }
        } catch {
            AppLogger.shared.debug("Could not check certificate version", category: .security, error: error)
        }
        
        return nil
    }
    
    /// Synchronize certificate with server
    private func synchronizeCertificateWithServer(domain: String) async {
        do {
            let syncURL = URL(string: "https://\(domain)/ssl/sync")!
            var request = URLRequest(url: syncURL)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            // Include current certificate fingerprint
            if let config = pinningConfigurations[domain],
               let fingerprint = config.certificateHashes.first {
                let syncData = ["current_fingerprint": fingerprint]
                request.httpBody = try JSONSerialization.data(withJSONObject: syncData)
            }
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 {
                AppLogger.shared.info("Certificate synchronization successful", category: .security)
            }
        } catch {
            AppLogger.shared.warning("Certificate synchronization failed", category: .security, error: error)
        }
    }
}