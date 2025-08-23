import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var showingLogoutAlert = false
    
    var body: some View {
        NavigationView {
            List {
                Section {
                    if let user = authManager.user {
                        HStack {
                            Image(systemName: "person.circle.fill")
                                .font(.title)
                                .foregroundColor(.blue)
                            
                            VStack(alignment: .leading) {
                                Text(user.username)
                                    .font(.headline)
                                
                                Text("Rol: \(user.role.capitalized)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                } header: {
                    Text("Usuario")
                }
                
                Section {
                    HStack {
                        Image(systemName: "server.rack")
                        Text("Ambiente")
                        Spacer()
                        Text(AppConfig.currentEnvironment.displayName)
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Image(systemName: "network")
                        Text("API Base URL")
                        Spacer()
                        Text(AppConfig.API.baseURL)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Image(systemName: "info.circle")
                        Text("Versión")
                        Spacer()
                        Text("\(AppConfig.App.version) (\(AppConfig.App.buildNumber))")
                            .foregroundColor(.secondary)
                    }
                } header: {
                    Text("Información de la App")
                }
                
                Section {
                    HStack {
                        Image(systemName: authManager.biometricAuthAvailable ? "faceid" : "lock")
                        Text("Autenticación biométrica")
                        Spacer()
                        Text(authManager.biometricAuthAvailable ? "Disponible" : "No disponible")
                            .foregroundColor(authManager.biometricAuthAvailable ? .green : .secondary)
                    }
                } header: {
                    Text("Seguridad")
                }
                
                Section {
                    Button(action: {
                        showingLogoutAlert = true
                    }) {
                        HStack {
                            Image(systemName: "rectangle.portrait.and.arrow.right")
                                .foregroundColor(.red)
                            Text("Cerrar Sesión")
                                .foregroundColor(.red)
                        }
                    }
                }
            }
            .navigationTitle("Configuración")
        }
        .alert("Cerrar Sesión", isPresented: $showingLogoutAlert) {
            Button("Cancelar", role: .cancel) { }
            Button("Cerrar Sesión", role: .destructive) {
                Task {
                    await authManager.logout()
                }
            }
        } message: {
            Text("¿Estás seguro de que quieres cerrar sesión?")
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(AuthManager.shared)
}