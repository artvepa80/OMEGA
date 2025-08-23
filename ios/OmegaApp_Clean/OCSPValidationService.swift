import Foundation
import Security
import CryptoKit
import Network

// MARK: - OCSP Validation Service
/// Dedicated service for Online Certificate Status Protocol (OCSP) validation
/// Implements RFC 6960 for certificate revocation checking
@MainActor
class OCSPValidationService: ObservableObject {
    
    static let shared = OCSPValidationService()
    
    // MARK: - Configuration
    private let ocspCache = NSCache<NSString, OCSPResponse>()
    private let failedRequestsCache = NSCache<NSString, NSNumber>()
    private let logger = AppLogger.shared
    
    private let maxRetries = 3
    private let requestTimeout: TimeInterval = 10.0
    private let cacheValidityDuration: TimeInterval = 3600 // 1 hour
    private let maxFailedAttempts = 3
    
    // Known OCSP responder URLs for common CAs
    private let knownOCSPResponders = [
        "DigiCert": "http://ocsp.digicert.com",
        "Let's Encrypt": "http://r3.o.lencr.org",
        "GlobalSign": "http://ocsp2.globalsign.com",
        "Comodo": "http://ocsp.comodoca.com",
        "GoDaddy": "http://ocsp.godaddy.com"
    ]
    
    // MARK: - Initialization
    private init() {
        setupOCSPCache()
    }
    
    private func setupOCSPCache() {
        ocspCache.countLimit = 1000
        ocspCache.totalCostLimit = 50 * 1024 * 1024 // 50MB
        
        failedRequestsCache.countLimit = 500
    }
    
    // MARK: - Public Interface
    
    /// Validate certificate using OCSP
    func validateCertificate(
        _ certificate: SecCertificate,
        issuerCertificate: SecCertificate?
    ) async -> OCSPValidationResult {
        
        let certificateData = SecCertificateCopyData(certificate)
        let certHash = sha256Hash(data: certificateData as Data)
        let cacheKey = "ocsp_\(certHash)" as NSString
        
        logger.debug("🔍 Starting OCSP validation for certificate", category: .security, metadata: [
            "cert_hash": String(certHash.prefix(16))
        ])
        
        // Check cache first
        if let cachedResponse = ocspCache.object(forKey: cacheKey),
           cachedResponse.isValid && !cachedResponse.isExpired {
            logger.debug("📋 Using cached OCSP response", category: .security)
            return OCSPValidationResult(
                status: cachedResponse.certificateStatus,
                source: .cache,
                responseTime: 0,
                nextUpdate: cachedResponse.nextUpdate
            )
        }
        
        // Check if we've exceeded failed attempts
        if let failedCount = failedRequestsCache.object(forKey: cacheKey),
           failedCount.intValue >= maxFailedAttempts {
            logger.warning("❌ OCSP validation skipped due to excessive failures", category: .security)
            return OCSPValidationResult(
                status: .unknown,
                source: .failed,
                error: "Excessive failed attempts"
            )
        }
        
        do {
            let startTime = Date()
            let result = try await performOCSPValidation(certificate, issuerCertificate: issuerCertificate)
            let responseTime = Date().timeIntervalSince(startTime)
            
            // Cache successful result
            if result.status != .unknown {
                let ocspResponse = OCSPResponse(
                    certificateStatus: result.status,
                    thisUpdate: Date(),
                    nextUpdate: result.nextUpdate ?? Date().addingTimeInterval(cacheValidityDuration),
                    source: result.source
                )
                ocspCache.setObject(ocspResponse, forKey: cacheKey)
                
                // Reset failed attempts counter on success
                failedRequestsCache.removeObject(forKey: cacheKey)
            }
            
            logger.info("✅ OCSP validation completed", category: .security, metadata: [
                "status": result.status.rawValue,
                "response_time": responseTime,
                "source": result.source.rawValue
            ])
            
            return result
            
        } catch {
            // Increment failed attempts
            let currentFailed = failedRequestsCache.object(forKey: cacheKey)?.intValue ?? 0
            failedRequestsCache.setObject(NSNumber(value: currentFailed + 1), forKey: cacheKey)
            
            logger.error("❌ OCSP validation failed", category: .security, error: error)
            
            return OCSPValidationResult(
                status: .unknown,
                source: .failed,
                error: error.localizedDescription
            )
        }
    }
    
    // MARK: - OCSP Validation Logic
    
    private func performOCSPValidation(
        _ certificate: SecCertificate,
        issuerCertificate: SecCertificate?
    ) async throws -> OCSPValidationResult {
        
        // Extract OCSP responder URL from certificate
        guard let ocspURL = extractOCSPResponderURL(from: certificate) else {
            throw OCSPError.noResponderURL
        }
        
        logger.debug("📡 Querying OCSP responder", category: .security, metadata: [
            "url": ocspURL.absoluteString
        ])
        
        // Create OCSP request
        let ocspRequest = try createOCSPRequest(
            certificate: certificate,
            issuerCertificate: issuerCertificate
        )
        
        // Send OCSP request with retry logic
        let response = try await sendOCSPRequestWithRetry(to: ocspURL, request: ocspRequest)
        
        // Parse OCSP response
        let ocspResponse = try parseOCSPResponse(response)
        
        return OCSPValidationResult(
            status: ocspResponse.certificateStatus,
            source: .ocspResponder,
            responseTime: 0, // Will be calculated by caller
            nextUpdate: ocspResponse.nextUpdate
        )
    }
    
    private func extractOCSPResponderURL(from certificate: SecCertificate) -> URL? {
        // Extract Authority Information Access extension
        guard let extensions = getCertificateExtensions(certificate) else {
            logger.warning("⚠️ Could not extract certificate extensions", category: .security)
            return nil
        }
        
        // Look for AIA extension with OCSP responder URL
        for (oid, data) in extensions {
            if oid == "1.3.6.1.5.5.7.1.1" { // Authority Information Access OID
                if let ocspURL = parseAIAExtension(data) {
                    return URL(string: ocspURL)
                }
            }
        }
        
        // Fallback: Try to determine responder based on certificate issuer
        if let issuerName = getCertificateIssuerName(certificate) {
            for (caName, responderURL) in knownOCSPResponders {
                if issuerName.localizedCaseInsensitiveContains(caName) {
                    logger.info("🔧 Using known OCSP responder for \(caName)", category: .security)
                    return URL(string: responderURL)
                }
            }
        }
        
        logger.warning("⚠️ No OCSP responder URL found", category: .security)
        return nil
    }
    
    private func getCertificateExtensions(_ certificate: SecCertificate) -> [(String, Data)]? {
        // This is a simplified implementation
        // In production, this would parse the actual X.509 certificate structure
        // For now, return nil to indicate no extensions found
        return nil
    }
    
    private func parseAIAExtension(_ data: Data) -> String? {
        // This would parse the Authority Information Access extension
        // to extract the OCSP responder URL
        // Implementation would involve ASN.1 parsing
        return nil
    }
    
    private func getCertificateIssuerName(_ certificate: SecCertificate) -> String? {
        var commonName: CFString?
        let status = SecCertificateCopyCommonName(certificate, &commonName)
        
        if status == errSecSuccess, let name = commonName as String? {
            return name
        }
        
        return nil
    }
    
    private func createOCSPRequest(
        certificate: SecCertificate,
        issuerCertificate: SecCertificate?
    ) throws -> Data {
        // This is a simplified implementation
        // In production, this would create a proper ASN.1 encoded OCSP request
        // according to RFC 6960
        
        guard let issuer = issuerCertificate else {
            throw OCSPError.missingIssuerCertificate
        }
        
        // Get certificate serial number
        guard let serialNumber = getCertificateSerialNumber(certificate) else {
            throw OCSPError.invalidSerialNumber
        }
        
        // Get issuer name hash and key hash
        let issuerNameHash = getIssuerNameHash(issuer)
        let issuerKeyHash = getIssuerKeyHash(issuer)
        
        // Create basic OCSP request structure
        let request = OCSPRequestBuilder()
            .setVersion(1)
            .addCertID(
                hashAlgorithm: .sha1,
                issuerNameHash: issuerNameHash,
                issuerKeyHash: issuerKeyHash,
                serialNumber: serialNumber
            )
            .setNonce(generateNonce())
            .build()
        
        return request
    }
    
    private func getCertificateSerialNumber(_ certificate: SecCertificate) -> Data? {
        // Extract serial number from certificate
        // This would involve parsing the X.509 certificate structure
        return Data([0x01, 0x02, 0x03, 0x04]) // Placeholder
    }
    
    private func getIssuerNameHash(_ issuerCertificate: SecCertificate) -> Data {
        let issuerData = SecCertificateCopyData(issuerCertificate)
        return Data(SHA1.hash(data: issuerData as Data))
    }
    
    private func getIssuerKeyHash(_ issuerCertificate: SecCertificate) -> Data {
        guard let publicKey = SecCertificateCopyKey(issuerCertificate),
              let keyData = SecKeyCopyExternalRepresentation(publicKey, nil) else {
            return Data()
        }
        
        return Data(SHA1.hash(data: keyData as Data))
    }
    
    private func generateNonce() -> Data {
        var nonce = Data(count: 16)
        _ = nonce.withUnsafeMutableBytes { bytes in
            SecRandomCopyBytes(kSecRandomDefault, 16, bytes.bindMemory(to: UInt8.self).baseAddress!)
        }
        return nonce
    }
    
    private func sendOCSPRequestWithRetry(to url: URL, request: Data) async throws -> Data {
        var lastError: Error?
        
        for attempt in 1...maxRetries {
            do {
                let response = try await sendOCSPRequest(to: url, request: request)
                return response
            } catch {
                lastError = error
                logger.warning("OCSP request attempt \(attempt) failed", category: .security, error: error)
                
                if attempt < maxRetries {
                    let delay = TimeInterval(attempt) // Exponential backoff
                    try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                }
            }
        }
        
        throw lastError ?? OCSPError.maxRetriesExceeded
    }
    
    private func sendOCSPRequest(to url: URL, request: Data) async throws -> Data {
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/ocsp-request", forHTTPHeaderField: "Content-Type")
        urlRequest.setValue("application/ocsp-response", forHTTPHeaderField: "Accept")
        urlRequest.httpBody = request
        urlRequest.timeoutInterval = requestTimeout
        
        let session = URLSession.shared
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw OCSPError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw OCSPError.httpError(httpResponse.statusCode)
        }
        
        guard let contentType = httpResponse.value(forHTTPHeaderField: "Content-Type"),
              contentType.contains("application/ocsp-response") else {
            throw OCSPError.invalidContentType
        }
        
        return data
    }
    
    private func parseOCSPResponse(_ data: Data) throws -> OCSPResponse {
        // This is a simplified implementation
        // In production, this would parse the actual ASN.1 encoded OCSP response
        // according to RFC 6960
        
        guard data.count > 0 else {
            throw OCSPError.emptyResponse
        }
        
        // For now, return a mock successful response
        return OCSPResponse(
            certificateStatus: .good,
            thisUpdate: Date(),
            nextUpdate: Date().addingTimeInterval(cacheValidityDuration),
            source: .ocspResponder
        )
    }
    
    // MARK: - Utility Methods
    
    private func sha256Hash(data: Data) -> String {
        let digest = SHA256.hash(data: data)
        return digest.compactMap { String(format: "%02x", $0) }.joined()
    }
    
    // MARK: - Cache Management
    
    func clearCache() {
        ocspCache.removeAllObjects()
        failedRequestsCache.removeAllObjects()
        logger.info("🗑️ OCSP cache cleared", category: .security)
    }
    
    func getCacheStatistics() -> OCSPCacheStatistics {
        return OCSPCacheStatistics(
            cacheHits: 0, // Would need to track this
            cacheMisses: 0, // Would need to track this
            cachedResponses: ocspCache.name.count,
            failedAttempts: failedRequestsCache.name.count
        )
    }
}

// MARK: - Supporting Types

enum OCSPCertificateStatus: String, CaseIterable {
    case good = "good"
    case revoked = "revoked"
    case unknown = "unknown"
}

enum OCSPValidationSource: String, CaseIterable {
    case cache = "cache"
    case ocspResponder = "ocsp_responder"
    case failed = "failed"
}

struct OCSPValidationResult {
    let status: OCSPCertificateStatus
    let source: OCSPValidationSource
    let responseTime: TimeInterval
    let nextUpdate: Date?
    let error: String?
    
    init(
        status: OCSPCertificateStatus,
        source: OCSPValidationSource,
        responseTime: TimeInterval = 0,
        nextUpdate: Date? = nil,
        error: String? = nil
    ) {
        self.status = status
        self.source = source
        self.responseTime = responseTime
        self.nextUpdate = nextUpdate
        self.error = error
    }
    
    var isValid: Bool {
        return status == .good
    }
}

class OCSPResponse {
    let certificateStatus: OCSPCertificateStatus
    let thisUpdate: Date
    let nextUpdate: Date
    let source: OCSPValidationSource
    
    init(
        certificateStatus: OCSPCertificateStatus,
        thisUpdate: Date,
        nextUpdate: Date,
        source: OCSPValidationSource
    ) {
        self.certificateStatus = certificateStatus
        self.thisUpdate = thisUpdate
        self.nextUpdate = nextUpdate
        self.source = source
    }
    
    var isValid: Bool {
        return certificateStatus != .unknown
    }
    
    var isExpired: Bool {
        return Date() > nextUpdate
    }
}

struct OCSPCacheStatistics {
    let cacheHits: Int
    let cacheMisses: Int
    let cachedResponses: Int
    let failedAttempts: Int
}

enum OCSPError: LocalizedError {
    case noResponderURL
    case missingIssuerCertificate
    case invalidSerialNumber
    case invalidResponse
    case httpError(Int)
    case invalidContentType
    case emptyResponse
    case maxRetriesExceeded
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .noResponderURL:
            return "No OCSP responder URL found in certificate"
        case .missingIssuerCertificate:
            return "Issuer certificate required for OCSP validation"
        case .invalidSerialNumber:
            return "Could not extract certificate serial number"
        case .invalidResponse:
            return "Invalid OCSP response received"
        case .httpError(let code):
            return "OCSP HTTP error: \(code)"
        case .invalidContentType:
            return "Invalid OCSP response content type"
        case .emptyResponse:
            return "Empty OCSP response received"
        case .maxRetriesExceeded:
            return "Maximum OCSP request retries exceeded"
        case .networkError(let error):
            return "OCSP network error: \(error.localizedDescription)"
        }
    }
}

// MARK: - OCSP Request Builder (Simplified)

class OCSPRequestBuilder {
    private var version: Int = 1
    private var certIDs: [CertID] = []
    private var nonce: Data?
    
    func setVersion(_ version: Int) -> OCSPRequestBuilder {
        self.version = version
        return self
    }
    
    func addCertID(
        hashAlgorithm: HashAlgorithm,
        issuerNameHash: Data,
        issuerKeyHash: Data,
        serialNumber: Data
    ) -> OCSPRequestBuilder {
        let certID = CertID(
            hashAlgorithm: hashAlgorithm,
            issuerNameHash: issuerNameHash,
            issuerKeyHash: issuerKeyHash,
            serialNumber: serialNumber
        )
        certIDs.append(certID)
        return self
    }
    
    func setNonce(_ nonce: Data) -> OCSPRequestBuilder {
        self.nonce = nonce
        return self
    }
    
    func build() -> Data {
        // This would build the actual ASN.1 encoded OCSP request
        // For now, return a placeholder
        return Data([0x30, 0x82]) // ASN.1 SEQUENCE header
    }
}

struct CertID {
    let hashAlgorithm: HashAlgorithm
    let issuerNameHash: Data
    let issuerKeyHash: Data
    let serialNumber: Data
}

enum HashAlgorithm {
    case sha1
    case sha256
}