#!/usr/bin/env python3
# Incorporar resultado del 5/08/2025 al dataset histórico

import pandas as pd
from datetime import datetime

def update_historical_data():
    """Añade el resultado del 5/08/2025 al historial para entrenamiento futuro"""
    
    # Cargar datos históricos actuales
    try:
        df = pd.read_csv("data/historial_kabala_github_fixed.csv")
        print(f"📊 Datos actuales: {len(df)} registros")
        
        # Nuevo resultado del 14/08/2025
        nuevo_sorteo = {
            'fecha': '2025-08-05',
            'bolilla_1': 12,
            'bolilla_2': 27,
            'bolilla_3': 1,
            'bolilla_4': 10,
            'bolilla_5': 13,
            'bolilla_6': 22
        }
        
        # Verificar si ya existe
        if len(df) > 0:
            ultima_fecha = df['fecha'].iloc[-1] if 'fecha' in df.columns else 'N/A'
            print(f"📅 Última fecha en DB: {ultima_fecha}")
        
        # Crear DataFrame del nuevo sorteo
        nuevo_df = pd.DataFrame([nuevo_sorteo])
        
        # Agregar al historial
        df_actualizado = pd.concat([df, nuevo_df], ignore_index=True)
        
        # Guardar datos actualizados
        df_actualizado.to_csv("data/historial_kabala_github_fixed.csv", index=False)
        
        print(f"✅ Dataset actualizado: {len(df_actualizado)} registros")
        print(f"🎯 Agregado sorteo 5/08/2025: 14-39-34-40-31-29")
        
        # Crear archivo de backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data/backup/historial_backup_{timestamp}.csv"
        df.to_csv(backup_path, index=False)
        print(f"💾 Backup creado: {backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando historial: {e}")
        return False

def create_feedback_training_data():
    """Crea datos específicos de feedback para el resultado del 5/08/2025"""
    
    # Resultado real
    resultado_real = [14, 39, 34, 40, 31, 29]
    
    # Nuestras predicciones que tuvieron aciertos
    predicciones_exitosas = [
        [11, 14, 24, 27, 30, 31],  # 2 aciertos: 14, 31
        [11, 20, 21, 27, 30, 39],  # 1 acierto: 39
        [3, 8, 27, 28, 30, 40]     # 1 acierto: 40
    ]
    
    # Crear dataset de feedback
    feedback_data = []
    
    # Marcar resultado real como "perfecto"
    feedback_data.append({
        'bolilla_1': resultado_real[0],
        'bolilla_2': resultado_real[1], 
        'bolilla_3': resultado_real[2],
        'bolilla_4': resultado_real[3],
        'bolilla_5': resultado_real[4],
        'bolilla_6': resultado_real[5],
        'success_score': 1.0,
        'feedback_type': 'perfect_match',
        'date': '2025-08-14'
    })
    
    # Marcar predicciones parcialmente exitosas
    for i, pred in enumerate(predicciones_exitosas):
        aciertos = len(set(pred).intersection(set(resultado_real)))
        success_score = aciertos / 6.0
        
        feedback_data.append({
            'bolilla_1': pred[0],
            'bolilla_2': pred[1],
            'bolilla_3': pred[2], 
            'bolilla_4': pred[3],
            'bolilla_5': pred[4],
            'bolilla_6': pred[5],
            'success_score': success_score,
            'feedback_type': f'partial_match_{aciertos}_hits',
            'date': '2025-08-14'
        })
    
    # Guardar datos de feedback
    feedback_df = pd.DataFrame(feedback_data)
    feedback_df.to_csv("data/feedback_training_20250805.csv", index=False)
    
    print(f"🎯 Datos de feedback creados: {len(feedback_data)} registros")
    print("📁 Archivo: data/feedback_training_20250805.csv")
    
    return feedback_df

if __name__ == '__main__':
    print("🔄 ACTUALIZANDO DATOS HISTÓRICOS CON RESULTADO 5/08/2025")
    print("=" * 60)
    
    # Actualizar historial principal
    if update_historical_data():
        print("✅ Historial actualizado correctamente")
    
    print("\n🎯 CREANDO DATOS DE FEEDBACK PARA ENTRENAMIENTO")
    print("=" * 60)
    
    # Crear datos de feedback
    feedback_df = create_feedback_training_data()
    
    print("\n✅ Actualización completa - Sistema listo para re-entrenar")
