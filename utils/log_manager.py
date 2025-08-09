# OMEGA_PRO_AI_v10.1/utils/log_manager.py
import os
import glob
import time
import shutil
import gzip
from utils.logger import log_info, log_warning, log_error

def clean_old_logs(days: int = 7, base_dir: str = "logs", dry_run: bool = False) -> None:
    """
    Elimina logs antiguos con verificación de espacio en disco configurable.
    """
    abs_base_dir = os.path.abspath(base_dir)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if not abs_base_dir.startswith(project_root):
        log_warning(f"Directorio de logs fuera del proyecto: {abs_base_dir}")
        if not dry_run:
            log_error("Operación cancelada por seguridad")
            return

    disk_threshold = float(os.getenv("MIN_DISK_SPACE_RATIO", 0.1))
    try:
        stat = shutil.disk_usage(base_dir)
        if stat.free / stat.total < disk_threshold:
            log_warning(f"Espacio en disco bajo ({stat.free / (1024**3):.2f}GB libre, umbral={disk_threshold*100}%)")
    except Exception as e:
        log_error(f"Error verificando espacio en disco: {str(e)}", exc_info=True)

    current_time = time.time()
    threshold = current_time - (days * 86400)
    
    try:
        log_dirs = glob.glob(os.path.join(base_dir, "*"))
        deleted_count = 0
        for log_dir in log_dirs:
            if os.path.isdir(log_dir):
                dir_time = os.path.getmtime(log_dir)
                if dir_time < threshold:
                    if not dry_run and not os.access(log_dir, os.W_OK):
                        log_error(f"No se tienen permisos de escritura para {log_dir}")
                        continue
                    if dry_run:
                        log_info(f"Simulación: se eliminaría {log_dir} (más antiguo que {days} días)")
                        deleted_count += 1
                    else:
                        shutil.rmtree(log_dir)
                        log_info(f"Directorio de logs eliminado: {log_dir} (más antiguo que {days} días)")
                        deleted_count += 1
        
        if dry_run:
            log_info(f"Simulación completa: {deleted_count} directorios serían eliminados")
        else:
            log_info(f"Mantenimiento de logs completado: {deleted_count} directorios eliminados")
    except Exception as e:
        log_error(f"Error inesperado en clean_old_logs: {str(e)}", exc_info=True)

def manage_log_rotation(max_system_size_mb: int = None, max_error_size_mb: int = None, dry_run: bool = False, logger_callback: callable = None) -> None:
    """
    Monitorea y rota logs con compresión opcional y notificación a handlers.
    """
    if max_system_size_mb is None:
        max_system_size_mb = int(os.getenv("MAX_SYSTEM_LOG_MB", 100))
    if max_error_size_mb is None:
        max_error_size_mb = int(os.getenv("MAX_ERROR_LOG_MB", 50))
    
    if max_system_size_mb <= 0 or max_error_size_mb <= 0:
        log_error("Los límites de tamaño de log deben ser positivos")
        return
    
    log_info(f"Monitoreo de logs activado: Sistema={max_system_size_mb}MB, Errores={max_error_size_mb}MB")
    
    try:
        log_dirs = sorted(glob.glob(os.path.join("logs", "*")), key=os.path.getmtime, reverse=True)
        if not log_dirs:
            return
            
        latest_log_dir = log_dirs[0]
        system_log = os.path.join(latest_log_dir, "omega_system.log")
        error_log = os.path.join(latest_log_dir, "omega_errors.log")
        
        rotation_performed = False
        compression_enabled = os.getenv("LOG_COMPRESSION", "false").lower() == "true"
        compression_level = int(os.getenv("LOG_COMPRESSION_LEVEL", 9))
        retention_days = int(os.getenv("LOG_RETENTION_DAYS", 30))
        
        # Clean up old rotated logs
        for rotated_log in glob.glob(f"{latest_log_dir}/*.gz"):
            if os.path.getmtime(rotated_log) < time.time() - (retention_days * 86400):
                if not dry_run:
                    os.remove(rotated_log)
                    log_info(f"Log rotado eliminado: {os.path.basename(rotated_log)}")
                else:
                    log_info(f"Simulación: se eliminaría log rotado {os.path.basename(rotated_log)}")
        
        if os.path.exists(system_log):
            size_mb = os.path.getsize(system_log) / (1024 * 1024)
            if size_mb > max_system_size_mb:
                log_warning(f"Log del sistema excede límite ({size_mb:.2f}MB > {max_system_size_mb}MB)")
                if not dry_run and os.access(system_log, os.W_OK):
                    timestamp = int(time.time())
                    if compression_enabled:
                        new_name = f"{system_log}.{timestamp}.gz"
                        with open(system_log, 'rb') as f_in:
                            with gzip.open(new_name, 'wb', compresslevel=compression_level) as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        os.remove(system_log)
                        log_info(f"Log del sistema rotado y comprimido: {os.path.basename(new_name)}")
                    else:
                        new_name = f"{system_log}.{timestamp}"
                        os.rename(system_log, new_name)
                        log_info(f"Log del sistema rotado: {os.path.basename(new_name)}")
                    rotation_performed = True
                elif not dry_run:
                    log_error(f"No se tienen permisos de escritura para {system_log}")
                else:
                    log_info(f"Simulación: se rotaría log del sistema ({size_mb:.2f}MB)")
        
        if os.path.exists(error_log):
            size_mb = os.path.getsize(error_log) / (1024 * 1024)
            if size_mb > max_error_size_mb:
                log_warning(f"Log de errores excede límite ({size_mb:.2f}MB > {max_error_size_mb}MB)")
                if not dry_run and os.access(error_log, os.W_OK):
                    timestamp = int(time.time())
                    if compression_enabled:
                        new_name = f"{error_log}.{timestamp}.gz"
                        with open(error_log, 'rb') as f_in:
                            with gzip.open(new_name, 'wb', compresslevel=compression_level) as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        os.remove(error_log)
                        log_info(f"Log de errores rotado y comprimido: {os.path.basename(new_name)}")
                    else:
                        new_name = f"{error_log}.{timestamp}"
                        os.rename(error_log, new_name)
                        log_info(f"Log de errores rotado: {os.path.basename(new_name)}")
                    rotation_performed = True
                elif not dry_run:
                    log_error(f"No se tienen permisos de escritura para {error_log}")
                else:
                    log_info(f"Simulación: se rotaría log de errores ({size_mb:.2f}MB)")
        
        if rotation_performed:
            log_info("Rotación de logs completada")
            if logger_callback:
                try:
                    logger_callback()
                    log_info("Handlers de logging actualizados")
                except Exception as e:
                    log_error(f"Error actualizando handlers: {str(e)}", exc_info=True)
        elif dry_run:
            log_info("Simulación completa: no se requirió rotación")
                
    except Exception as e:
        log_error(f"Error en monitoreo de logs: {str(e)}", exc_info=True)

def initialize_logging(dry_run=False, logger_callback=None):
    """
    Inicializa el sistema de logging con tareas de mantenimiento.
    """
    log_info(f"Iniciando mantenimiento de logs (dry_run={dry_run})")
    clean_old_logs(dry_run=dry_run)
    manage_log_rotation(dry_run=dry_run)
    
    if logger_callback:
        try:
            logger_callback()
        except Exception as e:
            log_info(f"⚠️ Error ejecutando logger_callback: {str(e)}")
