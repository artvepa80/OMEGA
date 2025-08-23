import SwiftUI

struct PredictionsView: View {
    @EnvironmentObject var apiClient: OmegaAPIClient
    @State private var predictions: [Prediction] = []
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            VStack {
                if isLoading {
                    ProgressView("Cargando predicciones...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if predictions.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "brain.head.profile")
                            .font(.system(size: 60))
                            .foregroundColor(.secondary)
                        
                        Text("No hay predicciones disponibles")
                            .font(.headline)
                        
                        Text("Las predicciones aparecerán aquí una vez que el sistema las genere")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                        
                        Button("Actualizar") {
                            Task {
                                await loadPredictions()
                            }
                        }
                        .buttonStyle(.borderedProminent)
                    }
                    .padding()
                } else {
                    List(predictions) { prediction in
                        PredictionRowView(prediction: prediction)
                    }
                }
            }
            .navigationTitle("Predicciones")
            .refreshable {
                await loadPredictions()
            }
        }
        .task {
            await loadPredictions()
        }
    }
    
    private func loadPredictions() async {
        isLoading = true
        do {
            predictions = try await apiClient.getPredictions(limit: 50)
        } catch {
            print("Error loading predictions: \(error)")
        }
        isLoading = false
    }
}

struct PredictionRowView: View {
    let prediction: Prediction
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Predicción #\(prediction.id.prefix(8))")
                    .font(.headline)
                
                Spacer()
                
                Text("\(Int(prediction.confidence * 100))%")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(confidence > 0.8 ? .green : prediction.confidence > 0.6 ? .orange : .red)
            }
            
            HStack {
                ForEach(prediction.numbers, id: \.self) { number in
                    Text("\(number)")
                        .font(.title2)
                        .fontWeight(.bold)
                        .frame(width: 40, height: 40)
                        .background(Circle().fill(Color.blue.opacity(0.2)))
                        .foregroundColor(.blue)
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
        .padding(.vertical, 4)
    }
    
    private var confidence: Double {
        return prediction.confidence
    }
}

#Preview {
    PredictionsView()
        .environmentObject(OmegaAPIClient())
}