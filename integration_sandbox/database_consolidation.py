#!/usr/bin/env python3
"""
OMEGA AI Database Consolidation Script
Consolidates 350+ scattered databases into unified architecture
Based on Agent Expert recommendations
"""

import sqlite3
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConsolidator:
    """Consolidates scattered databases into unified architecture"""
    
    def __init__(self):
        self.main_db_path = "results/omega_unified.db"
        self.backup_dir = Path("database_backups")
        self.logs_dirs = []
        self.scattered_dbs = []
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
    def discover_scattered_databases(self) -> List[Path]:
        """Discover all scattered database files"""
        logger.info("🔍 Discovering scattered databases...")
        
        # Find all log directories
        for item in Path('.').iterdir():
            if item.is_dir() and 'logs' in item.name:
                self.logs_dirs.append(item)
        
        # Find database files
        db_files = []
        patterns = ['*.db', '*.sqlite', '*.sqlite3']
        
        for pattern in patterns:
            # Root directory
            db_files.extend(Path('.').glob(pattern))
            
            # Results directory
            results_dir = Path('results')
            if results_dir.exists():
                db_files.extend(results_dir.glob(pattern))
            
            # Logs directories
            for logs_dir in self.logs_dirs:
                db_files.extend(logs_dir.glob(f"**/{pattern}"))
        
        # Remove duplicates and filter out main databases
        unique_dbs = list(set(db_files))
        filtered_dbs = [
            db for db in unique_dbs 
            if 'unified' not in db.name and 'main' not in db.name
        ]
        
        logger.info(f"📊 Found {len(filtered_dbs)} scattered database files")
        return filtered_dbs
    
    def backup_existing_databases(self, db_files: List[Path]):
        """Create backup of existing databases"""
        logger.info("💾 Creating backups of existing databases...")
        
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"db_backup_{backup_timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        for db_file in db_files:
            try:
                backup_file = backup_path / f"{db_file.stem}_{backup_timestamp}{db_file.suffix}"
                shutil.copy2(db_file, backup_file)
                logger.info(f"✅ Backed up: {db_file} -> {backup_file}")
            except Exception as e:
                logger.error(f"❌ Error backing up {db_file}: {e}")
        
        logger.info(f"✅ Backups completed in: {backup_path}")
        return backup_path
    
    def create_unified_database(self):
        """Create new unified database schema"""
        logger.info("🏗️ Creating unified database schema...")
        
        # Remove existing unified database if exists
        if Path(self.main_db_path).exists():
            Path(self.main_db_path).unlink()
        
        # Create new unified database
        conn = sqlite3.connect(self.main_db_path)
        cursor = conn.cursor()
        
        # Main predictions table
        cursor.execute("""
        CREATE TABLE predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sorteo_fecha DATE,
            sorteo_numero INTEGER,
            model_source VARCHAR(50),
            combination TEXT,
            confidence REAL,
            consensus_score REAL,
            rank_position INTEGER,
            metadata_json TEXT
        )
        """)
        
        # System metrics table
        cursor.execute("""
        CREATE TABLE system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            component VARCHAR(50),
            metric_name VARCHAR(100),
            metric_value REAL,
            metric_unit VARCHAR(20),
            additional_info TEXT
        )
        """)
        
        # Model performance table
        cursor.execute("""
        CREATE TABLE model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            model_name VARCHAR(50),
            accuracy_score REAL,
            execution_time REAL,
            memory_usage_mb REAL,
            prediction_count INTEGER,
            success_rate REAL,
            configuration_json TEXT
        )
        """)
        
        # Filter configurations table
        cursor.execute("""
        CREATE TABLE filter_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            filter_name VARCHAR(50),
            configuration_json TEXT,
            applied_count INTEGER,
            success_rate REAL,
            is_active BOOLEAN DEFAULT 1
        )
        """)
        
        # Sorteo results table (historical data)
        cursor.execute("""
        CREATE TABLE sorteo_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sorteo_fecha DATE UNIQUE,
            sorteo_numero INTEGER,
            winning_numbers TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Scheduler logs table
        cursor.execute("""
        CREATE TABLE scheduler_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action VARCHAR(50),
            status VARCHAR(20),
            details TEXT,
            execution_time REAL
        )
        """)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX idx_predictions_timestamp ON predictions(timestamp)",
            "CREATE INDEX idx_predictions_sorteo_fecha ON predictions(sorteo_fecha)",
            "CREATE INDEX idx_predictions_model_source ON predictions(model_source)",
            "CREATE INDEX idx_system_metrics_component ON system_metrics(component)",
            "CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp)",
            "CREATE INDEX idx_model_performance_name ON model_performance(model_name)",
            "CREATE INDEX idx_sorteo_results_fecha ON sorteo_results(sorteo_fecha)",
            "CREATE INDEX idx_scheduler_logs_timestamp ON scheduler_logs(timestamp)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Unified database created: {self.main_db_path}")
    
    def migrate_data_from_scattered_dbs(self, db_files: List[Path]):
        """Migrate data from scattered databases to unified database"""
        logger.info("📦 Migrating data from scattered databases...")
        
        unified_conn = sqlite3.connect(self.main_db_path)
        unified_cursor = unified_conn.cursor()
        
        migrated_count = 0
        error_count = 0
        
        for db_file in db_files:
            try:
                logger.info(f"🔄 Processing: {db_file}")
                
                # Connect to source database
                source_conn = sqlite3.connect(db_file)
                source_cursor = source_conn.cursor()
                
                # Get table names
                source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = source_cursor.fetchall()
                
                for table_tuple in tables:
                    table_name = table_tuple[0]
                    
                    if table_name.startswith('sqlite_'):
                        continue  # Skip system tables
                    
                    try:
                        # Get table data
                        source_cursor.execute(f"SELECT * FROM {table_name}")
                        rows = source_cursor.fetchall()
                        
                        # Get column names
                        source_cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in source_cursor.fetchall()]
                        
                        # Migrate based on table content/name
                        self._migrate_table_data(
                            unified_cursor, table_name, columns, rows, db_file
                        )
                        
                        migrated_count += len(rows)
                        
                    except Exception as e:
                        logger.error(f"❌ Error migrating table {table_name} from {db_file}: {e}")
                        error_count += 1
                
                source_conn.close()
                
            except Exception as e:
                logger.error(f"❌ Error processing database {db_file}: {e}")
                error_count += 1
        
        unified_conn.commit()
        unified_conn.close()
        
        logger.info(f"✅ Migration completed: {migrated_count} records migrated, {error_count} errors")
    
    def _migrate_table_data(self, cursor, table_name: str, columns: List[str], 
                          rows: List[tuple], source_file: Path):
        """Migrate table data to appropriate unified table"""
        
        # Determine target table based on content
        if 'prediction' in table_name.lower() or 'combination' in table_name.lower():
            self._migrate_to_predictions(cursor, rows, source_file)
        
        elif 'metric' in table_name.lower() or 'performance' in table_name.lower():
            self._migrate_to_metrics(cursor, rows, source_file, table_name)
        
        elif 'filter' in table_name.lower():
            self._migrate_to_filters(cursor, rows, source_file, table_name)
        
        else:
            # Store as generic system metrics
            self._migrate_to_generic_metrics(cursor, table_name, columns, rows, source_file)
    
    def _migrate_to_predictions(self, cursor, rows: List[tuple], source_file: Path):
        """Migrate to predictions table"""
        for row in rows:
            try:
                cursor.execute("""
                INSERT INTO predictions (
                    sorteo_fecha, model_source, combination, confidence, 
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().date(),  # Default date
                    source_file.stem,       # Model source from file name
                    str(row),              # Combination data
                    0.5,                   # Default confidence
                    json.dumps({"migrated_from": str(source_file)})
                ))
            except Exception as e:
                logger.error(f"Error inserting prediction: {e}")
    
    def _migrate_to_metrics(self, cursor, rows: List[tuple], source_file: Path, table_name: str):
        """Migrate to system metrics table"""
        for row in rows:
            try:
                cursor.execute("""
                INSERT INTO system_metrics (
                    component, metric_name, metric_value, additional_info
                ) VALUES (?, ?, ?, ?)
                """, (
                    source_file.stem,  # Component name
                    table_name,        # Metric name
                    len(str(row)),     # Simple metric value
                    json.dumps({"original_data": str(row), "source": str(source_file)})
                ))
            except Exception as e:
                logger.error(f"Error inserting metric: {e}")
    
    def _migrate_to_filters(self, cursor, rows: List[tuple], source_file: Path, table_name: str):
        """Migrate to filter configurations table"""
        for row in rows:
            try:
                cursor.execute("""
                INSERT INTO filter_configurations (
                    filter_name, configuration_json, applied_count
                ) VALUES (?, ?, ?)
                """, (
                    f"{source_file.stem}_{table_name}",
                    json.dumps({"data": str(row), "source": str(source_file)}),
                    1
                ))
            except Exception as e:
                logger.error(f"Error inserting filter config: {e}")
    
    def _migrate_to_generic_metrics(self, cursor, table_name: str, columns: List[str], 
                                  rows: List[tuple], source_file: Path):
        """Migrate unknown data to generic metrics"""
        for row in rows:
            try:
                cursor.execute("""
                INSERT INTO system_metrics (
                    component, metric_name, additional_info
                ) VALUES (?, ?, ?)
                """, (
                    source_file.stem,
                    f"{table_name}_data",
                    json.dumps({
                        "columns": columns,
                        "data": str(row),
                        "source": str(source_file)
                    })
                ))
            except Exception as e:
                logger.error(f"Error inserting generic data: {e}")
    
    def cleanup_scattered_databases(self, db_files: List[Path], backup_path: Path):
        """Clean up scattered databases after successful migration"""
        logger.info("🧹 Cleaning up scattered databases...")
        
        # Create cleanup log
        cleanup_log_path = backup_path / "cleanup_log.txt"
        
        with open(cleanup_log_path, 'w') as log_file:
            log_file.write(f"Database Cleanup Log - {datetime.now().isoformat()}\n")
            log_file.write("="*50 + "\n\n")
            
            removed_count = 0
            error_count = 0
            
            for db_file in db_files:
                try:
                    if db_file.exists():
                        db_file.unlink()
                        log_file.write(f"REMOVED: {db_file}\n")
                        removed_count += 1
                        logger.info(f"🗑️ Removed: {db_file}")
                    else:
                        log_file.write(f"NOT_FOUND: {db_file}\n")
                except Exception as e:
                    log_file.write(f"ERROR: {db_file} - {e}\n")
                    error_count += 1
                    logger.error(f"❌ Error removing {db_file}: {e}")
            
            log_file.write(f"\nSUMMARY:\n")
            log_file.write(f"Removed: {removed_count}\n")
            log_file.write(f"Errors: {error_count}\n")
        
        logger.info(f"✅ Cleanup completed: {removed_count} files removed, {error_count} errors")
        logger.info(f"📄 Cleanup log: {cleanup_log_path}")
    
    def verify_unified_database(self):
        """Verify the unified database structure and content"""
        logger.info("🔍 Verifying unified database...")
        
        conn = sqlite3.connect(self.main_db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        verification_report = {
            "database_path": self.main_db_path,
            "tables_count": len(tables),
            "tables": {},
            "total_records": 0
        }
        
        for table_tuple in tables:
            table_name = table_tuple[0]
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            record_count = cursor.fetchone()[0]
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = cursor.fetchall()
            
            verification_report["tables"][table_name] = {
                "record_count": record_count,
                "columns": [col[1] for col in schema],
                "column_count": len(schema)
            }
            
            verification_report["total_records"] += record_count
        
        conn.close()
        
        # Save verification report
        report_path = Path("results/database_verification_report.json")
        with open(report_path, 'w') as f:
            json.dump(verification_report, f, indent=2)
        
        logger.info(f"✅ Verification completed:")
        logger.info(f"   📊 Tables: {verification_report['tables_count']}")
        logger.info(f"   📝 Total records: {verification_report['total_records']}")
        logger.info(f"   📄 Report saved: {report_path}")
        
        return verification_report
    
    def create_database_access_layer(self):
        """Create database access layer for unified database"""
        logger.info("🔧 Creating database access layer...")
        
        access_layer_code = '''#!/usr/bin/env python3
"""
OMEGA AI Unified Database Access Layer
Generated by Database Consolidation Script
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

class OmegaUnifiedDatabase:
    """Unified database access layer for OMEGA AI"""
    
    def __init__(self, db_path: str = "results/omega_unified.db"):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def save_prediction(self, sorteo_fecha: str, model_source: str, 
                       combination: List[int], confidence: float,
                       consensus_score: float = None, rank_position: int = None,
                       metadata: Dict[str, Any] = None):
        """Save prediction to unified database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO predictions (
                    sorteo_fecha, model_source, combination, confidence,
                    consensus_score, rank_position, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                sorteo_fecha,
                model_source,
                json.dumps(combination),
                confidence,
                consensus_score,
                rank_position,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_predictions(self, sorteo_fecha: str = None, model_source: str = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Get predictions from unified database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM predictions WHERE 1=1"
            params = []
            
            if sorteo_fecha:
                query += " AND sorteo_fecha = ?"
                params.append(sorteo_fecha)
            
            if model_source:
                query += " AND model_source = ?"
                params.append(model_source)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            predictions = []
            for row in rows:
                prediction = dict(row)
                if prediction['combination']:
                    prediction['combination'] = json.loads(prediction['combination'])
                if prediction['metadata_json']:
                    prediction['metadata'] = json.loads(prediction['metadata_json'])
                predictions.append(prediction)
            
            return predictions
    
    def save_system_metric(self, component: str, metric_name: str,
                          metric_value: float, metric_unit: str = None,
                          additional_info: Dict[str, Any] = None):
        """Save system metric"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_metrics (
                    component, metric_name, metric_value, metric_unit, additional_info
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                component,
                metric_name,
                metric_value,
                metric_unit,
                json.dumps(additional_info) if additional_info else None
            ))
            conn.commit()
    
    def get_model_performance(self, model_name: str = None, 
                            days: int = 30) -> List[Dict[str, Any]]:
        """Get model performance metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM model_performance 
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(days)
            
            params = []
            if model_name:
                query += " AND model_name = ?"
                params.append(model_name)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Table record counts
            tables = ['predictions', 'system_metrics', 'model_performance', 
                     'filter_configurations', 'sorteo_results', 'scheduler_logs']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Recent predictions count
            cursor.execute("""
                SELECT COUNT(*) FROM predictions 
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            stats['recent_predictions'] = cursor.fetchone()[0]
            
            # Model usage statistics
            cursor.execute("""
                SELECT model_source, COUNT(*) as count
                FROM predictions
                GROUP BY model_source
                ORDER BY count DESC
                LIMIT 5
            """)
            stats['top_models'] = [dict(row) for row in cursor.fetchall()]
            
            return stats

# Global instance
omega_db = OmegaUnifiedDatabase()
'''
        
        access_layer_path = Path("database_access_layer.py")
        with open(access_layer_path, 'w') as f:
            f.write(access_layer_code)
        
        logger.info(f"✅ Database access layer created: {access_layer_path}")
    
    def run_full_consolidation(self):
        """Run complete database consolidation process"""
        logger.info("🚀 Starting full database consolidation...")
        
        # Step 1: Discover scattered databases
        scattered_dbs = self.discover_scattered_databases()
        
        if not scattered_dbs:
            logger.info("ℹ️ No scattered databases found to consolidate")
            return
        
        # Step 2: Create backups
        backup_path = self.backup_existing_databases(scattered_dbs)
        
        # Step 3: Create unified database
        self.create_unified_database()
        
        # Step 4: Migrate data
        self.migrate_data_from_scattered_dbs(scattered_dbs)
        
        # Step 5: Verify unified database
        verification_report = self.verify_unified_database()
        
        # Step 6: Create access layer
        self.create_database_access_layer()
        
        # Step 7: Clean up (optional - commented out for safety)
        # self.cleanup_scattered_databases(scattered_dbs, backup_path)
        
        logger.info("✅ Database consolidation completed successfully!")
        logger.info(f"📊 Unified database: {self.main_db_path}")
        logger.info(f"💾 Backups: {backup_path}")
        logger.info(f"📝 Total records: {verification_report['total_records']}")
        
        return {
            "unified_db": self.main_db_path,
            "backup_path": str(backup_path),
            "verification_report": verification_report
        }

def main():
    """Main execution function"""
    consolidator = DatabaseConsolidator()
    result = consolidator.run_full_consolidation()
    
    print("\n🎯 OMEGA AI Database Consolidation Complete!")
    print("=" * 50)
    print(f"📊 Unified Database: {result['unified_db']}")
    print(f"💾 Backups Location: {result['backup_path']}")
    print(f"📝 Total Records: {result['verification_report']['total_records']}")
    print(f"🗂️ Tables: {result['verification_report']['tables_count']}")
    
    print("\n🔧 Next Steps:")
    print("1. Test the unified database with: python database_access_layer.py")
    print("2. Update API endpoints to use: omega_db.save_prediction()")
    print("3. Update ML models to use: omega_db.get_predictions()")
    print("4. Monitor performance and adjust as needed")

if __name__ == "__main__":
    main()