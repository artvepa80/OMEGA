import SwiftUI
import Combine

// MARK: - Enhanced New Prediction View
struct NewPredictionView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject var viewModel: PredictionsViewModel
    
    @State private var selectedModel = "neural_enhanced"
    @State private var selectedCategory: PredictionCategory = .lottery
    @State private var customParameters: [String: String] = [:]
    @State private var predictionName = ""
    @State private var tags: [String] = []
    @State private var newTag = ""
    
    @State private var currentStep = 0
    @State private var showingParametersHelp = false
    
    private let steps = ["Modelo", "Configuración", "Parámetros", "Confirmación"]
    
    private let availableModels = [
        ModelOption(id: "neural_enhanced", name: "Neural Enhanced", description: "Modelo de red neuronal avanzado con alta precisión", accuracy: 0.89, speed: "Rápido"),
        ModelOption(id: "transformer", name: "Transformer", description: "Modelo basado en arquitectura transformer para patrones complejos", accuracy: 0.92, speed: "Medio"),
        ModelOption(id: "genetic", name: "Genético", description: "Algoritmo genético optimizado para exploración amplia", accuracy: 0.85, speed: "Lento"),
        ModelOption(id: "lstm", name: "LSTM", description: "Redes LSTM para análisis de secuencias temporales", accuracy: 0.87, speed: "Medio"),
        ModelOption(id: "monte_carlo", name: "Monte Carlo", description: "Simulación Monte Carlo para análisis probabilístico", accuracy: 0.83, speed: "Rápido")
    ]
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Progress Bar
                ProgressBarView(currentStep: currentStep, totalSteps: steps.count, steps: steps)
                
                // Content
                ScrollView {
                    VStack(spacing: 24) {
                        switch currentStep {
                        case 0:
                            ModelSelectionStep(
                                selectedModel: $selectedModel,
                                models: availableModels
                            )
                        case 1:
                            ConfigurationStep(
                                selectedCategory: $selectedCategory,
                                predictionName: $predictionName,
                                tags: $tags,
                                newTag: $newTag
                            )
                        case 2:
                            ParametersStep(
                                selectedModel: selectedModel,
                                customParameters: $customParameters,
                                showingHelp: $showingParametersHelp
                            )
                        case 3:
                            ConfirmationStep(
                                selectedModel: selectedModel,
                                selectedCategory: selectedCategory,
                                predictionName: predictionName,
                                tags: tags,
                                customParameters: customParameters,
                                models: availableModels
                            )
                        default:
                            EmptyView()
                        }
                    }
                    .padding()
                }
                
                // Action Buttons
                ActionButtonsView(
                    currentStep: $currentStep,
                    totalSteps: steps.count,
                    isCreating: viewModel.isCreatingPrediction,
                    canProceed: canProceedToNextStep,
                    onBack: { currentStep = max(0, currentStep - 1) },
                    onNext: {
                        if currentStep < steps.count - 1 {
                            currentStep += 1
                        }
                    },
                    onCreate: createPrediction,
                    onCancel: { dismiss() }
                )
            }
            .navigationTitle("Nueva Predicción")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancelar") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    if currentStep == 2 {
                        Button("Ayuda") {
                            showingParametersHelp = true
                        }
                    }
                }
            }
            .sheet(isPresented: $showingParametersHelp) {
                ParametersHelpView()
            }
        }
    }
    
    private var canProceedToNextStep: Bool {
        switch currentStep {
        case 0:
            return !selectedModel.isEmpty
        case 1:
            return !predictionName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        case 2:
            return true // Parameters are optional
        case 3:
            return true
        default:
            return false
        }
    }
    
    private func createPrediction() {
        let parameters = PredictionParameters(
            modelType: selectedModel,
            customParams: customParameters.isEmpty ? nil : customParameters.mapValues { AnyCodable($0) }
        )
        
        Task {
            let success = await viewModel.createPrediction(parameters: parameters)
            if success {
                dismiss()
            }
        }
    }
}

// MARK: - Progress Bar View
struct ProgressBarView: View {
    let currentStep: Int
    let totalSteps: Int
    let steps: [String]
    
    var body: some View {
        VStack(spacing: 16) {
            // Progress Bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color(.systemGray5))
                        .frame(height: 4)
                    
                    Rectangle()
                        .fill(Color.blue)
                        .frame(width: geometry.size.width * CGFloat(currentStep + 1) / CGFloat(totalSteps), height: 4)
                        .animation(.easeInOut(duration: 0.3), value: currentStep)
                }
            }
            .frame(height: 4)
            
            // Step Indicators
            HStack {
                ForEach(0..<totalSteps, id: \.self) { index in
                    VStack(spacing: 4) {
                        Circle()
                            .fill(index <= currentStep ? Color.blue : Color(.systemGray4))
                            .frame(width: 12, height: 12)
                        
                        Text(steps[index])
                            .font(.caption2)
                            .foregroundColor(index <= currentStep ? .blue : .secondary)
                    }
                    
                    if index < totalSteps - 1 {
                        Spacer()
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
    }
}

// MARK: - Model Selection Step
struct ModelSelectionStep: View {
    @Binding var selectedModel: String
    let models: [ModelOption]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            StepHeader(
                title: "Selecciona el Modelo de IA",
                subtitle: "Elige el modelo que mejor se adapte a tus necesidades"
            )
            
            LazyVStack(spacing: 12) {
                ForEach(models, id: \.id) { model in
                    ModelCard(
                        model: model,
                        isSelected: selectedModel == model.id,
                        onSelect: {
                            selectedModel = model.id
                            HapticManager.shared.lightImpact()
                        }
                    )
                }
            }
        }
    }
}

// MARK: - Configuration Step
struct ConfigurationStep: View {
    @Binding var selectedCategory: PredictionCategory
    @Binding var predictionName: String
    @Binding var tags: [String]
    @Binding var newTag: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            StepHeader(
                title: "Configuración General",
                subtitle: "Personaliza los detalles de tu predicción"
            )
            
            // Prediction Name
            VStack(alignment: .leading, spacing: 8) {
                Text("Nombre de la Predicción")
                    .font(.headline)
                    .fontWeight(.medium)
                
                TextField("Ej: Predicción Semanal Lotería", text: $predictionName)
                    .textFieldStyle(CustomTextFieldStyle())
            }
            
            // Category Selection
            VStack(alignment: .leading, spacing: 12) {
                Text("Categoría")
                    .font(.headline)
                    .fontWeight(.medium)
                
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 12) {
                    ForEach(PredictionCategory.allCases, id: \.self) { category in
                        CategoryCard(
                            category: category,
                            isSelected: selectedCategory == category,
                            onSelect: {
                                selectedCategory = category
                                HapticManager.shared.lightImpact()
                            }
                        )
                    }
                }
            }
            
            // Tags
            VStack(alignment: .leading, spacing: 12) {
                Text("Etiquetas (Opcional)")
                    .font(.headline)
                    .fontWeight(.medium)
                
                // Add tag field
                HStack {
                    TextField("Agregar etiqueta", text: $newTag)
                        .textFieldStyle(CustomTextFieldStyle())
                    
                    Button("Agregar") {
                        if !newTag.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                            tags.append(newTag.trimmingCharacters(in: .whitespacesAndNewlines))
                            newTag = ""
                            HapticManager.shared.lightImpact()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(newTag.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
                
                // Tags display
                if !tags.isEmpty {
                    TagsView(tags: tags) { tagToRemove in
                        tags.removeAll { $0 == tagToRemove }
                        HapticManager.shared.lightImpact()
                    }
                }
            }
        }
    }
}

// MARK: - Parameters Step
struct ParametersStep: View {
    let selectedModel: String
    @Binding var customParameters: [String: String]
    @Binding var showingHelp: Bool
    
    private let modelParameters: [String: [ParameterDefinition]] = [
        "neural_enhanced": [
            ParameterDefinition(name: "learning_rate", displayName: "Tasa de Aprendizaje", defaultValue: "0.001", description: "Velocidad de entrenamiento del modelo"),
            ParameterDefinition(name: "epochs", displayName: "Épocas", defaultValue: "100", description: "Número de iteraciones de entrenamiento"),
            ParameterDefinition(name: "batch_size", displayName: "Tamaño de Lote", defaultValue: "32", description: "Cantidad de datos procesados simultáneamente")
        ],
        "transformer": [
            ParameterDefinition(name: "attention_heads", displayName: "Cabezas de Atención", defaultValue: "8", description: "Número de mecanismos de atención"),
            ParameterDefinition(name: "hidden_size", displayName: "Tamaño Oculto", defaultValue: "512", description: "Dimensión de las capas ocultas"),
            ParameterDefinition(name: "num_layers", displayName: "Número de Capas", defaultValue: "6", description: "Profundidad del modelo")
        ]
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            StepHeader(
                title: "Parámetros Avanzados",
                subtitle: "Ajusta los parámetros del modelo (opcional)"
            )
            
            if let parameters = modelParameters[selectedModel] {
                LazyVStack(spacing: 16) {
                    ForEach(parameters, id: \.name) { parameter in
                        ParameterInputView(
                            parameter: parameter,
                            value: Binding(
                                get: { customParameters[parameter.name] ?? parameter.defaultValue },
                                set: { customParameters[parameter.name] = $0 }
                            )
                        )
                    }
                }
            } else {
                VStack(spacing: 16) {
                    Image(systemName: "gear.circle")
                        .font(.system(size: 40))
                        .foregroundColor(.secondary)
                    
                    Text("No hay parámetros configurables para este modelo")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding()
            }
            
            InfoBox(
                title: "Sugerencia",
                message: "Los valores por defecto están optimizados para la mayoría de casos. Solo modifica si tienes experiencia con modelos de IA.",
                type: .info
            )
        }
    }
}

// MARK: - Confirmation Step
struct ConfirmationStep: View {
    let selectedModel: String
    let selectedCategory: PredictionCategory
    let predictionName: String
    let tags: [String]
    let customParameters: [String: String]
    let models: [ModelOption]
    
    private var selectedModelInfo: ModelOption? {
        models.first { $0.id == selectedModel }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            StepHeader(
                title: "Confirmar Predicción",
                subtitle: "Revisa los detalles antes de crear la predicción"
            )
            
            VStack(spacing: 16) {
                // Prediction Summary
                SummaryCard(title: "Resumen de la Predicción") {
                    VStack(alignment: .leading, spacing: 12) {
                        SummaryRow(label: "Nombre", value: predictionName)
                        SummaryRow(label: "Categoría", value: selectedCategory.displayName)
                        
                        if let modelInfo = selectedModelInfo {
                            SummaryRow(label: "Modelo", value: modelInfo.name)
                            SummaryRow(label: "Precisión Esperada", value: "\(Int(modelInfo.accuracy * 100))%")
                            SummaryRow(label: "Velocidad", value: modelInfo.speed)
                        }
                        
                        if !tags.isEmpty {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Etiquetas:")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                
                                TagsView(tags: tags, onRemove: nil)
                            }
                        }
                    }
                }
                
                // Model Details
                if let modelInfo = selectedModelInfo {
                    SummaryCard(title: "Detalles del Modelo") {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(modelInfo.description)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            
                            HStack {
                                AccuracyBadge(accuracy: modelInfo.accuracy)
                                Spacer()
                                SpeedBadge(speed: modelInfo.speed)
                            }
                        }
                    }
                }
                
                // Custom Parameters
                if !customParameters.isEmpty {
                    SummaryCard(title: "Parámetros Personalizados") {
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(Array(customParameters.keys.sorted()), id: \.self) { key in
                                if let value = customParameters[key] {
                                    SummaryRow(label: key.capitalized, value: value)
                                }
                            }
                        }
                    }
                }
            }
            
            InfoBox(
                title: "Tiempo Estimado",
                message: "Esta predicción tomará aproximadamente 2-5 minutos en procesarse",
                type: .info
            )
        }
    }
}

// MARK: - Supporting Views
struct StepHeader: View {
    let title: String
    let subtitle: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(subtitle)
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }
}

struct ModelCard: View {
    let model: ModelOption
    let isSelected: Bool
    let onSelect: () -> Void
    
    var body: some View {
        Button(action: onSelect) {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.name)
                            .font(.headline)
                            .fontWeight(.semibold)
                            .foregroundColor(.primary)
                        
                        Text(model.description)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.leading)
                    }
                    
                    Spacer()
                    
                    Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                        .font(.title2)
                        .foregroundColor(isSelected ? .blue : .secondary)
                }
                
                HStack {
                    AccuracyBadge(accuracy: model.accuracy)
                    Spacer()
                    SpeedBadge(speed: model.speed)
                }
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(.systemBackground))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(isSelected ? Color.blue : Color(.systemGray4), lineWidth: isSelected ? 2 : 1)
                    )
            )
        }
        .buttonStyle(ScaleButtonStyle())
    }
}

struct CategoryCard: View {
    let category: PredictionCategory
    let isSelected: Bool
    let onSelect: () -> Void
    
    var body: some View {
        Button(action: onSelect) {
            VStack(spacing: 8) {
                Image(systemName: category.icon)
                    .font(.title2)
                    .foregroundColor(isSelected ? .blue : .secondary)
                
                Text(category.displayName)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(isSelected ? Color.blue.opacity(0.1) : Color(.systemGray6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(isSelected ? Color.blue : Color.clear, lineWidth: 1)
                    )
            )
        }
        .buttonStyle(ScaleButtonStyle())
    }
}

struct TagsView: View {
    let tags: [String]
    let onRemove: ((String) -> Void)?
    
    var body: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 3), alignment: .leading, spacing: 8) {
            ForEach(tags, id: \.self) { tag in
                HStack(spacing: 4) {
                    Text(tag)
                        .font(.caption)
                        .foregroundColor(.blue)
                    
                    if let onRemove = onRemove {
                        Button(action: { onRemove(tag) }) {
                            Image(systemName: "xmark.circle.fill")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(
                    Capsule()
                        .fill(Color.blue.opacity(0.1))
                )
            }
        }
    }
}

struct ParameterInputView: View {
    let parameter: ParameterDefinition
    @Binding var value: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(parameter.displayName)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Spacer()
                
                Button(action: {}) {
                    Image(systemName: "info.circle")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            TextField(parameter.defaultValue, text: $value)
                .textFieldStyle(CustomTextFieldStyle())
            
            Text(parameter.description)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}

struct SummaryCard<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .fontWeight(.semibold)
            
            content
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.05), radius: 4, x: 0, y: 2)
        )
    }
}

struct SummaryRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Spacer()
            
            Text(value)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(.primary)
        }
    }
}

struct AccuracyBadge: View {
    let accuracy: Double
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "target")
                .font(.caption2)
                .foregroundColor(.green)
            
            Text("\(Int(accuracy * 100))%")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.green)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(Color.green.opacity(0.1))
        )
    }
}

struct SpeedBadge: View {
    let speed: String
    
    private var speedColor: Color {
        switch speed.lowercased() {
        case "rápido": return .green
        case "medio": return .orange
        case "lento": return .red
        default: return .gray
        }
    }
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "speedometer")
                .font(.caption2)
                .foregroundColor(speedColor)
            
            Text(speed)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(speedColor)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(speedColor.opacity(0.1))
        )
    }
}

struct InfoBox: View {
    let title: String
    let message: String
    let type: InfoBoxType
    
    enum InfoBoxType {
        case info, warning, success, error
        
        var color: Color {
            switch self {
            case .info: return .blue
            case .warning: return .orange
            case .success: return .green
            case .error: return .red
            }
        }
        
        var icon: String {
            switch self {
            case .info: return "info.circle.fill"
            case .warning: return "exclamationmark.triangle.fill"
            case .success: return "checkmark.circle.fill"
            case .error: return "xmark.circle.fill"
            }
        }
    }
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: type.icon)
                .font(.title3)
                .foregroundColor(type.color)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)
                
                Text(message)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(type.color.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(type.color.opacity(0.3), lineWidth: 1)
                )
        )
    }
}

struct ActionButtonsView: View {
    @Binding var currentStep: Int
    let totalSteps: Int
    let isCreating: Bool
    let canProceed: Bool
    let onBack: () -> Void
    let onNext: () -> Void
    let onCreate: () -> Void
    let onCancel: () -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            Divider()
            
            HStack(spacing: 16) {
                // Back Button
                if currentStep > 0 {
                    Button("Anterior") {
                        onBack()
                        HapticManager.shared.lightImpact()
                    }
                    .buttonStyle(.bordered)
                    .disabled(isCreating)
                }
                
                Spacer()
                
                // Next/Create Button
                if currentStep < totalSteps - 1 {
                    Button("Siguiente") {
                        onNext()
                        HapticManager.shared.lightImpact()
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!canProceed || isCreating)
                } else {
                    Button(action: {
                        onCreate()
                        HapticManager.shared.mediumImpact()
                    }) {
                        HStack {
                            if isCreating {
                                ProgressView()
                                    .scaleEffect(0.8)
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            }
                            
                            Text(isCreating ? "Creando..." : "Crear Predicción")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!canProceed || isCreating)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
    }
}

// MARK: - Custom Text Field Style
struct CustomTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color(.systemGray6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color(.systemGray4), lineWidth: 1)
                    )
            )
    }
}

// MARK: - Supporting Models
struct ModelOption {
    let id: String
    let name: String
    let description: String
    let accuracy: Double
    let speed: String
}

struct ParameterDefinition {
    let name: String
    let displayName: String
    let defaultValue: String
    let description: String
}

// MARK: - Parameters Help View
struct ParametersHelpView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Text("Los parámetros avanzados te permiten afinar el comportamiento del modelo de IA para obtener mejores resultados.")
                        .font(.body)
                        .foregroundColor(.secondary)
                    
                    VStack(alignment: .leading, spacing: 16) {
                        ParameterHelpItem(
                            title: "Tasa de Aprendizaje",
                            description: "Controla qué tan rápido aprende el modelo. Valores más altos pueden causar inestabilidad, valores más bajos pueden ralentizar el entrenamiento."
                        )
                        
                        ParameterHelpItem(
                            title: "Épocas",
                            description: "Número de veces que el modelo revisa todos los datos de entrenamiento. Más épocas pueden mejorar la precisión pero aumentan el tiempo de procesamiento."
                        )
                        
                        ParameterHelpItem(
                            title: "Tamaño de Lote",
                            description: "Cantidad de datos procesados simultáneamente. Lotes más grandes usan más memoria pero pueden ser más eficientes."
                        )
                    }
                    
                    InfoBox(
                        title: "Recomendación",
                        message: "Si no estás seguro, deja los valores por defecto. Están optimizados para la mayoría de casos de uso.",
                        type: .info
                    )
                }
                .padding()
            }
            .navigationTitle("Ayuda de Parámetros")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cerrar") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct ParameterHelpItem: View {
    let title: String
    let description: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
                .fontWeight(.semibold)
            
            Text(description)
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}

#Preview {
    NewPredictionView()
        .environmentObject(PredictionsViewModel())
}
