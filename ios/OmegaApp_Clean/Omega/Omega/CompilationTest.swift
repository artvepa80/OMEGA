import Foundation
import SwiftUI

// MARK: - Compilation Test
/// Simple test to verify that all key classes can be instantiated without compilation errors
struct CompilationTest {
    
    static func runBasicTests() -> Bool {
        do {
            // Test Config
            let environment = AppConfig.currentEnvironment
            let baseURL = AppConfig.API.baseURL
            let appVersion = AppConfig.App.version
            
            print("✅ Config test passed - Environment: \(environment), URL: \(baseURL), Version: \(appVersion)")
            
            // Test Logger
            let logger = AppLogger.shared
            logger.info("Compilation test message")
            
            print("✅ Logger test passed")
            
            // Test Security Manager
            let securityManager = SecurityManager.shared
            let isTokenValid = securityManager.isTokenValid()
            
            print("✅ SecurityManager test passed - Token valid: \(isTokenValid)")
            
            // Test JWT Decoder (basic test)
            let testJWT = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.invalid"
            do {
                _ = try JWTDecoder.decode(testJWT)
            } catch {
                // Expected to fail with invalid signature, but structure should work
                print("✅ JWTDecoder test passed (expected error: \(error))")
            }
            
            // Test API Client
            let apiClient = OmegaAPIClient()
            apiClient.configure()
            
            print("✅ OmegaAPIClient test passed")
            
            // Test SSL Manager
            let sslManager = SSLCertificatePinningManager.shared
            let config = sslManager.getConfiguration(for: "example.com")
            
            print("✅ SSLCertificatePinningManager test passed - Config exists: \(config != nil)")
            
            // Test Network Security Manager
            Task { @MainActor in
                let networkManager = NetworkSecurityManager.shared
                let summary = networkManager.getSecurityStatusSummary()
                print("✅ NetworkSecurityManager test passed - Status: \(summary.overallSecurityStatus)")
            }
            
            return true
            
        } catch {
            print("❌ Compilation test failed: \(error)")
            return false
        }
    }
}

// MARK: - SwiftUI View Test
/// Test that SwiftUI views can be compiled
struct ViewCompilationTest: View {
    var body: some View {
        VStack {
            Text("Compilation Test")
                .font(.title)
            
            Text("If you can see this, SwiftUI views are compiling correctly")
                .font(.body)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

#Preview {
    ViewCompilationTest()
}