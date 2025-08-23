import Foundation

// MARK: - App Configuration
/// Central configuration management for OMEGA Pro AI iOS app
struct AppConfig {
    
    // MARK: - Environment Detection
    static let currentEnvironment: AppEnvironment = {
        #if DEVELOPMENT
        return .development
        #elseif STAGING
        return .staging
        #else
        return .production
        #endif
    }()
    
    // MARK: - App Information
    struct App {
        static let displayName = Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String ?? "OMEGA PRO AI"
        static let bundleId = Bundle.main.bundleIdentifier ?? "com.omega.OmegaApp"
        static let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0.0"
        static let buildNumber = Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "1"
    }
    
    // MARK: - API Configuration
    struct API {
        static let baseURL: String = {
            switch currentEnvironment {
            case .development:
                return "http://127.0.0.1:8001"
            case .staging:
                return "https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online"
            case .production:
                return "https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online"
            }
        }()
        
        static let allowInsecureHTTP: Bool = {
            switch currentEnvironment {
            case .development:
                return true
            case .staging, .production:
                return false
            }
        }()
        
        // API Endpoints
        static let login = "/auth/token"
        static let refresh = "/auth/refresh"
        static let predict = "/predict"
        static let health = "/health"
        static let history = "/history"
        static let stats = "/stats"
        
        // Request Configuration
        static let requestTimeout: TimeInterval = 30.0
        static let resourceTimeout: TimeInterval = 60.0
        static let maxRetries = 3
    }
    
    // MARK: - Network Configuration
    struct Network {
        static let maxConcurrentOperations: Int = {
            switch currentEnvironment {
            case .development:
                return 4
            case .staging:
                return 6
            case .production:
                return 8
            }
        }()
        
        static let sslPinningEnabled: Bool = {
            switch currentEnvironment {
            case .development:
                return false
            case .staging:
                return true
            case .production:
                return true
            }
        }()
        
        static let allowSelfSignedCertificates: Bool = {
            switch currentEnvironment {
            case .development, .staging:
                return true
            case .production:
                return false
            }
        }()
    }
    
    // MARK: - Security Configuration
    struct Security {
        static let biometricAuthEnabled = true
        static let sessionTimeoutMinutes: Int = {
            switch currentEnvironment {
            case .development:
                return 60 // 1 hour for development
            case .staging:
                return 30 // 30 minutes for staging
            case .production:
                return 15 // 15 minutes for production
            }
        }()
        
        static let maxLoginAttempts = 5
        static let lockoutDurationMinutes = 15
        
        // Keychain Configuration
        static let keychainService = "com.omega.OmegaApp.keychain"
        static let keychainAccessGroup = "PSXDB5A2NN.com.omega.OmegaApp.shared"
    }
    
    // MARK: - Analytics Configuration
    struct Analytics {
        static let enabled: Bool = {
            switch currentEnvironment {
            case .development:
                return false
            case .staging, .production:
                return true
            }
        }()
        
        static let crashReportingEnabled: Bool = {
            switch currentEnvironment {
            case .development:
                return false
            case .staging, .production:
                return true
            }
        }()
    }
    
    // MARK: - Logging Configuration
    struct Logging {
        static let level: LogLevel = {
            switch currentEnvironment {
            case .development:
                return .debug
            case .staging:
                return .info
            case .production:
                return .error
            }
        }()
        
        static let enableConsoleLogging: Bool = {
            switch currentEnvironment {
            case .development, .staging:
                return true
            case .production:
                return false
            }
        }()
    }
    
    // MARK: - Feature Flags
    struct FeatureFlags {
        static let debugMenuEnabled: Bool = {
            switch currentEnvironment {
            case .development, .staging:
                return true
            case .production:
                return false
            }
        }()
        
        static let betaFeaturesEnabled: Bool = {
            switch currentEnvironment {
            case .development:
                return true
            case .staging:
                return true
            case .production:
                return false
            }
        }()
        
        static let performanceMonitoringEnabled = true
        static let advancedPredictionsEnabled = true
        static let realTimeUpdatesEnabled = true
    }
}

// MARK: - App Environment
enum AppEnvironment: String, CaseIterable {
    case development = "development"
    case staging = "staging"
    case production = "production"
    
    var displayName: String {
        switch self {
        case .development:
            return "Development"
        case .staging:
            return "Staging"
        case .production:
            return "Production"
        }
    }
    
    var isDebugMode: Bool {
        switch self {
        case .development, .staging:
            return true
        case .production:
            return false
        }
    }
    
    var requiresSSL: Bool {
        switch self {
        case .development:
            return false
        case .staging, .production:
            return true
        }
    }
}

// MARK: - Additional Configuration Extensions
extension AppConfig {
    
    // Enhanced Auth configuration
    struct Auth {
        static let keychainService = "com.omega.OmegaApp.secure"
        static let tokenKey = "auth_token"
        static let refreshTokenKey = "refresh_token"
        static let userDataKey = "user_data"
        
        // Token configuration
        static let tokenExpirationBuffer: TimeInterval = 300 // 5 minutes buffer
        static let maxRetryAttempts = 3
        
        // Development credentials (only for development builds)
        static var developmentCredentials: (username: String, password: String)? {
            #if DEBUG
            return ("omega_admin", "omega_2024")
            #else
            return nil
            #endif
        }
        
        // Biometric authentication
        static let biometricAuthEnabled = true
        static let biometricFallbackEnabled = true
    }
    
    // Enhanced App configuration
    struct App {
        static let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
        static let buildNumber = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
        static let displayName = "OMEGA PRO AI"
        static let description = "Sistema Agéntico V4.0"
        static let bundleIdentifier = Bundle.main.bundleIdentifier ?? "com.omega.OmegaApp"
        
        // Feature flags
        static let debugMenuEnabled = currentEnvironment.isDebugMode
        static let crashReportingEnabled = currentEnvironment.analyticsEnabled
        static let performanceMonitoringEnabled = true
    }
    
    // Enhanced Logging configuration
    struct Logging {
        static let level = currentEnvironment.logLevel
        static let fileLoggingEnabled = currentEnvironment != .production
        static let remoteLoggingEnabled = currentEnvironment.analyticsEnabled
        static let maxLogFileSize = 10 * 1024 * 1024 // 10MB
        static let maxLogFiles = 5
    }
}

// MARK: - AppEnvironment Extension
extension AppEnvironment {
    var baseURL: String {
        switch self {
        case .development:
            return "http://127.0.0.1:8001"
        case .staging:
            return "https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online"
        case .production:
            return "https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online"
        }
    }
    
    var logLevel: LogLevel {
        switch self {
        case .development:
            return .debug
        case .staging:
            return .info
        case .production:
            return .error
        }
    }
    
    var analyticsEnabled: Bool {
        switch self {
        case .development:
            return false
        case .staging, .production:
            return true
        }
}
