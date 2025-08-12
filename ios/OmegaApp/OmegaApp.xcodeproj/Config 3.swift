import Foundation

struct AppConfig {
    static let shared = AppConfig()
    
    // URLs del backend
    struct API {
        #if DEBUG
        static let baseURL = "http://127.0.0.1:8001"1
        static let isDevelopment = true
        #else
        static let baseURL = "https://omega-pro-ai-production.up.railway.app"  // ¡URL de Railway funcionando!
        static let isDevelopment = false
        #endif
        
        // Endpoints
        static let login = "/auth/login"
        static let status = "/status"
        static let health = "/health"
        static let predictions = "/predictions"
        static let agent = "/agent"
    }
    
    // Configuración de autenticación
    struct Auth {
        static let defaultUsername = "omega_admin"
        static let defaultPassword = "omega_2024"
        static let keychainService = "com.omega.OmegaApp"
    }
    
    // Configuración de la app
    struct App {
        static let version = "1.0.0"
        static let buildNumber = "1"
        static let displayName = "OMEGA PRO AI"
        static let description = "Sistema Agéntico V4.0"
    }
    
    // Configuración de notificaciones (para futuro)
    struct Notifications {
        static let bundleID = "com.tuempresa.OmegaApp"  // Cambiar por tu bundle ID
    }
    
    // Debug helpers
    static func printEnvironment() {
        print("🔧 OMEGA App Configuration:")
        print("   Environment: \(API.isDevelopment ? "Development" : "Production")")
        print("   API Base URL: \(API.baseURL)")
        print("   App Version: \(App.version) (\(App.buildNumber))")
    }
}
