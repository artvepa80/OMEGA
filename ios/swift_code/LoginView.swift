import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @EnvironmentObject var apiClient: OmegaAPIClient
    
    @State private var username = ""
    @State private var password = ""
    @State private var showingBiometrics = false
    @State private var showingError = false
    
    var body: some View {
        NavigationView {
            GeometryReader { geometry in
                ScrollView {
                    VStack(spacing: 32) {
                        Spacer()
                        
                        // Logo y título
                        VStack(spacing: 20) {
                            // Logo de Omega
                            ZStack {
                                Circle()
                                    .fill(
                                        LinearGradient(
                                            gradient: Gradient(colors: [.blue, .purple]),
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                    .frame(width: 100, height: 100)
                                
                                Image(systemName: "brain.head.profile")
                                    .font(.system(size: 50))
                                    .foregroundColor(.white)
                            }
                            
                            VStack(spacing: 8) {
                                Text("OMEGA PRO AI")
                                    .font(.largeTitle)
                                    .fontWeight(.bold)
                                    .foregroundColor(.primary)
                                
                                Text("Sistema Agéntico V4.0")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                        }
                        
                        // Formulario de login
                        VStack(spacing: 20) {
                            // Campo de usuario
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Usuario")
                                    .font(.caption)
                                    .fontWeight(.medium)
                                    .foregroundColor(.secondary)
                                
                                TextField("Introduce tu usuario", text: $username)
                                    .textFieldStyle(OmegaTextFieldStyle())
                                    .textContentType(.username)
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)
                            }
                            
                            // Campo de contraseña
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Contraseña")
                                    .font(.caption)
                                    .fontWeight(.medium)
                                    .foregroundColor(.secondary)
                                
                                SecureField("Introduce tu contraseña", text: $password)
                                    .textFieldStyle(OmegaTextFieldStyle())
                                    .textContentType(.password)
                            }
                        }
                        
                        // Botones de acción
                        VStack(spacing: 16) {
                            // Botón de login
                            Button(action: {
                                Task {
                                    await authManager.login(username: username, password: password)
                                }
                            }) {
                                HStack {
                                    if authManager.isLoading {
                                        ProgressView()
                                            .scaleEffect(0.8)
                                            .foregroundColor(.white)
                                    } else {
                                        Image(systemName: "arrow.right.circle.fill")
                                        Text("Iniciar Sesión")
                                    }
                                }
                                .frame(maxWidth: .infinity)
                                .frame(height: 50)
                                .background(
                                    LinearGradient(
                                        gradient: Gradient(colors: [.blue, .purple]),
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .foregroundColor(.white)
                                .cornerRadius(12)
                                .disabled(authManager.isLoading || username.isEmpty || password.isEmpty)
                            }
                            
                            // Divider
                            HStack {
                                Rectangle()
                                    .frame(height: 1)
                                    .foregroundColor(.gray.opacity(0.3))
                                
                                Text("o")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .padding(.horizontal, 12)
                                
                                Rectangle()
                                    .frame(height: 1)
                                    .foregroundColor(.gray.opacity(0.3))
                            }
                            
                            // Botón de Face ID/Touch ID
                            Button(action: {
                                Task {
                                    let success = await authManager.authenticateWithBiometrics()
                                    if !success {
                                        showingError = true
                                    }
                                }
                            }) {
                                HStack {
                                    Image(systemName: "faceid")
                                    Text("Face ID / Touch ID")
                                }
                                .frame(maxWidth: .infinity)
                                .frame(height: 50)
                                .background(Color(.systemGray6))
                                .foregroundColor(.primary)
                                .cornerRadius(12)
                            }
                        }
                        
                        Spacer()
                        
                        // Información adicional
                        VStack(spacing: 12) {
                            Text("Credenciales por defecto:")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            
                            VStack(spacing: 4) {
                                Text("Usuario: omega_admin")
                                    .font(.caption)
                                    .fontWeight(.medium)
                                
                                Text("Contraseña: omega_2024")
                                    .font(.caption)
                                    .fontWeight(.medium)
                            }
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(8)
                        }
                    }
                    .padding(.horizontal, 32)
                    .frame(minHeight: geometry.size.height)
                }
            }
        }
        .navigationBarHidden(true)
        .alert("Error de Autenticación", isPresented: $showingError) {
            Button("OK") {
                showingError = false
                authManager.error = nil
            }
        } message: {
            Text(authManager.error?.localizedDescription ?? "Error desconocido")
        }
        .onChange(of: authManager.error) { error in
            if error != nil {
                showingError = true
            }
        }
        .onAppear {
            // Autocompletar credenciales de desarrollo
            if username.isEmpty && password.isEmpty {
                username = "omega_admin"
                password = "omega_2024"
            }
        }
    }
}

// MARK: - Custom Text Field Style

struct OmegaTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(.systemGray6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color(.systemGray4), lineWidth: 1)
                    )
            )
    }
}

// MARK: - Preview Views

struct PredictionsView: View {
    @EnvironmentObject var apiClient: OmegaAPIClient
    @State private var predictions: [Prediction] = []
    @State private var isLoading = false
    @State private var showingNewPrediction = false
    
    var body: some View {
        NavigationView {
            VStack {
                if isLoading {
                    ProgressView("Cargando predicciones...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if predictions.isEmpty {
                    EmptyPredictionsView {
                        showingNewPrediction = true
                    }
                } else {
                    PredictionsList(predictions: predictions)
                }
            }
            .navigationTitle("Predicciones")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingNewPrediction = true
                    }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingNewPrediction) {
                NewPredictionView()
            }
            .task {
                await loadPredictions()
            }
            .refreshable {
                await loadPredictions()
            }
        }
    }
    
    private func loadPredictions() async {
        isLoading = true
        do {
            predictions = try await apiClient.getPredictions()
        } catch {
            print("Error loading predictions: \(error)")
        }
        isLoading = false
    }
}

struct EmptyPredictionsView: View {
    let onCreateNew: () -> Void
    
    var body: some View {
        VStack(spacing: 24) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 60))
                .foregroundColor(.gray)
            
            VStack(spacing: 8) {
                Text("No hay predicciones")
                    .font(.title2)
                    .fontWeight(.semibold)
                
                Text("Crea tu primera predicción con IA")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            Button(action: onCreateNew) {
                HStack {
                    Image(systemName: "plus.circle.fill")
                    Text("Nueva Predicción")
                }
                .frame(maxWidth: .infinity)
                .frame(height: 50)
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(12)
            }
            .padding(.horizontal)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct PredictionsList: View {
    let predictions: [Prediction]
    
    var body: some View {
        List(predictions) { prediction in
            PredictionCard(prediction: prediction)
                .listRowSeparator(.hidden)
                .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
        }
        .listStyle(PlainListStyle())
    }
}

struct PredictionCard: View {
    let prediction: Prediction
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Predicción \(prediction.id.prefix(8))")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Spacer()
                
                Text("\(Int(prediction.confidence * 100))%")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(confidenceColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(confidenceColor.opacity(0.2))
                    .cornerRadius(6)
            }
            
            // Números predichos
            HStack {
                ForEach(prediction.numbers, id: \.self) { number in
                    Text("\(number)")
                        .font(.title3)
                        .fontWeight(.bold)
                        .frame(width: 40, height: 40)
                        .background(Color.blue.opacity(0.1))
                        .foregroundColor(.blue)
                        .cornerRadius(8)
                }
            }
            
            HStack {
                Text("Modelo: \(prediction.modelUsed)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(prediction.timestamp.formatted(date: .abbreviated, time: .shortened))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
        )
    }
    
    private var confidenceColor: Color {
        if prediction.confidence >= 0.8 {
            return .green
        } else if prediction.confidence >= 0.6 {
            return .orange
        } else {
            return .red
        }
    }
}

struct ResultsView: View {
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    Text("Resultados y Análisis")
                        .font(.title)
                        .fontWeight(.bold)
                        .padding()
                    
                    // Aquí irán las gráficas y estadísticas
                    Text("Próximamente: Gráficas de rendimiento")
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Resultados")
        }
    }
}

struct SettingsView: View {
    @EnvironmentObject var authManager: AuthManager
    
    var body: some View {
        NavigationView {
            List {
                Section("Usuario") {
                    HStack {
                        Image(systemName: "person.circle.fill")
                            .font(.title2)
                            .foregroundColor(.blue)
                        
                        VStack(alignment: .leading) {
                            Text(authManager.user?.username ?? "Usuario")
                                .font(.headline)
                            
                            Text(authManager.user?.role.capitalized ?? "Rol")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.vertical, 8)
                }
                
                Section("Configuración") {
                    NavigationLink(destination: EmptyView()) {
                        Label("Notificaciones", systemImage: "bell")
                    }
                    
                    NavigationLink(destination: EmptyView()) {
                        Label("Preferencias API", systemImage: "gear")
                    }
                    
                    NavigationLink(destination: EmptyView()) {
                        Label("Privacidad", systemImage: "lock")
                    }
                }
                
                Section("Soporte") {
                    NavigationLink(destination: EmptyView()) {
                        Label("Ayuda", systemImage: "questionmark.circle")
                    }
                    
                    NavigationLink(destination: EmptyView()) {
                        Label("Acerca de", systemImage: "info.circle")
                    }
                }
                
                Section {
                    Button(action: {
                        authManager.logout()
                    }) {
                        Label("Cerrar Sesión", systemImage: "arrow.right.square")
                            .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Configuración")
        }
    }
}

struct NewPredictionView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject var apiClient: OmegaAPIClient
    
    @State private var selectedModel = "neural_enhanced"
    @State private var isCreating = false
    
    let models = [
        ("neural_enhanced", "Neural Enhanced"),
        ("transformer", "Transformer"),
        ("genetic", "Genético"),
        ("lstm", "LSTM"),
        ("monte_carlo", "Monte Carlo")
    ]
    
    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Selecciona el modelo")
                        .font(.headline)
                    
                    Picker("Modelo", selection: $selectedModel) {
                        ForEach(models, id: \.0) { model in
                            Text(model.1).tag(model.0)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
                
                Button(action: createPrediction) {
                    HStack {
                        if isCreating {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "brain.head.profile")
                            Text("Crear Predicción")
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                    .disabled(isCreating)
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Nueva Predicción")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancelar") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    private func createPrediction() {
        isCreating = true
        
        Task {
            do {
                let parameters = PredictionParameters(
                    modelType: selectedModel,
                    customParams: nil
                )
                
                let _ = try await apiClient.createPrediction(parameters: parameters)
                
                await MainActor.run {
                    dismiss()
                }
            } catch {
                print("Error creating prediction: \(error)")
            }
            
            isCreating = false
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthManager())
        .environmentObject(OmegaAPIClient())
}
