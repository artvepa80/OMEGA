import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var apiClient: OmegaAPIClient
    
    @State private var username = ""
    @State private var password = ""
    @State private var showingAlert = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                // Logo/Title
                VStack(spacing: 8) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 60))
                        .foregroundColor(.blue)
                    
                    Text("OMEGA PRO AI")
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text("Sistema Agéntico V4.0")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .padding(.top, 40)
                
                // Login Form
                VStack(spacing: 16) {
                    TextField("Usuario", text: $username)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .autocapitalization(.none)
                        .autocorrectionDisabled()
                    
                    SecureField("Contraseña", text: $password)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                }
                .padding(.horizontal)
                
                // Login Button
                Button(action: login) {
                    HStack {
                        if authManager.isLoading {
                            ProgressView()
                                .scaleEffect(0.8)
                                .foregroundColor(.white)
                        } else {
                            Text("Iniciar Sesión")
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(8)
                }
                .disabled(authManager.isLoading || username.isEmpty || password.isEmpty)
                .padding(.horizontal)
                
                // Biometric Login (if available)
                if authManager.biometricAuthAvailable {
                    Button(action: biometricLogin) {
                        HStack {
                            Image(systemName: getBiometricIcon())
                            Text("Usar \(authManager.getBiometricTypeString())")
                        }
                        .foregroundColor(.blue)
                    }
                }
                
                Spacer()
                
                // Environment indicator
                Text("Ambiente: \(AppConfig.currentEnvironment.displayName)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.bottom)
            }
            .navigationBarHidden(true)
        }
        .alert("Error de Autenticación", isPresented: $showingAlert) {
            Button("OK") { }
        } message: {
            if let error = authManager.error {
                Text(error.localizedDescription)
            }
        }
        .onChange(of: authManager.error) { error in
            showingAlert = error != nil
        }
    }
    
    private func login() {
        Task {
            await authManager.login(username: username, password: password)
        }
    }
    
    private func biometricLogin() {
        Task {
            _ = await authManager.authenticateWithBiometrics()
        }
    }
    
    private func getBiometricIcon() -> String {
        switch authManager.getBiometricTypeString() {
        case "Face ID":
            return "faceid"
        case "Touch ID":
            return "touchid"
        default:
            return "lock"
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthManager.shared)
        .environmentObject(OmegaAPIClient())
}