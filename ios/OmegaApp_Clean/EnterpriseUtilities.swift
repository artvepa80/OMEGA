import Foundation
import SwiftUI
import Combine
import Network
import CoreLocation
import UserNotifications

// MARK: - Enterprise Utilities Collection

// MARK: - Network Connectivity Manager
@MainActor
final class ConnectivityManager: ObservableObject {
    @Published var isConnected = true
    @Published var connectionType: ConnectionType = .wifi
    
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "ConnectivityMonitor")
    
    enum ConnectionType {
        case wifi, cellular, ethernet, unknown
        
        var displayName: String {
            switch self {
            case .wifi: return "Wi-Fi"
            case .cellular: return "Datos Móviles"
            case .ethernet: return "Ethernet"
            case .unknown: return "Desconocido"
            }
        }
        
        var icon: String {
            switch self {
            case .wifi: return "wifi"
            case .cellular: return "antenna.radiowaves.left.and.right"
            case .ethernet: return "cable.connector"
            case .unknown: return "questionmark.circle"
            }
        }
    }
    
    init() {
        startMonitoring()
    }
    
    private func startMonitoring() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isConnected = path.status == .satisfied
                self?.updateConnectionType(path)
            }
        }
        monitor.start(queue: queue)
    }
    
    private func updateConnectionType(_ path: NWPath) {
        if path.usesInterfaceType(.wifi) {
            connectionType = .wifi
        } else if path.usesInterfaceType(.cellular) {
            connectionType = .cellular
        } else if path.usesInterfaceType(.wiredEthernet) {
            connectionType = .ethernet
        } else {
            connectionType = .unknown
        }
    }
    
    deinit {
        monitor.cancel()
    }
}

// MARK: - Location Service Manager
final class LocationManager: NSObject, ObservableObject {
    @Published var location: CLLocation?
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined
    @Published var locationError: LocationError?
    
    private let locationManager = CLLocationManager()
    
    enum LocationError: LocalizedError {
        case denied
        case restricted
        case unavailable
        case timeout
        
        var errorDescription: String? {
            switch self {
            case .denied:
                return "Acceso a ubicación denegado"
            case .restricted:
                return "Acceso a ubicación restringido"
            case .unavailable:
                return "Ubicación no disponible"
            case .timeout:
                return "Tiempo de espera agotado para obtener ubicación"
            }
        }
    }
    
    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
    }
    
    func requestLocation() {
        switch authorizationStatus {
        case .notDetermined:
            locationManager.requestWhenInUseAuthorization()
        case .authorizedWhenInUse, .authorizedAlways:
            locationManager.requestLocation()
        default:
            locationError = .denied
        }
    }
    
    func startUpdatingLocation() {
        guard authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways else {
            locationError = .denied
            return
        }
        locationManager.startUpdatingLocation()
    }
    
    func stopUpdatingLocation() {
        locationManager.stopUpdatingLocation()
    }
}

extension LocationManager: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        location = locations.last
        locationError = nil
    }
    
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        if let clError = error as? CLError {
            switch clError.code {
            case .denied:
                locationError = .denied
            case .locationUnknown:
                locationError = .unavailable
            case .network:
                locationError = .timeout
            default:
                locationError = .unavailable
            }
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didChangeAuthorization status: CLAuthorizationStatus) {
        authorizationStatus = status
    }
}

// MARK: - Biometric Authentication Manager
import LocalAuthentication

final class BiometricAuthManager: ObservableObject {
    @Published var biometricType: LABiometryType = .none
    @Published var isAvailable = false
    @Published var lastAuthenticationDate: Date?
    
    private let context = LAContext()
    
    init() {
        updateBiometricAvailability()
    }
    
    func updateBiometricAvailability() {
        var error: NSError?
        isAvailable = context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error)
        biometricType = context.biometryType
    }
    
    func authenticate(reason: String) async throws -> Bool {
        let context = LAContext()
        
        do {
            let result = try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics,
                localizedReason: reason
            )
            
            if result {
                await MainActor.run {
                    lastAuthenticationDate = Date()
                }
            }
            
            return result
        } catch {
            throw BiometricError.from(error)
        }
    }
    
    enum BiometricError: LocalizedError {
        case notAvailable
        case notEnrolled
        case lockout
        case cancelled
        case failed
        case unknown(Error)
        
        static func from(_ error: Error) -> BiometricError {
            guard let laError = error as? LAError else {
                return .unknown(error)
            }
            
            switch laError.code {
            case .biometryNotAvailable:
                return .notAvailable
            case .biometryNotEnrolled:
                return .notEnrolled
            case .biometryLockout:
                return .lockout
            case .userCancel:
                return .cancelled
            case .authenticationFailed:
                return .failed
            default:
                return .unknown(error)
            }
        }
        
        var errorDescription: String? {
            switch self {
            case .notAvailable:
                return "Autenticación biométrica no disponible"
            case .notEnrolled:
                return "No hay datos biométricos registrados"
            case .lockout:
                return "Autenticación biométrica bloqueada"
            case .cancelled:
                return "Autenticación cancelada por el usuario"
            case .failed:
                return "Autenticación biométrica falló"
            case .unknown(let error):
                return "Error desconocido: \(error.localizedDescription)"
            }
        }
    }
}

// MARK: - File Manager Utilities
final class FileManagerUtility {
    static let shared = FileManagerUtility()
    private let fileManager = FileManager.default
    
    private init() {}
    
    // MARK: - Directory Management
    func getDocumentsDirectory() -> URL {
        fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
    
    func getCachesDirectory() -> URL {
        fileManager.urls(for: .cachesDirectory, in: .userDomainMask)[0]
    }
    
    func createDirectory(at url: URL) throws {
        try fileManager.createDirectory(at: url, withIntermediateDirectories: true)
    }
    
    // MARK: - File Operations
    func saveData<T: Codable>(_ data: T, to fileName: String, in directory: SearchPathDirectory = .documentDirectory) throws {
        let url = getURL(for: fileName, in: directory)
        let encoded = try JSONEncoder().encode(data)
        try encoded.write(to: url)
    }
    
    func loadData<T: Codable>(_ type: T.Type, from fileName: String, in directory: SearchPathDirectory = .documentDirectory) throws -> T {
        let url = getURL(for: fileName, in: directory)
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode(type, from: data)
    }
    
    func deleteFile(named fileName: String, in directory: SearchPathDirectory = .documentDirectory) throws {
        let url = getURL(for: fileName, in: directory)
        try fileManager.removeItem(at: url)
    }
    
    func fileExists(named fileName: String, in directory: SearchPathDirectory = .documentDirectory) -> Bool {
        let url = getURL(for: fileName, in: directory)
        return fileManager.fileExists(atPath: url.path)
    }
    
    private func getURL(for fileName: String, in directory: SearchPathDirectory) -> URL {
        let directory = fileManager.urls(for: directory, in: .userDomainMask)[0]
        return directory.appendingPathComponent(fileName)
    }
    
    // MARK: - Cache Management
    func calculateCacheSize() -> Int64 {
        let cacheURL = getCachesDirectory()
        guard let enumerator = fileManager.enumerator(at: cacheURL, includingPropertiesForKeys: [.fileSizeKey]) else {
            return 0
        }
        
        var totalSize: Int64 = 0
        
        for case let fileURL as URL in enumerator {
            guard let resourceValues = try? fileURL.resourceValues(forKeys: [.fileSizeKey]),
                  let fileSize = resourceValues.fileSize else {
                continue
            }
            totalSize += Int64(fileSize)
        }
        
        return totalSize
    }
    
    func clearCache() throws {
        let cacheURL = getCachesDirectory()
        let contents = try fileManager.contentsOfDirectory(at: cacheURL, includingPropertiesForKeys: nil)
        
        for fileURL in contents {
            try fileManager.removeItem(at: fileURL)
        }
    }
}

// MARK: - Device Information Utility
final class DeviceInfoUtility {
    static let shared = DeviceInfoUtility()
    
    private init() {}
    
    var deviceModel: String {
        var systemInfo = utsname()
        uname(&systemInfo)
        
        let modelCode = withUnsafePointer(to: &systemInfo.machine) {
            $0.withMemoryRebound(to: CChar.self, capacity: 1) {
                ptr in String.init(validatingUTF8: ptr)
            }
        }
        
        return modelCode ?? UIDevice.current.model
    }
    
    var deviceName: String {
        UIDevice.current.name
    }
    
    var systemVersion: String {
        UIDevice.current.systemVersion
    }
    
    var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "Unknown"
    }
    
    var buildNumber: String {
        Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "Unknown"
    }
    
    var bundleIdentifier: String {
        Bundle.main.bundleIdentifier ?? "Unknown"
    }
    
    var screenSize: CGSize {
        UIScreen.main.bounds.size
    }
    
    var availableMemory: UInt64 {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size) / 4
        
        let kerr: kern_return_t = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        
        if kerr == KERN_SUCCESS {
            return info.resident_size
        } else {
            return 0
        }
    }
    
    var deviceInfo: [String: Any] {
        [
            "deviceModel": deviceModel,
            "deviceName": deviceName,
            "systemVersion": systemVersion,
            "appVersion": appVersion,
            "buildNumber": buildNumber,
            "bundleIdentifier": bundleIdentifier,
            "screenSize": "\(screenSize.width)x\(screenSize.height)",
            "availableMemory": availableMemory
        ]
    }
}

// MARK: - Validation Utilities
struct ValidationUtility {
    
    static func isValidEmail(_ email: String) -> Bool {
        let emailRegex = "^[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
        let emailPredicate = NSPredicate(format: "SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: email)
    }
    
    static func isValidPassword(_ password: String) -> PasswordValidation {
        var issues: [PasswordIssue] = []
        
        if password.count < 8 {
            issues.append(.tooShort)
        }
        
        if !password.contains(where: { $0.isUppercase }) {
            issues.append(.missingUppercase)
        }
        
        if !password.contains(where: { $0.islowercase }) {
            issues.append(.missingLowercase)
        }
        
        if !password.contains(where: { $0.isNumber }) {
            issues.append(.missingNumber)
        }
        
        let specialCharacters = CharacterSet(charactersIn: "!@#$%^&*()_+-=[]{}|;:,.<>?")
        if password.rangeOfCharacter(from: specialCharacters) == nil {
            issues.append(.missingSpecialCharacter)
        }
        
        return PasswordValidation(isValid: issues.isEmpty, issues: issues)
    }
    
    static func isValidPhoneNumber(_ phoneNumber: String) -> Bool {
        let phoneRegex = "^[+]?[0-9]{10,15}$"
        let phonePredicate = NSPredicate(format: "SELF MATCHES %@", phoneRegex)
        return phonePredicate.evaluate(with: phoneNumber.replacingOccurrences(of: " ", with: ""))
    }
    
    static func sanitizeInput(_ input: String) -> String {
        // Remove potentially dangerous characters
        let allowedCharacterSet = CharacterSet.alphanumerics
            .union(.whitespaces)
            .union(CharacterSet(charactersIn: ".-_@()[]{}"))
        
        return String(input.unicodeScalars.filter { allowedCharacterSet.contains($0) })
    }
    
    struct PasswordValidation {
        let isValid: Bool
        let issues: [PasswordIssue]
        
        var strengthScore: Double {
            let maxIssues = PasswordIssue.allCases.count
            let currentIssues = issues.count
            return Double(maxIssues - currentIssues) / Double(maxIssues)
        }
        
        var strengthText: String {
            switch strengthScore {
            case 0.8...1.0: return "Muy Fuerte"
            case 0.6..<0.8: return "Fuerte"
            case 0.4..<0.6: return "Moderada"
            case 0.2..<0.4: return "Débil"
            default: return "Muy Débil"
            }
        }
        
        var strengthColor: Color {
            switch strengthScore {
            case 0.8...1.0: return .green
            case 0.6..<0.8: return .blue
            case 0.4..<0.6: return .orange
            case 0.2..<0.4: return .red
            default: return .red
            }
        }
    }
    
    enum PasswordIssue: CaseIterable {
        case tooShort
        case missingUppercase
        case missingLowercase
        case missingNumber
        case missingSpecialCharacter
        
        var description: String {
            switch self {
            case .tooShort:
                return "Debe tener al menos 8 caracteres"
            case .missingUppercase:
                return "Debe contener al menos una letra mayúscula"
            case .missingLowercase:
                return "Debe contener al menos una letra minúscula"
            case .missingNumber:
                return "Debe contener al menos un número"
            case .missingSpecialCharacter:
                return "Debe contener al menos un carácter especial"
            }
        }
    }
}

// MARK: - Date Utilities
extension Date {
    func timeAgoDisplay() -> String {
        let now = Date()
        let components = Calendar.current.dateComponents([.second, .minute, .hour, .day, .month, .year], from: self, to: now)
        
        if let years = components.year, years > 0 {
            return years == 1 ? "hace 1 año" : "hace \(years) años"
        }
        
        if let months = components.month, months > 0 {
            return months == 1 ? "hace 1 mes" : "hace \(months) meses"
        }
        
        if let days = components.day, days > 0 {
            return days == 1 ? "hace 1 día" : "hace \(days) días"
        }
        
        if let hours = components.hour, hours > 0 {
            return hours == 1 ? "hace 1 hora" : "hace \(hours) horas"
        }
        
        if let minutes = components.minute, minutes > 0 {
            return minutes == 1 ? "hace 1 minuto" : "hace \(minutes) minutos"
        }
        
        return "ahora"
    }
    
    func isToday() -> Bool {
        Calendar.current.isDateInToday(self)
    }
    
    func isYesterday() -> Bool {
        Calendar.current.isDateInYesterday(self)
    }
    
    func startOfDay() -> Date {
        Calendar.current.startOfDay(for: self)
    }
    
    func endOfDay() -> Date {
        var components = DateComponents()
        components.day = 1
        components.second = -1
        return Calendar.current.date(byAdding: components, to: startOfDay()) ?? self
    }
}

// MARK: - String Extensions
extension String {
    func truncated(to length: Int, trailing: String = "...") -> String {
        if self.count > length {
            return String(self.prefix(length)) + trailing
        } else {
            return self
        }
    }
    
    func initials() -> String {
        return self.components(separatedBy: " ")
            .compactMap { $0.first }
            .map { String($0).uppercased() }
            .joined()
    }
    
    func isValidURL() -> Bool {
        guard let url = URL(string: self) else { return false }
        return UIApplication.shared.canOpenURL(url)
    }
    
    func masked() -> String {
        guard count > 4 else { return self }
        let start = String(prefix(2))
        let end = String(suffix(2))
        let middle = String(repeating: "*", count: count - 4)
        return start + middle + end
    }
}

// MARK: - Color Extensions
extension Color {
    static let omegaPrimary = Color("OmegaPrimary")
    static let omegaSecondary = Color("OmegaSecondary")
    static let omegaAccent = Color("OmegaAccent")
    static let omegaBackground = Color("OmegaBackground")
    static let omegaSurface = Color("OmegaSurface")
    
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }
        
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Custom Modifiers
struct CardModifier: ViewModifier {
    let padding: CGFloat
    let cornerRadius: CGFloat
    let shadowRadius: CGFloat
    
    init(padding: CGFloat = 16, cornerRadius: CGFloat = 12, shadowRadius: CGFloat = 4) {
        self.padding = padding
        self.cornerRadius = cornerRadius
        self.shadowRadius = shadowRadius
    }
    
    func body(content: Content) -> some View {
        content
            .padding(padding)
            .background(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .fill(Color(.systemBackground))
                    .shadow(color: .black.opacity(0.1), radius: shadowRadius, x: 0, y: 2)
            )
    }
}

struct LoadingModifier: ViewModifier {
    let isLoading: Bool
    
    func body(content: Content) -> some View {
        ZStack {
            content
                .opacity(isLoading ? 0.6 : 1.0)
                .disabled(isLoading)
            
            if isLoading {
                ProgressView()
                    .scaleEffect(1.2)
                    .progressViewStyle(CircularProgressViewStyle(tint: .blue))
            }
        }
    }
}

extension View {
    func cardStyle(padding: CGFloat = 16, cornerRadius: CGFloat = 12, shadowRadius: CGFloat = 4) -> some View {
        modifier(CardModifier(padding: padding, cornerRadius: cornerRadius, shadowRadius: shadowRadius))
    }
    
    func loading(_ isLoading: Bool) -> some View {
        modifier(LoadingModifier(isLoading: isLoading))
    }
}

// MARK: - Environment Values
struct AppThemeKey: EnvironmentKey {
    static let defaultValue = AppTheme.default
}

extension EnvironmentValues {
    var appTheme: AppTheme {
        get { self[AppThemeKey.self] }
        set { self[AppThemeKey.self] = newValue }
    }
}

struct AppTheme {
    let primaryColor: Color
    let secondaryColor: Color
    let backgroundColor: Color
    let textColor: Color
    let cornerRadius: CGFloat
    
    static let `default` = AppTheme(
        primaryColor: .blue,
        secondaryColor: .gray,
        backgroundColor: Color(.systemBackground),
        textColor: Color(.label),
        cornerRadius: 12
    )
    
    static let dark = AppTheme(
        primaryColor: .blue,
        secondaryColor: .gray,
        backgroundColor: .black,
        textColor: .white,
        cornerRadius: 12
    )
}

// MARK: - Custom Preference Keys
struct ScrollOffsetPreferenceKey: PreferenceKey {
    static var defaultValue: CGFloat = 0
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = nextValue()
    }
}

struct SizePreferenceKey: PreferenceKey {
    static var defaultValue: CGSize = .zero
    static func reduce(value: inout CGSize, nextValue: () -> CGSize) {
        value = nextValue()
    }
}

// MARK: - Error Handling Utilities
final class ErrorHandler: ObservableObject {
    @Published var currentError: ErrorDisplayModel?
    
    func handle(_ error: Error, context: String = "") {
        let displayModel = ErrorDisplayModel(
            title: "Error",
            message: error.localizedDescription,
            context: context,
            error: error
        )
        
        DispatchQueue.main.async {
            self.currentError = displayModel
        }
    }
    
    func clearError() {
        currentError = nil
    }
}

struct ErrorDisplayModel: Identifiable {
    let id = UUID()
    let title: String
    let message: String
    let context: String
    let error: Error
    let timestamp = Date()
}

// MARK: - Threading Utilities
@MainActor
final class MainActorUtility {
    static func run<T>(_ block: @MainActor () throws -> T) rethrows -> T {
        return try block()
    }
    
    static func async<T>(_ block: @escaping @MainActor () async throws -> T) -> Task<T, Error> {
        return Task { @MainActor in
            return try await block()
        }
    }
}

// MARK: - Debouncer Utility
final class Debouncer {
    private let timeInterval: TimeInterval
    private var timer: Timer?
    
    init(timeInterval: TimeInterval) {
        self.timeInterval = timeInterval
    }
    
    func debounce(action: @escaping () -> Void) {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: timeInterval, repeats: false) { _ in
            action()
        }
    }
    
    deinit {
        timer?.invalidate()
    }
}

// MARK: - Feature Flag Manager
final class FeatureFlagManager: ObservableObject {
    @Published private var flags: [String: Bool] = [:]
    
    private let userDefaults = UserDefaults.standard
    private let remoteConfig: RemoteConfigProtocol?
    
    init(remoteConfig: RemoteConfigProtocol? = nil) {
        self.remoteConfig = remoteConfig
        loadFlags()
    }
    
    func isEnabled(_ flag: FeatureFlag) -> Bool {
        return flags[flag.rawValue] ?? flag.defaultValue
    }
    
    func setFlag(_ flag: FeatureFlag, enabled: Bool) {
        flags[flag.rawValue] = enabled
        userDefaults.set(enabled, forKey: "feature_flag_\(flag.rawValue)")
    }
    
    private func loadFlags() {
        for flag in FeatureFlag.allCases {
            let key = "feature_flag_\(flag.rawValue)"
            if userDefaults.object(forKey: key) != nil {
                flags[flag.rawValue] = userDefaults.bool(forKey: key)
            } else {
                flags[flag.rawValue] = flag.defaultValue
            }
        }
    }
    
    func refreshFromRemote() async {
        guard let remoteConfig = remoteConfig else { return }
        
        do {
            let remoteFlags = try await remoteConfig.fetchFlags()
            
            await MainActor.run {
                for (key, value) in remoteFlags {
                    flags[key] = value
                }
            }
        } catch {
            print("Failed to fetch remote feature flags: \(error)")
        }
    }
}

enum FeatureFlag: String, CaseIterable {
    case biometricAuth = "biometric_auth"
    case advancedAnalytics = "advanced_analytics"
    case experimentalFeatures = "experimental_features"
    case pushNotifications = "push_notifications"
    case darkMode = "dark_mode"
    
    var defaultValue: Bool {
        switch self {
        case .biometricAuth, .advancedAnalytics, .pushNotifications, .darkMode:
            return true
        case .experimentalFeatures:
            return false
        }
    }
}

protocol RemoteConfigProtocol {
    func fetchFlags() async throws -> [String: Bool]
}

// MARK: - Memory Management Utilities
final class MemoryMonitor: ObservableObject {
    @Published var memoryUsage: Double = 0.0
    @Published var memoryPressure: MemoryPressure = .normal
    
    enum MemoryPressure {
        case normal, warning, critical
        
        var color: Color {
            switch self {
            case .normal: return .green
            case .warning: return .orange
            case .critical: return .red
            }
        }
        
        var description: String {
            switch self {
            case .normal: return "Normal"
            case .warning: return "Advertencia"
            case .critical: return "Crítico"
            }
        }
    }
    
    private var timer: Timer?
    
    init() {
        startMonitoring()
    }
    
    private func startMonitoring() {
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.updateMemoryUsage()
        }
    }
    
    private func updateMemoryUsage() {
        let usage = getMemoryUsage()
        
        DispatchQueue.main.async {
            self.memoryUsage = usage
            self.memoryPressure = self.determineMemoryPressure(usage)
        }
    }
    
    private func getMemoryUsage() -> Double {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size) / 4
        
        let kerr = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        
        guard kerr == KERN_SUCCESS else { return 0.0 }
        
        let usedMemory = Double(info.resident_size)
        let totalMemory = Double(ProcessInfo.processInfo.physicalMemory)
        
        return usedMemory / totalMemory
    }
    
    private func determineMemoryPressure(_ usage: Double) -> MemoryPressure {
        switch usage {
        case 0.0..<0.7:
            return .normal
        case 0.7..<0.9:
            return .warning
        default:
            return .critical
        }
    }
    
    deinit {
        timer?.invalidate()
    }
}
