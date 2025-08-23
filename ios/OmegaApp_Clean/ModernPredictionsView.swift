import SwiftUI

struct ModernPredictionsView: View {
    @StateObject private var apiClient = OmegaAPIClient()
    @State private var isGenerating = false
    @State private var selectedProfile = "moderado"
    @State private var predictionCount = 10
    @State private var showingErrorAlert = false
    @State private var errorMessage = ""
    @State private var showingSettings = false
    
    let profiles = ["conservador", "moderado", "agresivo", "balanceado"]
    let countOptions = [5, 10, 15, 20]
    
    var body: some View {
        NavigationView {
            ZStack {
                // Background gradient
                LinearGradient(
                    gradient: Gradient(colors: [.blue.opacity(0.1), .purple.opacity(0.1)]),
                    startPoint: .topTrailing,
                    endPoint: .bottomLeading
                )
                .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Header Card
                        headerCard
                        
                        // Quick Controls
                        controlsCard
                        
                        // Generate Button
                        generateButton
                        
                        // Status Card
                        if isGenerating {
                            loadingCard
                        }
                        
                        // Predictions List
                        if !apiClient.predictions.isEmpty {
                            predictionsCard
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("OMEGA Pro AI")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingSettings = true
                    } label: {
                        Image(systemName: "gearshape.fill")
                            .foregroundColor(.blue)
                    }
                }
            }
            .sheet(isPresented: $showingSettings) {
                SettingsSheetView(
                    selectedProfile: $selectedProfile,
                    predictionCount: $predictionCount,
                    profiles: profiles,
                    countOptions: countOptions
                )
            }
            .alert("Error", isPresented: $showingErrorAlert) {
                Button("OK") { }
            } message: {
                Text(errorMessage)
            }
            .onAppear {
                apiClient.configure()
                checkSystemHealth()
            }
        }
    }
    
    // MARK: - View Components
    
    private var headerCard: some View {
        VStack(spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("🚀 Sistema Operacional")
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    Text("Conectado a Akash Network")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Connection status indicator
                Circle()
                    .fill(.green)
                    .frame(width: 12, height: 12)
                    .overlay(
                        Circle()
                            .stroke(.green, lineWidth: 2)
                            .scaleEffect(1.5)
                            .opacity(0.3)
                            .animation(.easeInOut(duration: 1).repeatForever(autoreverses: false), value: true)
                    )
            }
            
            Text("Sistema de predicción avanzada basado en análisis estadístico con ensemble de modelos ML")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
    
    private var controlsCard: some View {
        VStack(spacing: 16) {
            HStack {
                VStack(alignment: .leading) {
                    Text("Perfil de Riesgo")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Picker("Perfil", selection: $selectedProfile) {
                        ForEach(profiles, id: \.self) { profile in
                            Text(profile.capitalized)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }
            }
            
            HStack {
                VStack(alignment: .leading) {
                    Text("Cantidad: \(predictionCount)")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Slider(
                        value: Binding(
                            get: { Double(predictionCount) },
                            set: { predictionCount = Int($0) }
                        ),
                        in: 5...20,
                        step: 5
                    )
                    .accentColor(.blue)
                }
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
    
    private var generateButton: some View {
        Button {
            generatePredictions()
        } label: {
            HStack {
                if isGenerating {
                    ProgressView()
                        .scaleEffect(0.8)
                        .foregroundColor(.white)
                } else {
                    Image(systemName: "brain.head.profile")
                        .font(.title2)
                }
                
                Text(isGenerating ? "Generando..." : "Generar Predicciones")
                    .font(.headline)
                    .fontWeight(.semibold)
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                LinearGradient(
                    gradient: Gradient(colors: [.blue, .purple]),
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .scaleEffect(isGenerating ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: isGenerating)
        }
        .disabled(isGenerating)
    }
    
    private var loadingCard: some View {
        VStack(spacing: 12) {
            HStack {
                ProgressView()
                    .scaleEffect(1.2)
                
                VStack(alignment: .leading) {
                    Text("Generando predicciones...")
                        .font(.headline)
                    
                    Text("Analizando datos históricos con IA")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
    
    private var predictionsCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("🎯 Predicciones Generadas")
                    .font(.headline)
                    .fontWeight(.bold)
                
                Spacer()
                
                Text("\(apiClient.predictions.count) resultados")
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(.blue.opacity(0.2))
                    .clipShape(Capsule())
            }
            
            LazyVStack(spacing: 12) {
                ForEach(Array(apiClient.predictions.enumerated()), id: \.element.id) { index, prediction in
                    PredictionRowView(prediction: prediction, index: index + 1)
                }
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
    
    // MARK: - Actions
    
    private func generatePredictions() {
        isGenerating = true
        
        Task {
            do {
                let _ = try await apiClient.generatePredictions(
                    count: predictionCount,
                    perfilSVI: selectedProfile
                )
                
                await MainActor.run {
                    isGenerating = false
                    
                    // Haptic feedback
                    let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
                    impactFeedback.impactOccurred()
                }
            } catch {
                await MainActor.run {
                    isGenerating = false
                    errorMessage = error.localizedDescription
                    showingErrorAlert = true
                    
                    // Error haptic
                    let notificationFeedback = UINotificationFeedbackGenerator()
                    notificationFeedback.notificationOccurred(.error)
                }
            }
        }
    }
    
    private func checkSystemHealth() {
        Task {
            do {
                let _ = try await apiClient.checkHealth()
                print("✅ OMEGA system is healthy")
            } catch {
                print("⚠️ OMEGA system health check failed: \(error)")
            }
        }
    }
}

// MARK: - Prediction Row View

struct PredictionRowView: View {
    let prediction: OmegaPrediction
    let index: Int
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                // Index number
                Text("\(index)")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .frame(width: 24, height: 24)
                    .background(prediction.qualityRating.color)
                    .clipShape(Circle())
                
                Spacer()
                
                // Quality rating
                HStack(spacing: 4) {
                    Image(systemName: prediction.qualityRating.icon)
                        .foregroundColor(prediction.qualityRating.color)
                        .font(.caption)
                    
                    Text(prediction.qualityRating.rawValue)
                        .font(.caption2)
                        .fontWeight(.medium)
                        .foregroundColor(prediction.qualityRating.color)
                }
            }
            
            // Numbers
            HStack {
                ForEach(prediction.numbers, id: \.self) { number in
                    Text("\(number)")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.primary)
                        .frame(width: 40, height: 40)
                        .background(.blue.opacity(0.1))
                        .clipShape(Circle())
                }
            }
            
            // Scores
            HStack(spacing: 16) {
                ScoreView(title: "Confianza", score: prediction.confidencePercentage, color: .blue)
                ScoreView(title: "SVI", score: prediction.sviPercentage, color: .green)
                
                Spacer()
                
                Text(prediction.source.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(.quaternary, lineWidth: 1)
        )
    }
}

struct ScoreView: View {
    let title: String
    let score: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
            
            Text(score)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
    }
}

// MARK: - Settings Sheet

struct SettingsSheetView: View {
    @Binding var selectedProfile: String
    @Binding var predictionCount: Int
    let profiles: [String]
    let countOptions: [Int]
    
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Configuración de Predicciones")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    // Profile selection
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Perfil de Análisis")
                            .font(.headline)
                        
                        ForEach(profiles, id: \.self) { profile in
                            Button {
                                selectedProfile = profile
                            } label: {
                                HStack {
                                    Text(profile.capitalized)
                                        .foregroundColor(.primary)
                                    
                                    Spacer()
                                    
                                    if selectedProfile == profile {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(.blue)
                                    } else {
                                        Image(systemName: "circle")
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .padding()
                                .background(.regularMaterial)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                        }
                    }
                    
                    // Count selection
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Cantidad de Predicciones")
                            .font(.headline)
                        
                        HStack {
                            ForEach(countOptions, id: \.self) { count in
                                Button {
                                    predictionCount = count
                                } label: {
                                    Text("\(count)")
                                        .foregroundColor(predictionCount == count ? .white : .primary)
                                        .fontWeight(.semibold)
                                        .frame(width: 50, height: 40)
                                        .background(predictionCount == count ? .blue : .regularMaterial)
                                        .clipShape(RoundedRectangle(cornerRadius: 8))
                                }
                            }
                            
                            Spacer()
                        }
                    }
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Configuración")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Hecho") {
                        dismiss()
                    }
                }
            }
        }
    }
}

// MARK: - Preview

struct ModernPredictionsView_Previews: PreviewProvider {
    static var previews: some View {
        ModernPredictionsView()
    }
}