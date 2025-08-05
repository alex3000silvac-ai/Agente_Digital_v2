#!/usr/bin/env python3
"""Script para cargar documentos de prueba en la gestión documental"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.core.database import get_db_connection
from datetime import datetime, timedelta
import random

def cargar_documentos_prueba():
    conn = get_db_connection()
    if not conn:
        print("❌ Error de conexión")
        return
        
    cursor = conn.cursor()
    
    try:
        print("\n=== CARGANDO DOCUMENTOS DE PRUEBA ===\n")
        
        empresas = [3, 10]  # Surtika y Jurídica
        
        documentos_por_carpeta = {
            1: [  # Configuración del Sistema
                ("Manual_Configuracion_ANCI.pdf", "Manual completo de configuración del sistema ANCI"),
                ("Parametros_Sistema_2025.xlsx", "Parámetros actualizados del sistema")
            ],
            2: [  # Registro ANCI
                ("Certificado_Registro_ANCI.pdf", "Certificado oficial de registro en ANCI"),
                ("Formulario_Inscripcion.pdf", "Formulario de inscripción completado")
            ],
            3: [  # Clasificación Entidad
                ("Clasificacion_PSE_2025.pdf", "Documento de clasificación como PSE"),
                ("Evaluacion_Riesgos.docx", "Evaluación de riesgos de la entidad")
            ],
            4: [  # Gobernanza y Seguridad
                ("Politica_Seguridad_v3.pdf", "Política de seguridad de la información v3.0"),
                ("Procedimiento_Incidentes.pdf", "Procedimiento de gestión de incidentes"),
                ("Organigrama_Seguridad.png", "Organigrama del área de seguridad")
            ],
            5: [  # Gestión de Incidentes
                ("Plan_Respuesta_Incidentes.pdf", "Plan de respuesta ante incidentes de seguridad"),
                ("Registro_Incidentes_2025.xlsx", "Registro detallado de incidentes"),
                ("Informe_Phishing_Q1.pdf", "Informe de intentos de phishing Q1")
            ],
            6: [  # Contratos con Terceros
                ("Contrato_SOC_2025.pdf", "Contrato con centro de operaciones de seguridad"),
                ("SLA_Proveedores.pdf", "Acuerdos de nivel de servicio con proveedores")
            ],
            7: [  # Certificaciones
                ("ISO_27001_Certificate.pdf", "Certificado ISO 27001:2022"),
                ("Informe_Auditoria_ISO.pdf", "Informe de auditoría de certificación")
            ],
            8: [  # Auditorías y Evidencias
                ("Auditoria_Interna_2025.pdf", "Informe de auditoría interna 2025"),
                ("Evidencias_Controles.zip", "Evidencias de implementación de controles"),
                ("Checklist_Cumplimiento.xlsx", "Checklist de cumplimiento normativo")
            ],
            9: [  # Capacitación del Personal
                ("Plan_Capacitacion_2025.pdf", "Plan anual de capacitación en ciberseguridad"),
                ("Certificados_Personal.zip", "Certificados de capacitación del personal"),
                ("Material_Phishing.pdf", "Material de capacitación sobre phishing")
            ],
            10: [ # Continuidad del Negocio
                ("BCP_2025.pdf", "Plan de continuidad del negocio actualizado"),
                ("BIA_Analysis.xlsx", "Análisis de impacto en el negocio"),
                ("DRP_Sistemas_Criticos.pdf", "Plan de recuperación ante desastres")
            ],
            11: [ # Comunicación ANCI
                ("Comunicados_ANCI_2025.pdf", "Comunicados oficiales con ANCI"),
                ("Reportes_Mensuales.zip", "Reportes mensuales enviados a ANCI")
            ],
            12: [ # Respaldos Históricos
                ("Respaldo_Politicas_2024.zip", "Respaldo de políticas año 2024"),
                ("Historico_Incidentes_2024.xlsx", "Histórico de incidentes 2024")
            ]
        }
        
        # Crear directorio base si no existe
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'archivos', 'documentos')
        os.makedirs(base_dir, exist_ok=True)
        
        documentos_creados = 0
        
        for empresa_id in empresas:
            print(f"\n📁 Cargando documentos para empresa ID {empresa_id}:")
            
            for carpeta_id, documentos in documentos_por_carpeta.items():
                # Solo cargar algunos documentos aleatoriamente
                if random.random() > 0.7:  # 70% de probabilidad de cargar
                    continue
                    
                for nombre_archivo, descripcion in documentos:
                    if random.random() > 0.6:  # 60% de probabilidad por documento
                        continue
                    
                    # Crear estructura de carpetas
                    carpeta_path = os.path.join(base_dir, f"empresa_{empresa_id}", f"carpeta_{carpeta_id}")
                    os.makedirs(carpeta_path, exist_ok=True)
                    
                    # Generar nombre único
                    extension = nombre_archivo.rsplit('.', 1)[1]
                    unique_filename = f"{random.randint(1000,9999)}_{nombre_archivo}"
                    filepath = os.path.join(carpeta_path, unique_filename)
                    
                    # Crear archivo dummy
                    with open(filepath, 'w') as f:
                        f.write(f"Archivo de prueba: {nombre_archivo}\n")
                        f.write(f"Empresa ID: {empresa_id}\n")
                        f.write(f"Carpeta: {carpeta_id}\n")
                        f.write(f"Descripción: {descripcion}\n")
                        f.write(f"Fecha: {datetime.now()}\n")
                    
                    # Insertar en BD
                    fecha_subida = datetime.now() - timedelta(days=random.randint(0, 90))
                    
                    cursor.execute("""
                        INSERT INTO DOCUMENTOS_ANCI (
                            EmpresaID, CarpetaID, NombreArchivo, 
                            RutaArchivo, TipoDocumento, Descripcion, 
                            FechaSubida, Activo
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """, (
                        empresa_id, carpeta_id, nombre_archivo,
                        filepath, extension, descripcion, fecha_subida
                    ))
                    
                    documentos_creados += 1
                    print(f"   ✅ {nombre_archivo} en carpeta {carpeta_id}")
        
        conn.commit()
        print(f"\n✅ Total de documentos creados: {documentos_creados}")
        
        # Mostrar resumen
        print("\n📊 Resumen por empresa:")
        for empresa_id in empresas:
            cursor.execute("""
                SELECT COUNT(*) as total, COUNT(DISTINCT CarpetaID) as carpetas
                FROM DOCUMENTOS_ANCI
                WHERE EmpresaID = ? AND Activo = 1
            """, (empresa_id,))
            result = cursor.fetchone()
            print(f"   - Empresa {empresa_id}: {result.total} documentos en {result.carpetas} carpetas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    cargar_documentos_prueba()