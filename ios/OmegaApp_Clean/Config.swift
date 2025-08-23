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
                return "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"
            case .production:
                return "https://f4o5gi3c0tfmvblt4avi2l6o08.ingress.akash.win"
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

enum LogLevel: String, CaseIterable {
    case debug, info, warning, error
}

struct AppConfig {
    static let shared = AppConfig()
    
    // Current environment detection
    static let currentEnvironment: AppEnvironment = {
        #if DEBUG
        return .development
        #elseif STAGING
        return .staging
        #else
        return .production
        #endif
    }()
    
    // URLs del backend
    struct API {
        static var baseURL: String {
            return currentEnvironment.baseURL
        }
        
        static var isDevelopment: Bool {
            return currentEnvironment.isDebugMode
        }
        
        // Endpoints
        static let login = "/auth/login"
        static let status = "/status"
        static let health = "/health"
        static let predictions = "/api/v1/predictions"
        static let agent = "/agent"
        static let refresh = "/auth/refresh"
        
        // Security
        static let allowInsecureHTTP: Bool = currentEnvironment == .development
        static let certificatePinningEnabled: Bool = currentEnvironment == .production
        
        // Timeouts
        static let requestTimeout: TimeInterval = 30.0
        static let resourceTimeout: TimeInterval = 60.0
    }
    
    // Configuración de autenticación
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
    
    // Configuración de la app
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
    
    // Configuración de notificaciones
    struct Notifications {
        static let bundleID = App.bundleIdentifier
        static let enabled = true
        static let categoriesEnabled = ["prediction_complete", "system_alert", "security_alert"]
    }
    
    // Network configuration
    struct Network {
        static let maxConcurrentOperations = 5
        static let retryAttempts = 3
        static let backoffMultiplier = 2.0
        static let cachePolicy: URLRequest.CachePolicy = .returnCacheDataElseLoad
        static let cacheMemoryCapacity = 50 * 1024 * 1024 // 50MB
        static let cacheDiskCapacity = 100 * 1024 * 1024 // 100MB
    }
    
    // Security configuration
    struct Security {
        static let sessionTimeoutMinutes: Int = 30
        static let maxFailedAttempts = 5
        static let lockoutDurationMinutes = 15
        static let requireBiometricsForSensitiveOperations = true
        
        // SSL Pinning (disabled for Akash Network self-signed certificates)
        static let pinnedCertificates: [String] = []
        static let allowInvalidCertificates = true
    }
    
    // Logging configuration
    struct Logging {
        static let level = currentEnvironment.logLevel
        static let fileLoggingEnabled = currentEnvironment != .production
        static let remoteLoggingEnabled = currentEnvironment.analyticsEnabled
        static let maxLogFileSize = 10 * 1024 * 1024 // 10MB
        static let maxLogFiles = 5
    }
    
    // Debug helpers
    static func printEnvironment() {
        print("🔧 OMEGA App Configuration:")
        print("   Environment: \(currentEnvironment.rawValue)")
        print("   API Base URL: \(API.baseURL)")
        print("   App Version: \(App.version) (\(App.buildNumber))")
        print("   Debug Mode: \(API.isDevelopment)")
        print("   Analytics: \(currentEnvironment.analyticsEnabled)")
        print("   Log Level: \(Logging.level.rawValue)")
    }
    
    // Validation
    static func validateConfiguration() -> Bool {
        guard !API.baseURL.isEmpty else {
            print("❌ Invalid API base URL")
            return false
        }
        
        guard !App.bundleIdentifier.isEmpty else {
            print("❌ Invalid bundle identifier")
            return false
        }
        
        if currentEnvironment == .production {
            guard API.certificatePinningEnabled else {
                print("❌ Certificate pinning must be enabled in production")
                return false
            }
            
            guard Auth.developmentCredentials == nil else {
                print("❌ Development credentials must not be available in production")
                return false
            }
        }
        
        return true
    }
}
