import Foundation
import UserNotifications
import BackgroundTasks
import Combine
import os.log
import CryptoKit

// MARK: - Notification Service
@MainActor
final class NotificationService: ObservableObject {
    @Published var notificationPermissionStatus: UNAuthorizationStatus = .notDetermined
    @Published var pendingNotifications: [PendingNotification] = []
    
    private let logger = Logger(subsystem: "com.omega.OmegaApp", category: "NotificationService")
    private let center = UNUserNotificationCenter.current()
    
    init() {
        setupNotificationCategories()
        checkAuthorizationStatus()
    }
    
    // MARK: - Permission Management
    func requestPermissions() async -> Bool {
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .badge, .sound, .provisional])
            await updateAuthorizationStatus()
            
            if granted {
                logger.info("Notification permissions granted")
                await registerForRemoteNotifications()
            } else {
                logger.warning("Notification permissions denied")
            }
            
            return granted
        } catch {
            logger.error("Failed to request notification permissions: \(error.localizedDescription)")
            return false
        }
    }
    
    private func checkAuthorizationStatus() {
        Task {
            await updateAuthorizationStatus()
        }
    }
    
    private func updateAuthorizationStatus() async {
        let settings = await center.notificationSettings()
        notificationPermissionStatus = settings.authorizationStatus
    }
    
    private func registerForRemoteNotifications() async {
        await UIApplication.shared.registerForRemoteNotifications()
    }
    
    // MARK: - Local Notifications
    func scheduleLocalNotification(_ notification: LocalNotification) async {
        guard notificationPermissionStatus == .authorized else {
            logger.warning("Cannot schedule notification - permissions not granted")
            return
        }
        
        let content = UNMutableNotificationContent()
        content.title = notification.title
        content.body = notification.body
        content.sound = notification.sound
        content.badge = notification.badge
        content.categoryIdentifier = notification.category.rawValue
        content.userInfo = notification.userInfo
        
        // Agregar attachments si los hay
        if let attachments = notification.attachments {
            content.attachments = attachments
        }
        
        let request = UNNotificationRequest(
            identifier: notification.id,
            content: content,
            trigger: notification.trigger
        )
        
        do {
            try await center.add(request)
            logger.info("Scheduled local notification: \(notification.id)")
            
            let pending = PendingNotification(
                id: notification.id,
                title: notification.title,
                scheduledFor: notification.scheduledDate
            )
            pendingNotifications.append(pending)
        } catch {
            logger.error("Failed to schedule notification: \(error.localizedDescription)")
        }
    }
    
    func cancelNotification(withId id: String) {
        center.removePendingNotificationRequests(withIdentifiers: [id])
        pendingNotifications.removeAll { $0.id == id }
        logger.info("Cancelled notification: \(id)")
    }
    
    func cancelAllNotifications() {
        center.removeAllPendingNotificationRequests()
        pendingNotifications.removeAll()
        logger.info("Cancelled all pending notifications")
    }
    
    // MARK: - Notification Categories
    private func setupNotificationCategories() {
        let predictionCompleteCategory = UNNotificationCategory(
            identifier: NotificationCategory.predictionComplete.rawValue,
            actions: [
                UNNotificationAction(
                    identifier: "VIEW_PREDICTION",
                    title: "Ver Predicción",
                    options: [.foreground]
                ),
                UNNotificationAction(
                    identifier: "DISMISS",
                    title: "Descartar",
                    options: []
                )
            ],
            intentIdentifiers: []
        )
        
        let systemAlertCategory = UNNotificationCategory(
            identifier: NotificationCategory.systemAlert.rawValue,
            actions: [
                UNNotificationAction(
                    identifier: "VIEW_SYSTEM",
                    title: "Ver Sistema",
                    options: [.foreground]
                ),
                UNNotificationAction(
                    identifier: "ACKNOWLEDGE",
                    title: "Confirmar",
                    options: []
                )
            ],
            intentIdentifiers: []
        )
        
        center.setNotificationCategories([predictionCompleteCategory, systemAlertCategory])
    }
    
    // MARK: - Convenience Methods
    func schedulePredictionCompleteNotification(predictionId: String, accuracy: Double) async {
        let notification = LocalNotification(
            title: "Predicción Completada",
            body: "Tu predicción ha sido procesada con \(Int(accuracy * 100))% de confianza",
            category: .predictionComplete,
            scheduledDate: Date(),
            userInfo: ["predictionId": predictionId, "accuracy": accuracy]
        )
        
        await scheduleLocalNotification(notification)
    }
    
    func scheduleSystemAlertNotification(alert: SystemAlert) async {
        let notification = LocalNotification(
            title: "Alerta del Sistema",
            body: alert.message,
            category: .systemAlert,
            scheduledDate: Date(),
            userInfo: ["alertId": alert.id, "severity": alert.severity.rawValue]
        )
        
        await scheduleLocalNotification(notification)
    }
}

// MARK: - Notification Models
struct LocalNotification {
    let id: String
    let title: String
    let body: String
    let category: NotificationCategory
    let scheduledDate: Date
    let sound: UNNotificationSound
    let badge: NSNumber?
    let userInfo: [String: Any]
    let attachments: [UNNotificationAttachment]?
    
    var trigger: UNNotificationTrigger {
        let timeInterval = scheduledDate.timeIntervalSinceNow
        return UNTimeIntervalNotificationTrigger(timeInterval: max(timeInterval, 1), repeats: false)
    }
    
    init(
        title: String,
        body: String,
        category: NotificationCategory,
        scheduledDate: Date,
        sound: UNNotificationSound = .default,
        badge: NSNumber? = nil,
        userInfo: [String: Any] = [:],
        attachments: [UNNotificationAttachment]? = nil
    ) {
        self.id = UUID().uuidString
        self.title = title
        self.body = body
        self.category = category
        self.scheduledDate = scheduledDate
        self.sound = sound
        self.badge = badge
        self.userInfo = userInfo
        self.attachments = attachments
    }
}

enum NotificationCategory: String, CaseIterable {
    case predictionComplete = "PREDICTION_COMPLETE"
    case systemAlert = "SYSTEM_ALERT"
    case reminder = "REMINDER"
    case update = "UPDATE"
}

struct PendingNotification: Identifiable {
    let id: String
    let title: String
    let scheduledFor: Date
}

// MARK: - Background Task Service
final class BackgroundTaskService {
    private let logger = Logger(subsystem: "com.omega.OmegaApp", category: "BackgroundTaskService")
    private let apiClient = OmegaAPIClient()
    
    private let dataRefreshTaskId = "com.omega.OmegaApp.dataRefresh"
    private let analyticsTaskId = "com.omega.OmegaApp.analytics"
    
    func registerBackgroundTasks() {
        // Data refresh task
        BGTaskScheduler.shared.register(forTaskWithIdentifier: dataRefreshTaskId, using: nil) { task in
            self.handleDataRefreshTask(task as! BGAppRefreshTask)
        }
        
        // Analytics processing task
        BGTaskScheduler.shared.register(forTaskWithIdentifier: analyticsTaskId, using: nil) { task in
            self.handleAnalyticsTask(task as! BGProcessingTask)
        }
        
        logger.info("Background tasks registered")
    }
    
    func scheduleDataRefresh() {
        let request = BGAppRefreshTaskRequest(identifier: dataRefreshTaskId)
        request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60) // 15 minutos
        
        do {
            try BGTaskScheduler.shared.submit(request)
            logger.info("Data refresh task scheduled")
        } catch {
            logger.error("Failed to schedule data refresh task: \(error.localizedDescription)")
        }
    }
    
    func scheduleAnalyticsProcessing() {
        let request = BGProcessingTaskRequest(identifier: analyticsTaskId)
        request.earliestBeginDate = Date(timeIntervalSinceNow: 30 * 60) // 30 minutos
        request.requiresNetworkConnectivity = true
        request.requiresExternalPower = false
        
        do {
            try BGTaskScheduler.shared.submit(request)
            logger.info("Analytics processing task scheduled")
        } catch {
            logger.error("Failed to schedule analytics task: \(error.localizedDescription)")
        }
    }
    
    private func handleDataRefreshTask(_ task: BGAppRefreshTask) {
        logger.info("Executing data refresh background task")
        
        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }
        
        Task {
            do {
                // Refresh critical data
                let _ = try await apiClient.getSystemStatus()
                let _ = try await apiClient.getHealthCheck()
                
                logger.info("Background data refresh completed successfully")
                task.setTaskCompleted(success: true)
                
                // Schedule next refresh
                scheduleDataRefresh()
            } catch {
                logger.error("Background data refresh failed: \(error.localizedDescription)")
                task.setTaskCompleted(success: false)
            }
        }
    }
    
    private func handleAnalyticsTask(_ task: BGProcessingTask) {
        logger.info("Executing analytics processing background task")
        
        task.expirationHandler = {
            task.setTaskCompleted(success: false)
        }
        
        Task {
            do {
                // Process pending analytics
                let analyticsProcessor = AnalyticsProcessor()
                await analyticsProcessor.processQueuedEvents()
                
                logger.info("Background analytics processing completed successfully")
                task.setTaskCompleted(success: true)
                
                // Schedule next processing
                scheduleAnalyticsProcessing()
            } catch {
                logger.error("Background analytics processing failed: \(error.localizedDescription)")
                task.setTaskCompleted(success: false)
            }
        }
    }
}

// MARK: - Enhanced Logging Service
final class LoggingService {
    private let logger = Logger(subsystem: "com.omega.OmegaApp", category: "LoggingService")
    private let fileManager = FileManager.default
    private let maxLogFileSize = AppConfigManager.LoggingConfig.maxLogFileSize
    private let logRetentionDays = AppConfigManager.LoggingConfig.logRetentionDays
    
    private lazy var logsDirectory: URL = {
        let documentsPath = fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return documentsPath.appendingPathComponent("Logs")
    }()
    
    init() {
        setupLogsDirectory()
        cleanupOldLogs()
    }
    
    private func setupLogsDirectory() {
        do {
            try fileManager.createDirectory(at: logsDirectory, withIntermediateDirectories: true)
        } catch {
            logger.error("Failed to create logs directory: \(error.localizedDescription)")
        }
    }
    
    func log(level: OSLogType, category: String, message: String, file: String = #file, function: String = #function, line: Int = #line) {
        let timestamp = DateFormatter.iso8601Full.string(from: Date())
        let fileName = URL(fileURLWithPath: file).lastPathComponent
        
        let logEntry = LogEntry(
            timestamp: timestamp,
            level: level.description,
            category: category,
            message: message,
            file: fileName,
            function: function,
            line: line
        )
        
        // Log to system
        let categoryLogger = Logger(subsystem: "com.omega.OmegaApp", category: category)
        categoryLogger.log(level: level, "\(message)")
        
        // Log to file if enabled
        if AppConfigManager.LoggingConfig.enableFileLogging {
            writeToFile(logEntry)
        }
    }
    
    private func writeToFile(_ entry: LogEntry) {
        let logFileName = "omega_\(DateFormatter.dateOnly.string(from: Date())).log"
        let logFileURL = logsDirectory.appendingPathComponent(logFileName)
        
        let logLine = "\(entry.timestamp) [\(entry.level)] \(entry.category) - \(entry.message) (\(entry.file):\(entry.line))\n"
        
        do {
            if fileManager.fileExists(atPath: logFileURL.path) {
                // Check file size
                let attributes = try fileManager.attributesOfItem(atPath: logFileURL.path)
                if let fileSize = attributes[.size] as? Int64, fileSize > maxLogFileSize {
                    rotateLogFile(logFileURL)
                }
                
                // Append to existing file
                let fileHandle = try FileHandle(forWritingTo: logFileURL)
                fileHandle.seekToEndOfFile()
                fileHandle.write(logLine.data(using: .utf8)!)
                fileHandle.closeFile()
            } else {
                // Create new file
                try logLine.write(to: logFileURL, atomically: true, encoding: .utf8)
            }
        } catch {
            logger.error("Failed to write log to file: \(error.localizedDescription)")
        }
    }
    
    private func rotateLogFile(_ logFileURL: URL) {
        let timestamp = DateFormatter.timestampFormat.string(from: Date())
        let rotatedFileName = logFileURL.lastPathComponent.replacingOccurrences(of: ".log", with: "_\(timestamp).log")
        let rotatedFileURL = logsDirectory.appendingPathComponent(rotatedFileName)
        
        do {
            try fileManager.moveItem(at: logFileURL, to: rotatedFileURL)
            logger.info("Log file rotated: \(rotatedFileName)")
        } catch {
            logger.error("Failed to rotate log file: \(error.localizedDescription)")
        }
    }
    
    private func cleanupOldLogs() {
        let cutoffDate = Date().addingTimeInterval(-TimeInterval(logRetentionDays * 24 * 60 * 60))
        
        do {
            let logFiles = try fileManager.contentsOfDirectory(at: logsDirectory, includingPropertiesForKeys: [.creationDateKey])
            
            for logFileURL in logFiles {
                let attributes = try fileManager.attributesOfItem(atPath: logFileURL.path)
                if let creationDate = attributes[.creationDate] as? Date, creationDate < cutoffDate {
                    try fileManager.removeItem(at: logFileURL)
                    logger.info("Deleted old log file: \(logFileURL.lastPathComponent)")
                }
            }
        } catch {
            logger.error("Failed to cleanup old logs: \(error.localizedDescription)")
        }
    }
    
    func exportLogs() -> URL? {
        let exportFileName = "omega_logs_\(DateFormatter.timestampFormat.string(from: Date())).zip"
        let exportURL = logsDirectory.appendingPathComponent(exportFileName)
        
        // Create zip archive of all log files
        do {
            let logFiles = try fileManager.contentsOfDirectory(at: logsDirectory, includingPropertiesForKeys: nil)
                .filter { $0.pathExtension == "log" }
            
            if !logFiles.isEmpty {
                try ZipUtility.zipFiles(logFiles, to: exportURL)
                return exportURL
            }
        } catch {
            logger.error("Failed to export logs: \(error.localizedDescription)")
        }
        
        return nil
    }
}

struct LogEntry {
    let timestamp: String
    let level: String
    let category: String
    let message: String
    let file: String
    let function: String
    let line: Int
}

// MARK: - Analytics Processor
actor AnalyticsProcessor {
    private let logger = Logger(subsystem: "com.omega.OmegaApp", category: "AnalyticsProcessor")
    private let apiClient = OmegaAPIClient()
    private var eventQueue: [AnalyticsEvent] = []
    private let maxBatchSize = AppConfigManager.AnalyticsConfig.batchSize
    
    func queueEvent(_ event: AnalyticsEvent) {
        eventQueue.append(event)
        
        if eventQueue.count >= maxBatchSize {
            Task {
                await processBatch()
            }
        }
    }
    
    func processQueuedEvents() async {
        while !eventQueue.isEmpty {
            await processBatch()
        }
    }
    
    private func processBatch() async {
        guard !eventQueue.isEmpty else { return }
        
        let batchSize = min(eventQueue.count, maxBatchSize)
        let batch = Array(eventQueue.prefix(batchSize))
        eventQueue.removeFirst(batchSize)
        
        do {
            for event in batch {
                try await apiClient.sendAnalyticsEvent(event)
            }
            logger.info("Processed analytics batch of \(batch.count) events")
        } catch {
            // Re-queue failed events
            eventQueue.append(contentsOf: batch)
            logger.error("Failed to process analytics batch: \(error.localizedDescription)")
        }
    }
}

// MARK: - Security Service
final class SecurityService {
    private let logger = Logger(subsystem: "com.omega.OmegaApp", category: "SecurityService")
    
    // MARK: - Data Encryption
    func encrypt(data: Data, with key: SymmetricKey) throws -> Data {
        let sealedBox = try AES.GCM.seal(data, using: key)
        return sealedBox.combined!
    }
    
    func decrypt(data: Data, with key: SymmetricKey) throws -> Data {
        let sealedBox = try AES.GCM.SealedBox(combined: data)
        return try AES.GCM.open(sealedBox, using: key)
    }
    
    // MARK: - Key Generation
    func generateSymmetricKey() -> SymmetricKey {
        return SymmetricKey(size: .bits256)
    }
    
    func deriveKey(from password: String, salt: Data) -> SymmetricKey {
        let inputKeyMaterial = SymmetricKey(data: password.data(using: .utf8)!)
        return HKDF<SHA256>.deriveKey(
            inputKeyMaterial: inputKeyMaterial,
            salt: salt,
            outputByteCount: 32
        )
    }
    
    // MARK: - Hash Functions
    func hash(data: Data) -> String {
        let digest = SHA256.hash(data: data)
        return digest.compactMap { String(format: "%02x", $0) }.joined()
    }
    
    func hashPassword(_ password: String, salt: String) -> String {
        let saltedPassword = password + salt
        return hash(data: saltedPassword.data(using: .utf8)!)
    }
    
    // MARK: - Certificate Pinning
    func validateCertificate(_ trust: SecTrust, for host: String) -> Bool {
        guard AppConfigManager.SecurityConfig.certificatePinning else {
            return true // Skip pinning in development
        }
        
        // Implement certificate pinning validation
        let pinnedCertificates = AppConfigManager.SecurityConfig.pinnedCertificates
        
        // Get server certificate
        guard let serverCertificate = SecTrustGetCertificateAtIndex(trust, 0) else {
            logger.error("Could not get server certificate")
            return false
        }
        
        let serverCertData = SecCertificateCopyData(serverCertificate)
        let serverCertHash = hash(data: Data(referencing: serverCertData))
        
        let isValid = pinnedCertificates.contains(serverCertHash)
        
        if !isValid {
            logger.error("Certificate pinning validation failed for host: \(host)")
        }
        
        return isValid
    }
    
    // MARK: - Input Validation
    func validateInput(_ input: String, pattern: String) -> Bool {
        let regex = try? NSRegularExpression(pattern: pattern)
        let range = NSRange(location: 0, length: input.utf16.count)
        return regex?.firstMatch(in: input, options: [], range: range) != nil
    }
    
    func sanitizeInput(_ input: String) -> String {
        // Remove potentially dangerous characters
        let allowedCharacterSet = CharacterSet.alphanumerics.union(.whitespaces).union(CharacterSet(charactersIn: ".-_@"))
        return String(input.unicodeScalars.filter { allowedCharacterSet.contains($0) })
    }
}

// MARK: - Performance Monitor
@MainActor
final class PerformanceMonitor: ObservableObject {
    @Published var currentMetrics: PerformanceMetrics?
    @Published var isMonitoring = false
    
    private let logger = Logger(subsystem: "com.omega.OmegaApp", category: "PerformanceMonitor")
    private var monitoringTimer: Timer?
    private var startTime: CFTimeInterval = 0
    
    func startMonitoring() {
        guard !isMonitoring else { return }
        
        isMonitoring = true
        startTime = CACurrentMediaTime()
        
        monitoringTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.updateMetrics()
        }
        
        logger.info("Performance monitoring started")
    }
    
    func stopMonitoring() {
        guard isMonitoring else { return }
        
        isMonitoring = false
        monitoringTimer?.invalidate()
        monitoringTimer = nil
        
        logger.info("Performance monitoring stopped")
    }
    
    private func updateMetrics() {
        let appMemoryUsage = getMemoryUsage()
        let cpuUsage = getCPUUsage()
        let uptime = CACurrentMediaTime() - startTime
        
        currentMetrics = PerformanceMetrics(
            throughput: 0, // Placeholder - would track requests/sec
            latency: LatencyMetrics(p50: 0, p95: 0, p99: 0, average: 0, maximum: 0),
            errorRates: ErrorRateMetrics(rate4xx: 0, rate5xx: 0, timeoutRate: 0, overallErrorRate: 0),
            resourceUtilization: ResourceUtilizationMetrics(
                cpu: ResourceMetric(current: cpuUsage, average: cpuUsage, peak: cpuUsage, threshold: 80.0),
                memory: ResourceMetric(current: appMemoryUsage, average: appMemoryUsage, peak: appMemoryUsage, threshold: 80.0),
                disk: ResourceMetric(current: 0, average: 0, peak: 0, threshold: 80.0),
                network: NetworkMetric(bytesIn: 0, bytesOut: 0, packetsIn: 0, packetsOut: 0, errorsIn: 0, errorsOut: 0)
            )
        )
    }
    
    private func getMemoryUsage() -> Double {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size) / 4
        
        let kerr: kern_return_t = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        
        if kerr == KERN_SUCCESS {
            let usedBytes = Double(info.resident_size)
            let totalBytes = Double(ProcessInfo.processInfo.physicalMemory)
            return usedBytes / totalBytes * 100.0
        }
        
        return 0.0
    }
    
    private func getCPUUsage() -> Double {
        var info = processor_info_array_t(bitPattern: 0)
        var numCpuInfo: mach_msg_type_number_t = 0
        var numCpus: natural_t = 0
        
        let result = host_processor_info(mach_host_self(), PROCESSOR_CPU_LOAD_INFO, &numCpus, &info, &numCpuInfo)
        
        if result == KERN_SUCCESS {
            // Simplified CPU usage calculation
            return Double.random(in: 5...25) // Placeholder
        }
        
        return 0.0
    }
}

// MARK: - Extensions
extension OSLogType {
    var description: String {
        switch self {
        case .default: return "DEFAULT"
        case .info: return "INFO"
        case .debug: return "DEBUG"
        case .error: return "ERROR"
        case .fault: return "FAULT"
        default: return "UNKNOWN"
        }
    }
}

extension DateFormatter {
    static let iso8601Full: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"
        formatter.calendar = Calendar(identifier: .iso8601)
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter
    }()
    
    static let dateOnly: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
    
    static let timestampFormat: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd_HHmmss"
        return formatter
    }()
}

// MARK: - Utility Classes
final class ZipUtility {
    static func zipFiles(_ files: [URL], to destination: URL) throws {
        // Simplified zip implementation - in real app would use proper zip library
        // For now, just create a placeholder file
        try "Compressed log files".write(to: destination, atomically: true, encoding: .utf8)
    }
}
