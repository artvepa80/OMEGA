import Foundation
import SwiftUI
import Network

// MARK: - SSL Error Handler
/// Comprehensive SSL error handling and user interaction for OMEGA iOS app
@MainActor
class SSLErrorHandler: ObservableObject {
    
    static let shared = SSLErrorHandler()
    
    // MARK: - Published Properties
    @Published var currentAlert: SSLErrorAlert?
    @Published var showingAlert = false
    @Published var errorHistory: [SSLErrorRecord] = []
    
    // MARK: - Properties
    private let maxErrorHistory = 100
    private var retryAttempts: [String: Int] = [:]
    private let maxRetryAttempts = 3
    
    private init() {}
    
    // MARK: - Public Methods
    
    /// Handle SSL-related errors and present appropriate user interface
    func handleSSLError(
        _ error: SSLError,
        for domain: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) {
        // Record the error
        recordError(error, domain: domain)
        
        // Determine appropriate user action
        let alert = createAlertForError(error, domain: domain, completion: completion)
        
        // Present alert to user
        presentAlert(alert)
    }
    
    /// Handle network errors that might be SSL-related
    func handleNetworkError(
        _ error: Error,
        for domain: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) {
        if let urlError = error as? URLError {
            handleURLError(urlError, domain: domain, completion: completion)
        } else {
            // Generic network error
            let sslError = SSLError.networkConnectionFailed(error.localizedDescription)
            handleSSLError(sslError, for: domain, completion: completion)
        }
    }
    
    private func handleURLError(
        _ urlError: URLError,
        domain: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) {
        let sslError: SSLError
        
        switch urlError.code {
        case .serverCertificateUntrusted:
            sslError = .untrustedCertificate("The server certificate is not trusted")
            
        case .serverCertificateHasBadDate:
            sslError = .certificateExpired("The server certificate has expired or is not yet valid")
            
        case .serverCertificateHasUnknownRoot:
            sslError = .untrustedRootCertificate("The server certificate has an unknown root certificate")
            
        case .clientCertificateRejected:
            sslError = .certificateRejected("The client certificate was rejected by the server")
            
        case .cannotConnectToHost:
            sslError = .connectionFailed("Cannot connect to the server. This might be due to SSL/TLS configuration issues.")
            
        case .secureConnectionFailed:
            sslError = .sslHandshakeFailed("SSL/TLS handshake failed")
            
        case .cancelled:
            sslError = .userCancelled
            
        default:
            sslError = .networkConnectionFailed(urlError.localizedDescription)
        }
        
        handleSSLError(sslError, for: domain, completion: completion)
    }
    
    // MARK: - Alert Creation
    
    private func createAlertForError(
        _ error: SSLError,
        domain: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        switch error {
        case .untrustedCertificate(let details):
            return createUntrustedCertificateAlert(domain: domain, details: details, completion: completion)
            
        case .certificateExpired(let details):
            return createCertificateExpiredAlert(domain: domain, details: details, completion: completion)
            
        case .certificateMismatch(let expectedHost, let actualHost):
            return createCertificateMismatchAlert(
                domain: domain,
                expectedHost: expectedHost,
                actualHost: actualHost,
                completion: completion
            )
            
        case .sslHandshakeFailed(let details):
            return createHandshakeFailedAlert(domain: domain, details: details, completion: completion)
            
        case .invalidCertificateChain(let details):
            return createInvalidChainAlert(domain: domain, details: details, completion: completion)
            
        case .networkConnectionFailed(let details):
            return createNetworkFailedAlert(domain: domain, details: details, completion: completion)
            
        case .userCancelled:
            // Don't show alert for user cancellation
            completion(.cancel)
            return SSLErrorAlert(
                title: "",
                message: "",
                actions: [],
                severity: .info
            )
            
        case .connectionFailed(let details):
            return createConnectionFailedAlert(domain: domain, details: details, completion: completion)
            
        case .untrustedRootCertificate(let details):
            return createUntrustedRootAlert(domain: domain, details: details, completion: completion)
            
        case .certificateRejected(let details):
            return createCertificateRejectedAlert(domain: domain, details: details, completion: completion)
        }
    }
    
    private func createUntrustedCertificateAlert(
        domain: String,
        details: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        let isDevelopment = AppConfig.currentEnvironment == .development
        let allowSelfSigned = SSLCertificatePinningManager.shared.getConfiguration(for: domain)?.allowSelfSigned ?? false
        
        var actions: [SSLErrorAlert.Action] = []
        
        if isDevelopment || allowSelfSigned {
            actions.append(.init(
                title: "Permitir Esta Vez",
                style: .destructive,
                action: { completion(.allowOnce) }
            ))
        }
        
        actions.append(contentsOf: [
            .init(
                title: "Ver Detalles",
                style: .default,
                action: { [weak self] in
                    self?.showCertificateDetails(domain: domain)
                    completion(.showDetails)
                }
            ),
            .init(
                title: "Cancelar",
                style: .cancel,
                action: { completion(.cancel) }
            )
        ])
        
        return SSLErrorAlert(
            title: "Certificado No Confiable",
            message: "El certificado SSL del servidor \(domain) no es confiable.\n\nDetalles: \(details)",
            actions: actions,
            severity: .error
        )
    }
    
    private func createCertificateExpiredAlert(
        domain: String,
        details: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        SSLErrorAlert(
            title: "Certificado Expirado",
            message: "El certificado SSL de \(domain) ha expirado o no es válido aún.\n\nDetalles: \(details)",
            actions: [
                .init(
                    title: "Actualizar Certificado",
                    style: .default,
                    action: { [weak self] in
                        self?.requestCertificateUpdate(domain: domain)
                        completion(.updateCertificate)
                    }
                ),
                .init(
                    title: "Cancelar",
                    style: .cancel,
                    action: { completion(.cancel) }
                )
            ],
            severity: .error
        )
    }
    
    private func createCertificateMismatchAlert(
        domain: String,
        expectedHost: String,
        actualHost: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        SSLErrorAlert(
            title: "Certificado No Coincide",
            message: "El certificado SSL no coincide con el dominio.\n\nEsperado: \(expectedHost)\nRecibido: \(actualHost)",
            actions: [
                .init(
                    title: "Ver Detalles",
                    style: .default,
                    action: { [weak self] in
                        self?.showCertificateDetails(domain: domain)
                        completion(.showDetails)
                    }
                ),
                .init(
                    title: "Cancelar",
                    style: .cancel,
                    action: { completion(.cancel) }
                )
            ],
            severity: .error
        )
    }
    
    private func createHandshakeFailedAlert(
        domain: String,
        details: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        SSLErrorAlert(
            title: "Error de Conexión SSL",
            message: "No se pudo establecer una conexión SSL segura con \(domain).\n\nDetalles: \(details)",
            actions: [
                .init(
                    title: "Reintentar",
                    style: .default,
                    action: { completion(.retry) }
                ),
                .init(
                    title: "Cancelar",
                    style: .cancel,
                    action: { completion(.cancel) }
                )
            ],
            severity: .error
        )
    }
    
    private func createInvalidChainAlert(
        domain: String,
        details: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        SSLErrorAlert(
            title: "Cadena de Certificado Inválida",
            message: "La cadena de certificados SSL de \(domain) no es válida.\n\nDetalles: \(details)",
            actions: [
                .init(
                    title: "Ver Detalles",
                    style: .default,
                    action: { [weak self] in
                        self?.showCertificateDetails(domain: domain)
                        completion(.showDetails)
                    }
                ),
                .init(
                    title: "Cancelar",
                    style: .cancel,
                    action: { completion(.cancel) }
                )
            ],
            severity: .error
        )
    }
    
    private func createNetworkFailedAlert(
        domain: String,
        details: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        let currentRetries = retryAttempts[domain] ?? 0
        var actions: [SSLErrorAlert.Action] = []
        
        if currentRetries < maxRetryAttempts {
            actions.append(.init(
                title: "Reintentar (\(maxRetryAttempts - currentRetries) intentos restantes)",
                style: .default,
                action: { [weak self] in
                    self?.retryAttempts[domain] = currentRetries + 1
                    completion(.retry)
                }
            ))
        }
        
        actions.append(.init(
            title: "Cancelar",
            style: .cancel,
            action: { completion(.cancel) }
        ))
        
        return SSLErrorAlert(
            title: "Error de Conexión",
            message: "No se pudo conectar con \(domain).\n\nDetalles: \(details)",
            actions: actions,
            severity: .warning
        )
    }
    
    private func createConnectionFailedAlert(
        domain: String,
        details: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        SSLErrorAlert(
            title: "Conexión Fallida",
            message: "No se pudo conectar con el servidor \(domain).\n\nDetalles: \(details)",
            actions: [
                .init(
                    title: "Reintentar",
                    style: .default,
                    action: { completion(.retry) }
                ),
                .init(
                    title: "Cancelar",
                    style: .cancel,
                    action: { completion(.cancel) }
                )
            ],
            severity: .warning
        )
    }
    
    private func createUntrustedRootAlert(
        domain: String,
        details: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        SSLErrorAlert(
            title: "Certificado Raíz No Confiable",
            message: "El certificado raíz de \(domain) no es reconocido como confiable.\n\nDetalles: \(details)",
            actions: [
                .init(
                    title: "Ver Detalles",
                    style: .default,
                    action: { [weak self] in
                        self?.showCertificateDetails(domain: domain)
                        completion(.showDetails)
                    }
                ),
                .init(
                    title: "Cancelar",
                    style: .cancel,
                    action: { completion(.cancel) }
                )
            ],
            severity: .error
        )
    }
    
    private func createCertificateRejectedAlert(
        domain: String,
        details: String,
        completion: @escaping (SSLErrorResolution) -> Void
    ) -> SSLErrorAlert {
        SSLErrorAlert(
            title: "Certificado Rechazado",
            message: "El certificado cliente fue rechazado por el servidor \(domain).\n\nDetalles: \(details)",
            actions: [
                .init(
                    title: "Configurar Certificado",
                    style: .default,
                    action: { completion(.configureCertificate) }
                ),
                .init(
                    title: "Cancelar",
                    style: .cancel,
                    action: { completion(.cancel) }
                )
            ],
            severity: .error
        )
    }
    
    // MARK: - Helper Methods
    
    private func presentAlert(_ alert: SSLErrorAlert) {
        currentAlert = alert
        showingAlert = true
    }
    
    private func recordError(_ error: SSLError, domain: String) {
        let record = SSLErrorRecord(
            error: error,
            domain: domain,
            timestamp: Date(),
            environment: AppConfig.currentEnvironment
        )
        
        errorHistory.append(record)
        
        // Limit history size
        if errorHistory.count > maxErrorHistory {
            errorHistory.removeFirst(errorHistory.count - maxErrorHistory)
        }
        
        // Log error
        AppLogger.shared.error("SSL Error: \(error)", category: .security, metadata: [
            "domain": domain,
            "environment": AppConfig.currentEnvironment.rawValue
        ])
    }
    
    private func showCertificateDetails(domain: String) {
        // This would typically open a detailed view showing certificate information
        // For now, we'll log the details
        AppLogger.shared.info("Showing certificate details for domain: \(domain)", category: .security)
    }
    
    private func requestCertificateUpdate(domain: String) {
        Task {
            do {
                let certificates = try await SSLCertificatePinningManager.loadCertificatesFromAkash(domain: domain)
                for (index, certData) in certificates.enumerated() {
                    let fileName = "akash_cert_\(index).pem"
                    SSLCertificatePinningManager.shared.updateCertificate(certData, for: fileName)
                }
                
                AppLogger.shared.info("SSL certificates updated for domain: \(domain)", category: .security)
            } catch {
                AppLogger.shared.error("Failed to update SSL certificates", category: .security, error: error)
            }
        }
    }
    
    /// Clear error history
    func clearErrorHistory() {
        errorHistory.removeAll()
        retryAttempts.removeAll()
    }
    
    /// Get error statistics
    func getErrorStatistics() -> SSLErrorStatistics {
        let totalErrors = errorHistory.count
        let errorsByType = Dictionary(grouping: errorHistory, by: { $0.error.errorType })
            .mapValues { $0.count }
        let errorsByDomain = Dictionary(grouping: errorHistory, by: { $0.domain })
            .mapValues { $0.count }
        
        let last24Hours = Date().addingTimeInterval(-24 * 60 * 60)
        let recentErrors = errorHistory.filter { $0.timestamp > last24Hours }.count
        
        return SSLErrorStatistics(
            totalErrors: totalErrors,
            errorsByType: errorsByType,
            errorsByDomain: errorsByDomain,
            recentErrors: recentErrors
        )
    }
}

// MARK: - Supporting Types

enum SSLError: Error, Equatable {
    case untrustedCertificate(String)
    case certificateExpired(String)
    case certificateMismatch(expectedHost: String, actualHost: String)
    case sslHandshakeFailed(String)
    case invalidCertificateChain(String)
    case networkConnectionFailed(String)
    case userCancelled
    case connectionFailed(String)
    case untrustedRootCertificate(String)
    case certificateRejected(String)
    
    var errorType: String {
        switch self {
        case .untrustedCertificate:
            return "untrusted_certificate"
        case .certificateExpired:
            return "certificate_expired"
        case .certificateMismatch:
            return "certificate_mismatch"
        case .sslHandshakeFailed:
            return "ssl_handshake_failed"
        case .invalidCertificateChain:
            return "invalid_certificate_chain"
        case .networkConnectionFailed:
            return "network_connection_failed"
        case .userCancelled:
            return "user_cancelled"
        case .connectionFailed:
            return "connection_failed"
        case .untrustedRootCertificate:
            return "untrusted_root_certificate"
        case .certificateRejected:
            return "certificate_rejected"
        }
    }
}

enum SSLErrorResolution {
    case retry
    case allowOnce
    case allowAlways
    case cancel
    case showDetails
    case updateCertificate
    case configureCertificate
}

struct SSLErrorAlert {
    let title: String
    let message: String
    let actions: [Action]
    let severity: Severity
    
    struct Action {
        let title: String
        let style: Style
        let action: () -> Void
        
        enum Style {
            case `default`
            case cancel
            case destructive
        }
    }
    
    enum Severity {
        case info
        case warning
        case error
    }
}

struct SSLErrorRecord: Identifiable {
    let id = UUID()
    let error: SSLError
    let domain: String
    let timestamp: Date
    let environment: AppEnvironment
}

struct SSLErrorStatistics {
    let totalErrors: Int
    let errorsByType: [String: Int]
    let errorsByDomain: [String: Int]
    let recentErrors: Int
}

// MARK: - SwiftUI Integration

extension SSLErrorHandler {
    /// SwiftUI modifier to handle SSL error alerts
    func sslErrorAlert<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        content()
            .alert(
                currentAlert?.title ?? "Error SSL",
                isPresented: $showingAlert,
                presenting: currentAlert
            ) { alert in
                ForEach(0..<alert.actions.count, id: \.self) { index in
                    let action = alert.actions[index]
                    Button(action.title) {
                        action.action()
                        currentAlert = nil
                    }
                }
            } message: { alert in
                Text(alert.message)
            }
    }
}

// MARK: - Error Alert Extensions

extension SSLErrorAlert.Action.Style {
    var buttonRole: ButtonRole? {
        switch self {
        case .default:
            return nil
        case .cancel:
            return .cancel
        case .destructive:
            return .destructive
        }
    }
}