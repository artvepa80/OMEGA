import SwiftUI
import Charts
import MapKit

// MARK: - Complete Enterprise Views Collection

// MARK: - Enhanced Results View
struct ResultsView: View {
    @StateObject private var viewModel = ResultsViewModel()
    @State private var selectedTimeRange: TimeRange = .week
    @State private var selectedMetric: MetricType = .accuracy
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    // Time Range Selector
                    TimeRangeSelector(selectedRange: $selectedTimeRange)
                    
                    // Key Metrics Overview
                    MetricsOverviewCard(
                        metrics: viewModel.keyMetrics,
                        timeRange: selectedTimeRange
                    )
                    
                    // Performance Charts
                    PerformanceChartsCard(
                        chartData: viewModel.chartData,
                        selectedMetric: $selectedMetric
                    )
                    
                    // Results Table
                    ResultsTableCard(
                        results: viewModel.results,
                        isLoading: viewModel.isLoading
                    )
                    
                    // Insights and Recommendations
                    InsightsCard(insights: viewModel.insights)
                    
                    // Export Options
                    ExportOptionsCard {
                        Task { await viewModel.exportResults() }
                    }
                }
                .padding()
            }
            .navigationTitle("Resultados")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarTrailing) {
                    Button(action: {
                        Task { await viewModel.refreshData() }
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(viewModel.isLoading)
                    
                    Button(action: {
                        // Share functionality
                    }) {
                        Image(systemName: "square.and.arrow.up")
                    }
                }
            }
            .refreshable {
                await viewModel.refreshData()
            }
            .task {
                await viewModel.loadInitialData()
            }
        }
    }
}

// MARK: - Enhanced Settings View with Enterprise Features
struct EnhancedSettingsView: View {
    @StateObject private var viewModel = SettingsViewModel()
    @EnvironmentObject var authManager: AuthManager
    
    @State private var showingLogoutAlert = false
    @State private var showingDataExport = false
    @State private var showingSecuritySettings = false
    
    var body: some View {
        NavigationView {
            List {
                // User Profile Section
                Section {
                    UserProfileCard(user: authManager.user)
                } header: {
                    Text("Perfil")
                }
                
                // Quick Actions
                Section {
                    QuickActionRow(
                        title: "Sincronizar Datos",
                        icon: "arrow.clockwise.circle",
                        action: { Task { await viewModel.syncData() } }
                    )
                    
                    QuickActionRow(
                        title: "Borrar Caché",
                        icon: "trash.circle",
                        action: { Task { await viewModel.clearCache() } }
                    )
                    
                    QuickActionRow(
                        title: "Exportar Datos",
                        icon: "square.and.arrow.up.circle",
                        action: { showingDataExport = true }
                    )
                } header: {
                    Text("Acciones Rápidas")
                }
                
                // App Preferences
                Section {
                    ToggleRow(
                        title: "Notificaciones Push",
                        icon: "bell",
                        isOn: $viewModel.pushNotificationsEnabled
                    )
                    
                    ToggleRow(
                        title: "Modo Oscuro",
                        icon: "moon",
                        isOn: $viewModel.darkModeEnabled
                    )
                    
                    ToggleRow(
                        title: "Análisis de Uso",
                        icon: "chart.bar",
                        isOn: $viewModel.analyticsEnabled
                    )
                    
                    ToggleRow(
                        title: "Feedback Háptico",
                        icon: "hand.tap",
                        isOn: $viewModel.hapticFeedbackEnabled
                    )
                } header: {
                    Text("Preferencias")
                }
                
                // Security Settings
                Section {
                    NavigationLink(destination: SecuritySettingsDetailView()) {
                        SettingsRow(
                            title: "Configuración de Seguridad",
                            icon: "lock.shield",
                            hasChevron: true
                        )
                    }
                    
                    ToggleRow(
                        title: "Autenticación Biométrica",
                        icon: "faceid",
                        isOn: $viewModel.biometricAuthEnabled
                    )
                    
                    SettingsRow(
                        title: "Cambiar Contraseña",
                        icon: "key",
                        hasChevron: true,
                        action: { /* Navigate to change password */ }
                    )
                } header: {
                    Text("Seguridad")
                }
                
                // Data & Privacy
                Section {
                    NavigationLink(destination: DataPrivacyView()) {
                        SettingsRow(
                            title: "Privacidad de Datos",
                            icon: "hand.raised.shield",
                            hasChevron: true
                        )
                    }
                    
                    SettingsRow(
                        title: "Solicitud de Datos (GDPR)",
                        icon: "doc.text.below.ecg",
                        hasChevron: true,
                        action: { /* GDPR data request */ }
                    )
                } header: {
                    Text("Datos y Privacidad")
                }
                
                // Support & About
                Section {
                    NavigationLink(destination: HelpSupportView()) {
                        SettingsRow(
                            title: "Ayuda y Soporte",
                            icon: "questionmark.circle",
                            hasChevron: true
                        )
                    }
                    
                    NavigationLink(destination: AboutView()) {
                        SettingsRow(
                            title: "Acerca de OMEGA",
                            icon: "info.circle",
                            hasChevron: true
                        )
                    }
                    
                    SettingsRow(
                        title: "Términos de Servicio",
                        icon: "doc.text",
                        hasChevron: true,
                        action: { /* Show terms */ }
                    )
                    
                    SettingsRow(
                        title: "Política de Privacidad",
                        icon: "hand.raised",
                        hasChevron: true,
                        action: { /* Show privacy policy */ }
                    )
                } header: {
                    Text("Soporte")
                }
                
                // System Information
                Section {
                    InfoRow(title: "Versión de la App", value: AppVersion.version)
                    InfoRow(title: "Build", value: AppVersion.build)
                    InfoRow(title: "Entorno", value: viewModel.currentEnvironment)
                    InfoRow(title: "ID del Dispositivo", value: UIDevice.current.identifierForVendor?.uuidString ?? "N/A")
                } header: {
                    Text("Información del Sistema")
                }
                
                // Account Actions
                Section {
                    Button("Cerrar Sesión") {
                        showingLogoutAlert = true
                    }
                    .foregroundColor(.red)
                    .fontWeight(.medium)
                } footer: {
                    Text("Al cerrar sesión se eliminarán todos los datos locales.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Configuración")
            .navigationBarTitleDisplayMode(.large)
        }
        .alert("Cerrar Sesión", isPresented: $showingLogoutAlert) {
            Button("Cancelar", role: .cancel) { }
            Button("Cerrar Sesión", role: .destructive) {
                Task { await authManager.logout() }
            }
        } message: {
            Text("¿Estás seguro de que deseas cerrar sesión?")
        }
        .sheet(isPresented: $showingDataExport) {
            DataExportView()
        }
    }
}

// MARK: - Advanced Analytics Dashboard
struct AdvancedAnalyticsView: View {
    @StateObject private var viewModel = AdvancedAnalyticsViewModel()
    @State private var selectedDateRange = DateRange.lastMonth
    @State private var selectedMetrics: Set<AnalyticsMetric> = [.predictions, .accuracy, .responseTime]
    
    var body: some View {
        NavigationView {
            GeometryReader { geometry in
                ScrollView {
                    LazyVStack(spacing: 20) {
                        // Controls
                        AnalyticsControlsCard(
                            dateRange: $selectedDateRange,
                            selectedMetrics: $selectedMetrics
                        )
                        
                        // Real-time Metrics
                        RealTimeMetricsCard(metrics: viewModel.realTimeMetrics)
                        
                        // Charts Grid
                        AnalyticsChartsGrid(
                            chartData: viewModel.chartData,
                            selectedMetrics: selectedMetrics,
                            geometry: geometry
                        )
                        
                        // Detailed Tables
                        DetailedAnalyticsTable(data: viewModel.detailedData)
                        
                        // Insights & Trends
                        TrendsAnalysisCard(trends: viewModel.trends)
                        
                        // Predictive Analytics
                        PredictiveAnalyticsCard(predictions: viewModel.predictiveData)
                    }
                    .padding()
                }
            }
            .navigationTitle("Analytics Avanzado")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarTrailing) {
                    Button("Configurar") {
                        // Analytics configuration
                    }
                    
                    Button("Exportar") {
                        Task { await viewModel.exportAnalytics() }
                    }
                }
            }
        }
        .task {
            await viewModel.loadAnalytics(for: selectedDateRange)
        }
        .onChange(of: selectedDateRange) { _, newRange in
            Task {
                await viewModel.loadAnalytics(for: newRange)
            }
        }
    }
}

// MARK: - System Health Monitor
struct SystemHealthView: View {
    @StateObject private var viewModel = SystemHealthViewModel()
    @State private var autoRefresh = true
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 20) {
                    // Overall Health Status
                    OverallHealthCard(status: viewModel.overallStatus)
                    
                    // System Components
                    SystemComponentsGrid(components: viewModel.components)
                    
                    // Performance Metrics
                    PerformanceMetricsCard(metrics: viewModel.performanceMetrics)
                    
                    // Recent Alerts
                    RecentAlertsCard(alerts: viewModel.recentAlerts)
                    
                    // Resource Usage
                    ResourceUsageCard(usage: viewModel.resourceUsage)
                }
                .padding()
            }
            .navigationTitle("Estado del Sistema")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarTrailing) {
                    Toggle("Auto", isOn: $autoRefresh)
                        .toggleStyle(.button)
                    
                    Button("Actualizar") {
                        Task { await viewModel.refreshStatus() }
                    }
                    .disabled(viewModel.isLoading)
                }
            }
        }
        .task {
            await viewModel.loadSystemStatus()
            
            if autoRefresh {
                await viewModel.startAutoRefresh()
            }
        }
        .onChange(of: autoRefresh) { _, newValue in
            Task {
                if newValue {
                    await viewModel.startAutoRefresh()
                } else {
                    await viewModel.stopAutoRefresh()
                }
            }
        }
    }
}

// MARK: - User Management View (Admin)
struct UserManagementView: View {
    @StateObject private var viewModel = UserManagementViewModel()
    @State private var showingAddUser = false
    @State private var searchText = ""
    
    var body: some View {
        NavigationView {
            VStack {
                // Search Bar
                SearchBar(text: $searchText, placeholder: "Buscar usuarios...")
                
                // Users List
                List {
                    ForEach(viewModel.filteredUsers(searchText: searchText), id: \.id) { user in
                        UserRowView(user: user) {
                            // User detail action
                        }
                    }
                    .onDelete(perform: viewModel.deleteUsers)
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("Gestión de Usuarios")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarTrailing) {
                    Button("Agregar") {
                        showingAddUser = true
                    }
                }
            }
            .sheet(isPresented: $showingAddUser) {
                AddUserView()
            }
        }
        .task {
            await viewModel.loadUsers()
        }
    }
}

// MARK: - Audit Log View
struct AuditLogView: View {
    @StateObject private var viewModel = AuditLogViewModel()
    @State private var selectedFilter: AuditFilter = .all
    @State private var dateRange = DateRange.lastWeek
    
    var body: some View {
        NavigationView {
            VStack {
                // Filters
                HStack {
                    Picker("Filtro", selection: $selectedFilter) {
                        ForEach(AuditFilter.allCases, id: \.self) { filter in
                            Text(filter.displayName).tag(filter)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    
                    Spacer()
                    
                    DateRangePicker(selection: $dateRange)
                }
                .padding()
                
                // Audit Entries
                List(viewModel.filteredEntries, id: \.id) { entry in
                    AuditEntryRow(entry: entry)
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("Registro de Auditoría")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Exportar") {
                        Task { await viewModel.exportAuditLog() }
                    }
                }
            }
        }
        .task {
            await viewModel.loadAuditEntries(filter: selectedFilter, dateRange: dateRange)
        }
        .onChange(of: selectedFilter) { _, newFilter in
            Task {
                await viewModel.loadAuditEntries(filter: newFilter, dateRange: dateRange)
            }
        }
        .onChange(of: dateRange) { _, newRange in
            Task {
                await viewModel.loadAuditEntries(filter: selectedFilter, dateRange: newRange)
            }
        }
    }
}

// MARK: - Supporting Views and Components

struct UserProfileCard: View {
    let user: User?
    
    var body: some View {
        HStack(spacing: 16) {
            // Avatar
            ZStack {
                Circle()
                    .fill(LinearGradient(
                        gradient: Gradient(colors: [.blue, .purple]),
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ))
                    .frame(width: 60, height: 60)
                
                Text(user?.profileImageInitials ?? "U")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
            }
            
            // User Info
            VStack(alignment: .leading, spacing: 4) {
                Text(user?.displayName ?? "Usuario")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Text(user?.email ?? user?.username ?? "")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                HStack(spacing: 8) {
                    Image(systemName: "checkmark.shield.fill")
                        .font(.caption)
                        .foregroundColor(.green)
                    
                    Text(user?.role.capitalized ?? "")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(4)
                }
            }
            
            Spacer()
            
            // Edit Button
            Button("Editar") {
                // Edit profile action
            }
            .buttonStyle(.bordered)
        }
        .padding()
    }
}

struct QuickActionRow: View {
    let title: String
    let icon: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                Text(title)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct ToggleRow: View {
    let title: String
    let icon: String
    @Binding var isOn: Bool
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .font(.title3)
                .foregroundColor(.blue)
                .frame(width: 24)
            
            Text(title)
            
            Spacer()
            
            Toggle("", isOn: $isOn)
                .labelsHidden()
        }
    }
}

struct SettingsRow: View {
    let title: String
    let icon: String
    let hasChevron: Bool
    let action: (() -> Void)?
    
    init(title: String, icon: String, hasChevron: Bool = false, action: (() -> Void)? = nil) {
        self.title = title
        self.icon = icon
        self.hasChevron = hasChevron
        self.action = action
    }
    
    var body: some View {
        Button(action: action ?? {}) {
            HStack {
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundColor(.blue)
                    .frame(width: 24)
                
                Text(title)
                    .foregroundColor(.primary)
                
                Spacer()
                
                if hasChevron {
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(action == nil)
    }
}

struct InfoRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .foregroundColor(.primary)
            
            Spacer()
            
            Text(value)
                .foregroundColor(.secondary)
                .fontWeight(.medium)
        }
    }
}

struct SearchBar: View {
    @Binding var text: String
    let placeholder: String
    
    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField(placeholder, text: $text)
                .textFieldStyle(PlainTextFieldStyle())
            
            if !text.isEmpty {
                Button("Limpiar") {
                    text = ""
                }
                .foregroundColor(.blue)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

struct UserRowView: View {
    let user: User
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                // Avatar
                Circle()
                    .fill(Color.blue)
                    .frame(width: 40, height: 40)
                    .overlay(
                        Text(user.profileImageInitials)
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                    )
                
                // User Info
                VStack(alignment: .leading, spacing: 2) {
                    Text(user.displayName)
                        .font(.subheadline)
                        .fontWeight(.medium)
                    
                    Text(user.email ?? user.username)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Role Badge
                Text(user.role.capitalized)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(4)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct AuditEntryRow: View {
    let entry: AuditEntry
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(entry.action)
                    .font(.subheadline)
                    .fontWeight(.medium)
                
                Spacer()
                
                Text(entry.timestamp.formatted(date: .omitted, time: .shortened))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Text(entry.details)
                .font(.caption)
                .foregroundColor(.secondary)
            
            HStack {
                Text("Usuario: \(entry.userId)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(entry.ipAddress)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Supporting Models and Enums

enum TimeRange: String, CaseIterable {
    case hour = "1h"
    case day = "24h"
    case week = "7d"
    case month = "30d"
    case year = "1y"
    
    var displayName: String { rawValue }
}

enum MetricType: String, CaseIterable {
    case accuracy = "accuracy"
    case responseTime = "response_time"
    case throughput = "throughput"
    case errorRate = "error_rate"
    
    var displayName: String {
        switch self {
        case .accuracy: return "Precisión"
        case .responseTime: return "Tiempo de Respuesta"
        case .throughput: return "Rendimiento"
        case .errorRate: return "Tasa de Error"
        }
    }
}

enum DateRange: String, CaseIterable {
    case lastWeek = "last_week"
    case lastMonth = "last_month"
    case lastQuarter = "last_quarter"
    case lastYear = "last_year"
    
    var displayName: String {
        switch self {
        case .lastWeek: return "Última Semana"
        case .lastMonth: return "Último Mes"
        case .lastQuarter: return "Último Trimestre"
        case .lastYear: return "Último Año"
        }
    }
}

enum AnalyticsMetric: String, CaseIterable {
    case predictions = "predictions"
    case accuracy = "accuracy"
    case responseTime = "response_time"
    case users = "users"
    case errors = "errors"
    
    var displayName: String {
        switch self {
        case .predictions: return "Predicciones"
        case .accuracy: return "Precisión"
        case .responseTime: return "Tiempo de Respuesta"
        case .users: return "Usuarios"
        case .errors: return "Errores"
        }
    }
}

enum AuditFilter: String, CaseIterable {
    case all = "all"
    case logins = "logins"
    case predictions = "predictions"
    case admin = "admin"
    case errors = "errors"
    
    var displayName: String {
        switch self {
        case .all: return "Todos"
        case .logins: return "Inicios de Sesión"
        case .predictions: return "Predicciones"
        case .admin: return "Administración"
        case .errors: return "Errores"
        }
    }
}

struct AuditEntry: Identifiable {
    let id = UUID()
    let action: String
    let details: String
    let userId: String
    let ipAddress: String
    let timestamp: Date
}

// MARK: - ViewModels Placeholders (to be implemented)

@MainActor
class ResultsViewModel: ObservableObject {
    @Published var keyMetrics: [String: Double] = [:]
    @Published var chartData: [String: Any] = [:]
    @Published var results: [String] = []
    @Published var insights: [String] = []
    @Published var isLoading = false
    
    func loadInitialData() async { }
    func refreshData() async { }
    func exportResults() async { }
}

@MainActor
class AdvancedAnalyticsViewModel: ObservableObject {
    @Published var realTimeMetrics: [String: Any] = [:]
    @Published var chartData: [String: Any] = [:]
    @Published var detailedData: [String: Any] = [:]
    @Published var trends: [String] = []
    @Published var predictiveData: [String: Any] = [:]
    
    func loadAnalytics(for dateRange: DateRange) async { }
    func exportAnalytics() async { }
}

@MainActor
class SystemHealthViewModel: ObservableObject {
    @Published var overallStatus: String = "Healthy"
    @Published var components: [String] = []
    @Published var performanceMetrics: [String: Any] = [:]
    @Published var recentAlerts: [String] = []
    @Published var resourceUsage: [String: Double] = [:]
    @Published var isLoading = false
    
    func loadSystemStatus() async { }
    func refreshStatus() async { }
    func startAutoRefresh() async { }
    func stopAutoRefresh() async { }
}

@MainActor
class UserManagementViewModel: ObservableObject {
    @Published var users: [User] = []
    
    func loadUsers() async { }
    func filteredUsers(searchText: String) -> [User] { return users }
    func deleteUsers(at offsets: IndexSet) { }
}

@MainActor
class AuditLogViewModel: ObservableObject {
    @Published var filteredEntries: [AuditEntry] = []
    
    func loadAuditEntries(filter: AuditFilter, dateRange: DateRange) async { }
    func exportAuditLog() async { }
}
