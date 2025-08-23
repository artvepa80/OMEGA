// DEMO: Así se vería la app iOS con OMEGA integrado
// Este archivo muestra cómo la app iOS se conecta a tu sistema OMEGA real

import SwiftUI
import Foundation

// MARK: - Vista Principal con OMEGA Real
struct OmegaPredictionsView: View {
    @StateObject private var viewModel = OmegaPredictionsViewModel()
    @State private var showingFilters = false
    @State private var selectedLotteryType = "kabala"
    @State private var seriesCount = 5
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    
                    // Header con disclaimer
                    DisclaimerCard()
                    
                    // Controles de predicción
                    PredictionControlsCard(
                        selectedLotteryType: $selectedLotteryType,
                        seriesCount: $seriesCount,
                        onGenerate: {
                            Task {
                                await viewModel.generatePredictions(
                                    lotteryType: selectedLotteryType,
                                    seriesCount: seriesCount
                                )
                            }
                        }
                    )
                    
                    // Resultados de OMEGA
                    if viewModel.isLoading {
                        LoadingCard()
                    } else if let result = viewModel.currentResult {
                        OmegaResultsCard(result: result)
                    }
                    
                    // Análisis estadístico
                    if let analysis = viewModel.currentResult?.analysis {
                        StatisticalAnalysisCard(analysis: analysis)
                    }
                    
                    // Recomendaciones
                    if let recommendations = viewModel.currentResult?.recommendations {
                        RecommendationsCard(recommendations: recommendations)
                    }
                }
                .padding()
            }
            .navigationTitle("OMEGA Statistical Analysis")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Filtros") {
                        showingFilters = true
                    }
                }
            }
            .sheet(isPresented: $showingFilters) {
                FiltersView()
            }
        }
    }
}

// MARK: - Disclaimer Card
struct DisclaimerCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "info.circle.fill")
                    .foregroundColor(.blue)
                Text("OMEGA AI Statistical Analysis")
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
            }
            
            Text("⚠️ Este sistema realiza análisis estadístico basado en datos históricos. Presenta patrones matemáticos y probabilidades, NO recomendaciones.")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.leading)
            
            Text("• Los resultados son análisis de datos, no consejos")
                .font(.caption2)
                .foregroundColor(.secondary)
            
            Text("• Los sorteos son eventos aleatorios e independientes")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBlue).opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color(.systemBlue).opacity(0.3), lineWidth: 1)
                )
        )
    }
}

// MARK: - Controls Card
struct PredictionControlsCard: View {
    @Binding var selectedLotteryType: String
    @Binding var seriesCount: Int
    let onGenerate: () -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            HStack {
                Text("Configuración de Análisis")
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
            }
            
            VStack(spacing: 12) {
                // Selector de lotería
                Picker("Tipo de Lotería", selection: $selectedLotteryType) {
                    Text("Kabala").tag("kabala")
                    Text("Powerball").tag("powerball")
                    Text("Mega Millions").tag("mega_millions")
                }
                .pickerStyle(.segmented)
                
                // Cantidad de series
                HStack {
                    Text("Series a generar:")
                    Spacer()
                    Stepper("\(seriesCount)", value: $seriesCount, in: 1...10)
                }
                
                // Botón generar
                Button(action: onGenerate) {
                    HStack {
                        Image(systemName: "brain.head.profile")
                        Text("Generar Análisis OMEGA")
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color(.systemBlue))
                    )
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 4)
        )
    }
}

// MARK: - OMEGA Results Card (Datos Reales)
struct OmegaResultsCard: View {
    let result: OmegaPredictionResult
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .foregroundColor(.green)
                Text("Análisis Estadístico OMEGA")
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
                
                Text("Generado: \(result.timestamp.formatted(date: .omitted, time: .shortened))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            // Series generadas por OMEGA
            ForEach(Array(result.series.enumerated()), id: \.offset) { index, series in
                OmegaSeriesRow(
                    seriesNumber: index + 1,
                    series: series
                )
            }
            
            // Resumen estadístico
            if let analysis = result.analysis {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Resumen del Análisis:")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    HStack {
                        MetricBadge(
                            title: "Confianza Promedio",
                            value: String(format: "%.1f%%", analysis.avgConfidence * 100),
                            color: .green
                        )
                        
                        MetricBadge(
                            title: "Consistencia de Patrones",
                            value: String(format: "%.1f%%", analysis.patternConsistency * 100),
                            color: .blue
                        )
                    }
                }
                .padding(.top, 8)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 4)
        )
    }
}

// MARK: - Serie Row (Cada predicción de OMEGA)
struct OmegaSeriesRow: View {
    let seriesNumber: Int
    let series: OmegaSeries
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Serie #\(seriesNumber)")
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Spacer()
                
                // Badge del modelo OMEGA que lo generó
                Text(series.source.uppercased())
                    .font(.caption2)
                    .fontWeight(.medium)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(
                        Capsule()
                            .fill(sourceColor(for: series.source).opacity(0.2))
                    )
                    .foregroundColor(sourceColor(for: series.source))
            }
            
            // Los números generados por OMEGA
            HStack(spacing: 8) {
                ForEach(series.numbers, id: \.self) { number in
                    NumberBall(number: number)
                }
                
                Spacer()
                
                // Confianza de OMEGA
                VStack(alignment: .trailing) {
                    Text("\(Int(series.confidence * 100))%")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(confidenceColor(series.confidence))
                    
                    Text("confianza")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            
            // Scores adicionales de OMEGA
            HStack {
                ScorePill(title: "SVI", score: series.sviScore, color: .purple)
                ScorePill(title: "Patrón", score: series.patternScore, color: .orange)
                ScorePill(title: "Frecuencia", score: series.frequencyScore, color: .blue)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(.systemGray6))
        )
    }
    
    private func sourceColor(for source: String) -> Color {
        switch source.lowercased() {
        case "omega_consensus": return .green
        case "omega_lstm_v2": return .blue
        case "omega_transformer_deep": return .purple
        case "omega_montecarlo": return .orange
        case "omega_apriori": return .red
        case "omega_genetic": return .pink
        default: return .gray
        }
    }
    
    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 { return .green }
        if confidence >= 0.6 { return .orange }
        return .red
    }
}

// MARK: - Number Ball
struct NumberBall: View {
    let number: Int
    
    var body: some View {
        Text("\(number)")
            .font(.system(size: 14, weight: .bold, design: .rounded))
            .frame(width: 28, height: 28)
            .background(
                Circle()
                    .fill(
                        LinearGradient(
                            gradient: Gradient(colors: [.blue, .purple]),
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            )
            .foregroundColor(.white)
    }
}

// MARK: - Score Pills
struct ScorePill: View {
    let title: String
    let score: Double
    let color: Color
    
    var body: some View {
        VStack(spacing: 2) {
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
            
            Text(String(format: "%.2f", score))
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(color)
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 4)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(color.opacity(0.1))
        )
    }
}

// MARK: - Statistical Analysis Card
struct StatisticalAnalysisCard: View {
    let analysis: StatisticalAnalysis
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "chart.bar.doc.horizontal")
                    .foregroundColor(.blue)
                Text("Análisis Estadístico Detallado")
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
            }
            
            // Distribución de números
            if let numberAnalysis = analysis.numberAnalysis {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Números más frecuentes en el análisis:")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    HStack {
                        ForEach(numberAnalysis.mostFrequent.prefix(6), id: \.self) { number in
                            Text("\(number)")
                                .font(.caption)
                                .fontWeight(.medium)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(
                                    RoundedRectangle(cornerRadius: 6)
                                        .fill(Color(.systemBlue).opacity(0.2))
                                )
                        }
                        Spacer()
                    }
                }
            }
            
            // Distribución odd/even
            if let distribution = analysis.oddEvenDistribution {
                HStack {
                    Text("Distribución Impar/Par:")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Spacer()
                    
                    Text("\(Int(distribution.oddPercentage))% / \(Int(distribution.evenPercentage))%")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 4)
        )
    }
}

// MARK: - Recommendations Card
struct RecommendationsCard: View {
    let recommendations: [String]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "lightbulb.fill")
                    .foregroundColor(.orange)
                Text("Observaciones Estadísticas")
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
            }
            
            VStack(alignment: .leading, spacing: 8) {
                ForEach(Array(recommendations.enumerated()), id: \.offset) { index, recommendation in
                    if !recommendation.isEmpty && !recommendation.starts(with: "📊") && !recommendation.starts(with: "⚠️") {
                        HStack(alignment: .top, spacing: 8) {
                            Text("•")
                                .foregroundColor(.orange)
                            Text(recommendation)
                                .font(.subheadline)
                                .foregroundColor(.primary)
                                .multilineTextAlignment(.leading)
                            Spacer()
                        }
                    }
                }
            }
            
            // Disclaimer final
            Text("Recuerda: Estos son análisis estadísticos, no recomendaciones de juego.")
                .font(.caption)
                .foregroundColor(.secondary)
                .italic()
                .padding(.top, 8)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemOrange).opacity(0.05))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color(.systemOrange).opacity(0.3), lineWidth: 1)
                )
        )
    }
}

// MARK: - Loading Card
struct LoadingCard: View {
    var body: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            
            Text("OMEGA analizando patrones estadísticos...")
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Text("Procesando modelos: LSTM, Transformer, Monte Carlo, Apriori...")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(40)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 4)
        )
    }
}

// MARK: - Metric Badge
struct MetricBadge: View {
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.subheadline)
                .fontWeight(.bold)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(color.opacity(0.1))
        )
    }
}

// MARK: - Data Models (conectados a tu API real)
struct OmegaPredictionResult: Codable {
    let success: Bool
    let data: OmegaData
    let timestamp: Date
    let type: String
    
    var series: [OmegaSeries] { data.series }
    var analysis: StatisticalAnalysis? { data.analysis }
    var recommendations: [String]? { data.recommendations }
    var disclaimer: String { data.disclaimer }
}

struct OmegaData: Codable {
    let series: [OmegaSeries]
    let analysis: StatisticalAnalysis
    let recommendations: [String]
    let disclaimer: String
}

struct OmegaSeries: Codable {
    let numbers: [Int]
    let confidence: Double
    let patternScore: Double
    let frequencyScore: Double
    let statisticalScore: Double
    let source: String
    let sviScore: Double
    let metaData: [String: String]
}

struct StatisticalAnalysis: Codable {
    let predictionQuality: PredictionQuality
    let numberAnalysis: NumberAnalysis?
    let statisticalSummary: StatisticalSummary
    let disclaimerInfo: DisclaimerInfo
    
    var avgConfidence: Double { predictionQuality.avgConfidence }
    var patternConsistency: Double { predictionQuality.patternConsistency }
    var oddEvenDistribution: OddEvenDistribution? { statisticalSummary.oddEvenDistribution }
    
    private enum CodingKeys: String, CodingKey {
        case predictionQuality = "prediction_quality"
        case numberAnalysis = "number_analysis"
        case statisticalSummary = "statistical_summary"
        case disclaimerInfo = "disclaimer_info"
    }
}

struct PredictionQuality: Codable {
    let avgConfidence: Double
    let patternConsistency: Double
    let avgSviScore: Double
    
    private enum CodingKeys: String, CodingKey {
        case avgConfidence = "avg_confidence"
        case patternConsistency = "pattern_consistency"
        case avgSviScore = "avg_svi_score"
    }
}

struct NumberAnalysis: Codable {
    let mostFrequent: [Int]
    let leastFrequent: [Int]
    
    private enum CodingKeys: String, CodingKey {
        case mostFrequent = "most_frequent"
        case leastFrequent = "least_frequent"
    }
}

struct StatisticalSummary: Codable {
    let avgSum: Double
    let oddEvenDistribution: OddEvenDistribution
    
    private enum CodingKeys: String, CodingKey {
        case avgSum = "avg_sum"
        case oddEvenDistribution = "odd_even_distribution"
    }
}

struct OddEvenDistribution: Codable {
    let oddPercentage: Double
    let evenPercentage: Double
    
    private enum CodingKeys: String, CodingKey {
        case oddPercentage = "odd_percentage"
        case evenPercentage = "even_percentage"
    }
}

struct DisclaimerInfo: Codable {
    let analysisType: String
    let recommendationType: String
    
    private enum CodingKeys: String, CodingKey {
        case analysisType = "analysis_type"
        case recommendationType = "recommendation_type"
    }
}

// MARK: - ViewModel (conectado a tu API real)
class OmegaPredictionsViewModel: ObservableObject {
    @Published var currentResult: OmegaPredictionResult?
    @Published var isLoading = false
    
    func generatePredictions(lotteryType: String, seriesCount: Int) async {
        await MainActor.run { isLoading = true }
        
        do {
            // Llamada real a tu API OMEGA
            let request = PredictionRequest(
                lotteryType: lotteryType,
                seriesCount: seriesCount,
                filters: [:],
                preferences: [:]
            )
            
            let url = URL(string: "http://localhost:8000/entregar_series")!
            var urlRequest = URLRequest(url: url)
            urlRequest.httpMethod = "POST"
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            urlRequest.httpBody = try JSONEncoder().encode(request)
            
            let (data, _) = try await URLSession.shared.data(for: urlRequest)
            let result = try JSONDecoder().decode(OmegaPredictionResult.self, from: data)
            
            await MainActor.run {
                self.currentResult = result
                self.isLoading = false
            }
            
        } catch {
            await MainActor.run {
                self.isLoading = false
                print("Error calling OMEGA API: \(error)")
            }
        }
    }
}

struct PredictionRequest: Codable {
    let lotteryType: String
    let seriesCount: Int
    let filters: [String: String]
    let preferences: [String: String]
    
    private enum CodingKeys: String, CodingKey {
        case lotteryType = "lottery_type"
        case seriesCount = "series_count"
        case filters, preferences
    }
}

// MARK: - Preview
#Preview {
    OmegaPredictionsView()
}