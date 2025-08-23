import Foundation
import Network
import Security
import CryptoKit
import UIKit

// MARK: - Network Security Manager
/// Comprehensive network security manager for OMEGA iOS app with Akash Network SSL support
@MainActor
class NetworkSecurityManager: NSObject, ObservableObject {
    
    static let shared = NetworkSecurityManager()
    
    // MARK: - Published Properties
    @Published var isNetworkSecure: Bool = false
    @Published var sslStatus: SSLStatus = .unknown
    @Published var lastSecurityCheck: Date?
    @Published var securityAlerts: [SecurityAlert] = []
    
    // MARK: - Properties
    private let sslPinningManager = SSLCertificatePinningManager.shared
    private let pathMonitor = NWPathMonitor()
    private let securityQueue = DispatchQueue(label: "network.security", qos: .userInitiated)
    private var networkPath: NWPath?
    private var secureURLSession: URLSession?
    
    // Security configuration
    private let minTLSVersion: tls_protocol_version_t = .TLSv12
    private let allowedCipherSuites: [SSLCipherSuite] = [
        SSL_RSA_WITH_AES_256_GCM_SHA384,
        SSL_RSA_WITH_AES_128_GCM_SHA256,
        TLS_AES_256_GCM_SHA384,
        TLS_AES_128_GCM_SHA256,
        TLS_CHACHA20_POLY1305_SHA256
    ]
    
    // MARK: - Initialization
    private override init() {
        super.init()
        setupSecureURLSession()
        startNetworkMonitoring()
        
        Task {
            await performInitialSecurityCheck()
        }
    }
    
    deinit {
        pathMonitor.cancel()
    }
    
    // MARK: - URL Session Configuration
    private func setupSecureURLSession() {
        let configuration = URLSessionConfiguration.default
        
        // Security settings
        configuration.tlsMinimumSupportedProtocolVersion = .TLSv12
        configuration.tlsMaximumSupportedProtocolVersion = .TLSv13
        configuration.requestCachePolicy = .returnCacheDataElseLoad
        configuration.timeoutIntervalForRequest = AppConfig.API.requestTimeout
        configuration.timeoutIntervalForResource = AppConfig.API.resourceTimeout
        
        // Enhanced security headers
        configuration.httpAdditionalHeaders = [
            "User-Agent": createSecureUserAgent(),
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": Locale.preferredLanguages.prefix(3).joined(separator: ", "),
            "DNT": "1", // Do Not Track
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        ]
        
        // Connection pooling and performance
        configuration.httpMaximumConnectionsPerHost = AppConfig.Network.maxConcurrentOperations
        configuration.waitsForConnectivity = true
        configuration.allowsCellularAccess = true
        configuration.allowsConstrainedNetworkAccess = true
        configuration.allowsExpensiveNetworkAccess = true
        
        // Create secure session with SSL pinning
        secureURLSession = URLSession(
            configuration: configuration,
            delegate: self,
            delegateQueue: nil
        )
        
        AppLogger.shared.info("Configured secure URL session with SSL pinning", category: .security)
    }
    
    private func createSecureUserAgent() -> String {
        let appName = AppConfig.App.displayName
        let appVersion = AppConfig.App.version
        let buildNumber = AppConfig.App.buildNumber
        let deviceModel = UIDevice.current.model
        let osVersion = UIDevice.current.systemVersion
        
        return "\(appName)/\(appVersion) (\(buildNumber); \(deviceModel); iOS \(osVersion))"
    }
    
    // MARK: - Network Monitoring
    private func startNetworkMonitoring() {
        pathMonitor.pathUpdateHandler = { [weak self] path in
            Task { @MainActor in
                await self?.handleNetworkPathUpdate(path)
            }
        }
        pathMonitor.start(queue: securityQueue)
    }
    
    private func handleNetworkPathUpdate(_ path: NWPath) async {
        networkPath = path
        
        // Check network security based on connection type
        let wasSecure = isNetworkSecure
        isNetworkSecure = evaluateNetworkSecurity(path)
        
        if isNetworkSecure != wasSecure {
            let alertType: SecurityAlert.AlertType = isNetworkSecure ? .networkSecured : .networkInsecure
            let alert = SecurityAlert(
                type: alertType,
                message: isNetworkSecure ? "Network connection secured" : "Network connection may be insecure",
                severity: isNetworkSecure ? .info : .warning
            )
            addSecurityAlert(alert)
        }
        
        // Perform security check on network changes
        await performNetworkSecurityCheck()
    }
    
    private func evaluateNetworkSecurity(_ path: NWPath) -> Bool {
        // Network is considered secure if:
        // 1. Connection is available
        // 2. Not using unsecured WiFi (if we can detect it)
        // 3. Not using VPN that might intercept traffic (unless it's our own)
        
        guard path.status == .satisfied else {
            return false
        }
        
        // Check for expensive or constrained connections that might indicate cellular
        if path.isExpensive || path.isConstrained {
            // Cellular connections are generally considered more secure than public WiFi
            return true
        }
        
        // For WiFi connections, we assume they could be less secure
        // In production, additional WiFi security checks could be implemented
        return true // Default to secure for now
    }
    
    // MARK: - Security Checks
    
    func performInitialSecurityCheck() async {
        await performNetworkSecurityCheck()
        await performSSLConfigurationCheck()
        await performCertificateValidation()
        
        lastSecurityCheck = Date()
        
        AppLogger.shared.info("Initial security check completed", category: .security, metadata: [
            "network_secure": isNetworkSecure,
            "ssl_status": sslStatus.rawValue
        ])
    }
    
    func performNetworkSecurityCheck() async {
        guard let path = networkPath else {
            isNetworkSecure = false
            return
        }
        
        // Evaluate current network security
        let wasSecure = isNetworkSecure
        isNetworkSecure = evaluateNetworkSecurity(path)
        
        // Log network interface information
        var interfaceTypes: [String] = []
        if path.usesInterfaceType(.wifi) { interfaceTypes.append("WiFi") }
        if path.usesInterfaceType(.cellular) { interfaceTypes.append("Cellular") }
        if path.usesInterfaceType(.wiredEthernet) { interfaceTypes.append("Ethernet") }
        if path.usesInterfaceType(.other) { interfaceTypes.append("Other") }
        
        AppLogger.shared.debug("Network security evaluation", category: .security, metadata: [
            "interfaces": interfaceTypes.joined(separator: ", "),
            "expensive": path.isExpensive,
            "constrained": path.isConstrained,
            "secure": isNetworkSecure
        ])
        
        // Alert on security changes
        if wasSecure != isNetworkSecure {
            let message = isNetworkSecure ? 
                "Network connection secured using \(interfaceTypes.joined(separator: ", "))" :
                "Network connection may be insecure using \(interfaceTypes.joined(separator: ", "))"
            
            addSecurityAlert(SecurityAlert(
                type: isNetworkSecure ? .networkSecured : .networkInsecure,
                message: message,
                severity: isNetworkSecure ? .info : .warning
            ))
        }
    }
    
    func performSSLConfigurationCheck() async {
        // Check SSL configuration for current environment
        let currentEnvironment = AppConfig.currentEnvironment
        let apiBaseURL = AppConfig.API.baseURL
        
        guard let url = URL(string: apiBaseURL),
              let host = url.host else {
            sslStatus = .configurationError
            return
        }
        
        let config = sslPinningManager.getConfiguration(for: host)
        
        switch currentEnvironment {
        case .production:
            if config?.requireCertificatePinning == true {
                sslStatus = .pinningEnabled
            } else {
                sslStatus = .pinningDisabled
                addSecurityAlert(SecurityAlert(
                    type: .sslConfigurationIssue,
                    message: "SSL pinning should be enabled in production",
                    severity: .warning
                ))
            }
            
        case .staging:
            if config?.allowSelfSigned == true {
                sslStatus = .selfSignedAllowed
            } else {
                sslStatus = .standardValidation
            }
            
        case .development:
            sslStatus = .developmentMode
            if !AppConfig.API.allowInsecureHTTP {
                addSecurityAlert(SecurityAlert(
                    type: .sslConfigurationIssue,
                    message: "Development mode should allow insecure HTTP for testing",
                    severity: .info
                ))
            }
        }
        
        AppLogger.shared.info("SSL configuration check completed", category: .security, metadata: [
            "environment": currentEnvironment.rawValue,
            "host": host,
            "ssl_status": sslStatus.rawValue
        ])
    }
    
    func performCertificateValidation() async {
        guard let url = URL(string: AppConfig.API.baseURL),
              let host = url.host else {
            return
        }
        
        let validationResult = await sslPinningManager.validateCertificateChain(for: host)
        
        switch validationResult {
        case .valid(let message):
            AppLogger.shared.info("Certificate validation successful: \(message)", category: .security)
            
        case .warning(let message):
            AppLogger.shared.warning("Certificate validation warning: \(message)", category: .security)
            addSecurityAlert(SecurityAlert(
                type: .certificateWarning,
                message: message,
                severity: .warning
            ))
            
        case .error(let message):
            AppLogger.shared.error("Certificate validation failed: \(message)", category: .security)
            addSecurityAlert(SecurityAlert(
                type: .certificateValidationFailed,
                message: message,
                severity: .error
            ))
        }
    }
    
    // MARK: - Secure Networking
    
    /// Create a secure URL request with proper security headers
    func createSecureRequest(for url: URL, method: HTTPMethod = .GET) -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.timeoutInterval = AppConfig.API.requestTimeout
        
        // Security headers
        request.setValue(createSecureUserAgent(), forHTTPHeaderField: "User-Agent")
        request.setValue("no-cache", forHTTPHeaderField: "Cache-Control")
        request.setValue("no-store", forHTTPHeaderField: "Pragma")
        request.setValue("1", forHTTPHeaderField: "DNT")
        
        // API-specific headers
        if method != .GET {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        // CSRF protection
        let csrfToken = generateCSRFToken()
        request.setValue(csrfToken, forHTTPHeaderField: "X-CSRF-Token")
        
        // Authentication
        if let token = AuthManager.shared.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        return request
    }
    
    /// Perform secure data task using configured SSL pinning
    func performSecureDataTask(
        with request: URLRequest
    ) async throws -> (Data, URLResponse) {
        guard let session = secureURLSession else {
            throw NetworkSecurityError.sessionNotConfigured
        }
        
        // Log request for security audit
        AppLogger.shared.debug("Performing secure network request", category: .security, metadata: [
            "url": request.url?.absoluteString ?? "unknown",
            "method": request.httpMethod ?? "unknown"
        ])
        
        do {
            let (data, response) = try await session.data(for: request)
            
            // Validate response security
            try validateResponseSecurity(response)
            
            return (data, response)
            
        } catch let error as URLError {
            AppLogger.shared.error("Secure network request failed", category: .security, error: error)
            throw NetworkSecurityError.networkError(error)
        } catch {
            AppLogger.shared.error("Unexpected network error", category: .security, error: error)
            throw NetworkSecurityError.unknownError(error)
        }
    }
    
    private func validateResponseSecurity(_ response: URLResponse) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkSecurityError.invalidResponse
        }
        
        // Enhanced security header validation
        let requiredSecurityHeaders = [
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block"
        ]
        
        let recommendedHeaders = [
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy"
        ]
        
        var missingCriticalHeaders: [String] = []
        var weakSecurityHeaders: [String: String] = [:]
        
        // Validate required headers
        for (header, expectedValue) in requiredSecurityHeaders {
            if let actualValue = httpResponse.allHeaderFields[header] as? String {
                // Check if the value meets minimum security requirements
                if !validateSecurityHeaderValue(header: header, value: actualValue, expected: expectedValue) {
                    weakSecurityHeaders[header] = actualValue
                }
            } else {
                missingCriticalHeaders.append(header)
            }
        }
        
        // Check CSP policy specifically
        if let cspHeader = httpResponse.allHeaderFields["Content-Security-Policy"] as? String {
            try validateCSPPolicy(cspHeader)
        } else if AppConfig.currentEnvironment == .production {
            missingCriticalHeaders.append("Content-Security-Policy")
        }
        
        // Log security issues
        if !missingCriticalHeaders.isEmpty {
            AppLogger.shared.error("Critical security headers missing", category: .security, metadata: [
                "missing_headers": missingCriticalHeaders
            ])
            
            if AppConfig.currentEnvironment == .production {
                throw NetworkSecurityError.missingSecurityHeaders(missingCriticalHeaders)
            }
        }
        
        if !weakSecurityHeaders.isEmpty {
            AppLogger.shared.warning("Weak security headers detected", category: .security, metadata: [
                "weak_headers": weakSecurityHeaders
            ])
        }
        
        // Validate HSTS header specifically
        if let hstsHeader = httpResponse.allHeaderFields["Strict-Transport-Security"] as? String {
            try validateHSTSHeader(hstsHeader)
        }
        
        // Validate status code
        guard 200..<300 ~= httpResponse.statusCode else {
            throw NetworkSecurityError.httpError(httpResponse.statusCode)
        }
        
        // Check for certificate pinning validation
        try validateCertificatePinningHeaders(httpResponse)
    }
    
    /// Validate security header values
    private func validateSecurityHeaderValue(header: String, value: String, expected: String) -> Bool {
        switch header {
        case "Strict-Transport-Security":
            // Check for minimum max-age and includeSubDomains
            return value.contains("max-age=") && 
                   value.contains("includeSubDomains") &&
                   extractMaxAge(from: value) >= 31536000 // 1 year minimum
            
        case "X-Content-Type-Options":
            return value.lowercased() == "nosniff"
            
        case "X-Frame-Options":
            return ["DENY", "SAMEORIGIN"].contains(value.uppercased())
            
        case "X-XSS-Protection":
            return value.contains("1") && value.contains("mode=block")
            
        default:
            return true
        }
    }
    
    /// Extract max-age value from HSTS header
    private func extractMaxAge(from hstsHeader: String) -> Int {
        let regex = try? NSRegularExpression(pattern: "max-age=(\\d+)", options: [])
        let nsString = hstsHeader as NSString
        let results = regex?.matches(in: hstsHeader, options: [], range: NSRange(location: 0, length: nsString.length))
        
        if let match = results?.first,
           match.numberOfRanges > 1 {
            let range = match.range(at: 1)
            let maxAgeString = nsString.substring(with: range)
            return Int(maxAgeString) ?? 0
        }
        
        return 0
    }
    
    /// Validate HSTS header
    private func validateHSTSHeader(_ hstsHeader: String) throws {
        let maxAge = extractMaxAge(from: hstsHeader)
        
        guard maxAge >= 31536000 else { // 1 year minimum
            throw NetworkSecurityError.weakHSTS("HSTS max-age too short: \(maxAge)")
        }
        
        guard hstsHeader.contains("includeSubDomains") else {
            throw NetworkSecurityError.weakHSTS("HSTS missing includeSubDomains")
        }
        
        if AppConfig.currentEnvironment == .production {
            guard hstsHeader.contains("preload") else {
                AppLogger.shared.warning("HSTS preload recommended for production", category: .security)
                return
            }
        }
    }
    
    /// Validate Content Security Policy
    private func validateCSPPolicy(_ cspHeader: String) throws {
        let policies = cspHeader.components(separatedBy: ";")
        
        var hasDefaultSrc = false
        var hasScriptSrc = false
        var hasUnsafeEval = false
        var hasUnsafeInline = false
        
        for policy in policies {
            let trimmedPolicy = policy.trimmingCharacters(in: .whitespacesAndNewlines)
            
            if trimmedPolicy.hasPrefix("default-src") {
                hasDefaultSrc = true
            }
            
            if trimmedPolicy.hasPrefix("script-src") {
                hasScriptSrc = true
                
                if trimmedPolicy.contains("'unsafe-eval'") {
                    hasUnsafeEval = true
                }
                
                if trimmedPolicy.contains("'unsafe-inline'") {
                    hasUnsafeInline = true
                }
            }
        }
        
        // Validate CSP strength
        if hasUnsafeEval || hasUnsafeInline {
            if AppConfig.currentEnvironment == .production {
                throw NetworkSecurityError.unsafeCSPPolicy("CSP contains unsafe-eval or unsafe-inline")
            } else {
                AppLogger.shared.warning("CSP contains unsafe directives", category: .security)
            }
        }
        
        if !hasDefaultSrc && !hasScriptSrc {
            AppLogger.shared.warning("CSP missing default-src or script-src directive", category: .security)
        }
    }
    
    /// Validate certificate pinning headers
    private func validateCertificatePinningHeaders(_ response: HTTPURLResponse) throws {
        // Check for Public Key Pinning header
        if let pkpHeader = response.allHeaderFields["Public-Key-Pins"] as? String {
            try validatePublicKeyPinningHeader(pkpHeader)
        }
        
        // Check for Expect-CT header
        if let expectCTHeader = response.allHeaderFields["Expect-CT"] as? String {
            try validateExpectCTHeader(expectCTHeader)
        }
    }
    
    private func validatePublicKeyPinningHeader(_ pkpHeader: String) throws {
        guard pkpHeader.contains("pin-") && pkpHeader.contains("max-age=") else {
            throw NetworkSecurityError.invalidPKPHeader("Malformed PKP header")
        }
        
        let maxAge = extractMaxAge(from: pkpHeader)
        guard maxAge > 0 else {
            throw NetworkSecurityError.invalidPKPHeader("PKP max-age must be positive")
        }
        
        AppLogger.shared.info("Public Key Pinning validated", category: .security)
    }
    
    private func validateExpectCTHeader(_ expectCTHeader: String) throws {
        let maxAge = extractMaxAge(from: expectCTHeader)
        guard maxAge > 0 else {
            throw NetworkSecurityError.invalidExpectCTHeader("Expect-CT max-age must be positive")
        }
        
        AppLogger.shared.info("Expect-CT header validated", category: .security)
    }
    
    // MARK: - Security Alerts
    
    private func addSecurityAlert(_ alert: SecurityAlert) {
        securityAlerts.append(alert)
        
        // Keep only the last 50 alerts
        if securityAlerts.count > 50 {
            securityAlerts.removeFirst(securityAlerts.count - 50)
        }
        
        AppLogger.shared.log(
            level: alert.severity.logLevel,
            message: alert.message,
            category: .security,
            metadata: ["alert_type": alert.type.rawValue]
        )
    }
    
    func clearSecurityAlerts() {
        securityAlerts.removeAll()
    }
    
    func getActiveSecurityAlerts() -> [SecurityAlert] {
        let fiveMinutesAgo = Date().addingTimeInterval(-300)
        return securityAlerts.filter { $0.timestamp > fiveMinutesAgo }
    }
    
    // MARK: - Utility Methods
    
    private func generateCSRFToken() -> String {
        let tokenData = Data((0..<32).map { _ in UInt8.random(in: 0...255) })
        return tokenData.base64EncodedString()
    }
    
    /// Get network security status summary
    func getSecurityStatusSummary() -> NetworkSecuritySummary {
        return NetworkSecuritySummary(
            isNetworkSecure: isNetworkSecure,
            sslStatus: sslStatus,
            activeAlerts: getActiveSecurityAlerts().count,
            lastCheckTime: lastSecurityCheck,
            environment: AppConfig.currentEnvironment
        )
    }
    
    /// Force refresh of all security checks
    func refreshSecurityStatus() async {
        await performInitialSecurityCheck()
    }
}

// MARK: - URLSessionDelegate
extension NetworkSecurityManager: URLSessionDelegate {
    
    nonisolated func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        // Delegate SSL validation to our SSL pinning manager
        sslPinningManager.urlSession(session, didReceive: challenge, completionHandler: completionHandler)
    }
    
    nonisolated func urlSession(
        _ session: URLSession,
        task: URLSessionTask,
        didCompleteWithError error: Error?
    ) {
        if let error = error {
            Task { @MainActor in
                let alert = SecurityAlert(
                    type: .networkError,
                    message: "Network task failed: \(error.localizedDescription)",
                    severity: .error
                )
                await MainActor.run {
                    self.addSecurityAlert(alert)
                }
            }
        }
    }
}

// MARK: - Supporting Types

enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case DELETE = "DELETE"
    case PATCH = "PATCH"
}

enum SSLStatus: String, CaseIterable {
    case unknown = "unknown"
    case pinningEnabled = "pinning_enabled"
    case pinningDisabled = "pinning_disabled"
    case selfSignedAllowed = "self_signed_allowed"
    case standardValidation = "standard_validation"
    case configurationError = "configuration_error"
    case developmentMode = "development_mode"
    
    var isSecure: Bool {
        switch self {
        case .pinningEnabled, .selfSignedAllowed, .standardValidation, .developmentMode:
            return true
        case .unknown, .pinningDisabled, .configurationError:
            return false
        }
    }
}

struct SecurityAlert: Identifiable, Equatable {
    let id = UUID()
    let type: AlertType
    let message: String
    let severity: Severity
    let timestamp: Date
    
    init(type: AlertType, message: String, severity: Severity) {
        self.type = type
        self.message = message
        self.severity = severity
        self.timestamp = Date()
    }
    
    enum AlertType: String, CaseIterable {
        case networkSecured = "network_secured"
        case networkInsecure = "network_insecure"
        case sslConfigurationIssue = "ssl_configuration_issue"
        case certificateWarning = "certificate_warning"
        case certificateValidationFailed = "certificate_validation_failed"
        case networkError = "network_error"
    }
    
    enum Severity: String, CaseIterable {
        case info = "info"
        case warning = "warning"
        case error = "error"
        
        var logLevel: LogLevel {
            switch self {
            case .info:
                return .info
            case .warning:
                return .warning
            case .error:
                return .error
            }
        }
    }
}

struct NetworkSecuritySummary {
    let isNetworkSecure: Bool
    let sslStatus: SSLStatus
    let activeAlerts: Int
    let lastCheckTime: Date?
    let environment: AppEnvironment
    
    var overallSecurityStatus: SecurityStatus {
        if activeAlerts > 0 {
            return .warning
        }
        return isNetworkSecure && sslStatus.isSecure ? .secure : .insecure
    }
    
    enum SecurityStatus {
        case secure
        case warning
        case insecure
        
        var color: String {
            switch self {
            case .secure:
                return "green"
            case .warning:
                return "orange"
            case .insecure:
                return "red"
            }
        }
    }
}

enum NetworkSecurityError: LocalizedError {
    case sessionNotConfigured
    case invalidResponse
    case networkError(URLError)
    case httpError(Int)
    case sslValidationFailed
    case unknownError(Error)
    case missingSecurityHeaders([String])
    case weakHSTS(String)
    case unsafeCSPPolicy(String)
    case invalidPKPHeader(String)
    case invalidExpectCTHeader(String)
    
    var errorDescription: String? {
        switch self {
        case .sessionNotConfigured:
            return "Secure network session not configured"
        case .invalidResponse:
            return "Invalid network response received"
        case .networkError(let urlError):
            return "Network error: \(urlError.localizedDescription)"
        case .httpError(let statusCode):
            return "HTTP error: \(statusCode)"
        case .sslValidationFailed:
            return "SSL certificate validation failed"
        case .unknownError(let error):
            return "Unknown network error: \(error.localizedDescription)"
        case .missingSecurityHeaders(let headers):
            return "Missing critical security headers: \(headers.joined(separator: ", "))"
        case .weakHSTS(let details):
            return "Weak HSTS configuration: \(details)"
        case .unsafeCSPPolicy(let details):
            return "Unsafe Content Security Policy: \(details)"
        case .invalidPKPHeader(let details):
            return "Invalid Public Key Pinning header: \(details)"
        case .invalidExpectCTHeader(let details):
            return "Invalid Expect-CT header: \(details)"
        }
    }
}