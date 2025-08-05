"""
Módulo simplificado para generación de informes ANCI
Version temporal sin dependencia de python-docx
"""

import os
import json
import logging
from datetime import datetime
from app.database import get_db_connection
from config import Config
import textwrap

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
logger = logging.getLogger(__name__)

class InformesANCI:
    def __init__(self):
        self.output_dir = os.path.join(UPLOAD_FOLDER, 'informes_anci')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generar_informe(self, incidente_id, tipo_informe='preliminar', usuario_id='sistema'):
        """
        Genera un informe ANCI del tipo especificado (versión simplificada)
        Por ahora genera un archivo de texto plano
        """
        try:
            logger.info(f"Iniciando generación de informe {tipo_informe} para incidente {incidente_id}")
            
            # Validar tipo de informe
            if tipo_informe not in ['preliminar', 'completo', 'final']:
                return {
                    'exito': False,
                    'error': 'Tipo de informe no válido'
                }
            
            # Obtener datos del incidente
            datos_incidente = self._obtener_datos_incidente(incidente_id)
            if not datos_incidente:
                return {
                    'exito': False,
                    'error': 'Incidente no encontrado'
                }
            
            # Generar el contenido del informe
            contenido = self._generar_contenido_informe(datos_incidente, tipo_informe)
            
            # Guardar el informe como archivo de texto
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"ANCI_{tipo_informe}_{datos_incidente['IDVisible']}_{timestamp}.txt"
            ruta_archivo = os.path.join(self.output_dir, nombre_archivo)
            
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            # Registrar en base de datos
            informe_id = self._registrar_informe(
                incidente_id=incidente_id,
                tipo_informe=tipo_informe,
                ruta_archivo=ruta_archivo,
                usuario_id=usuario_id
            )
            
            logger.info(f"Informe generado exitosamente: {ruta_archivo}")
            
            return {
                'exito': True,
                'informe_id': informe_id,
                'ruta_archivo': ruta_archivo,
                'contenido': contenido,
                'datos_incidente': datos_incidente
            }
            
        except Exception as e:
            logger.error(f"Error generando informe: {str(e)}")
            return {
                'exito': False,
                'error': str(e)
            }
    
    def _obtener_datos_incidente(self, incidente_id):
        """
        Obtiene los datos básicos del incidente desde la BD
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                i.IncidenteID,
                i.IDVisible,
                i.Titulo,
                i.FechaDeteccion,
                i.FechaOcurrencia,
                i.OrigenIncidente,
                i.Criticidad,
                i.EstadoActual,
                i.DescripcionInicial,
                i.AnciImpactoPreliminar,
                i.AccionesInmediatas,
                i.TipoRegistro,
                i.SolicitarCSIRT,
                e.RazonSocial as EmpresaNombre,
                e.RUT as EmpresaRUT,
                e.TipoEmpresa,
                inq.RazonSocial as InquilinoNombre
            FROM Incidentes i
            INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            INNER JOIN Inquilinos inq ON e.InquilinoID = inq.InquilinoID
            WHERE i.IncidenteID = ?
            """
            
            cursor.execute(query, (incidente_id,))
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            
            if not row:
                return None
                
            datos = dict(zip(columns, row))
            
            # Convertir fechas a string
            for campo in ['FechaDeteccion', 'FechaOcurrencia']:
                if datos.get(campo):
                    datos[campo] = datos[campo].strftime('%d/%m/%Y %H:%M')
            
            return datos
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del incidente: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def _generar_contenido_informe(self, datos, tipo_informe):
        """
        Genera el contenido del informe en formato estructurado para ANCI
        """
        contenido = []
        
        # Encabezado
        contenido.append("═" * 80)
        contenido.append(f"INFORME {tipo_informe.upper()} - PLATAFORMA ANCI")
        contenido.append("NOTIFICACIÓN DE INCIDENTE DE CIBERSEGURIDAD")
        contenido.append("═" * 80)
        contenido.append("")
        
        # Información del reporte
        contenido.append("╔═══════════════════════════════════════════════════════════════════════╗")
        contenido.append("║ INFORMACIÓN DEL REPORTE                                               ║")
        contenido.append("╚═══════════════════════════════════════════════════════════════════════╝")
        contenido.append(f"📅 Fecha del Reporte: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        contenido.append(f"🔢 ID Incidente: {datos.get('IDVisible', 'N/A')}")
        contenido.append(f"📋 Tipo de Informe: {tipo_informe.upper()}")
        contenido.append("")
        contenido.append("─" * 80)
        
        # Sección 1: Información de la Empresa
        contenido.append("╔═══════════════════════════════════════════════════════════════════════╗")
        contenido.append("║ 1. DATOS DE LA ORGANIZACIÓN AFECTADA                                  ║")
        contenido.append("╚═══════════════════════════════════════════════════════════════════════╝")
        contenido.append("")
        contenido.append(f"📌 Razón Social: {datos.get('EmpresaNombre', 'N/A')}")
        contenido.append(f"📌 RUT: {datos.get('EmpresaRUT', 'N/A')}")
        contenido.append(f"📌 Tipo de Entidad: {datos.get('TipoEmpresa', 'N/A')}")
        contenido.append(f"📌 Organización: {datos.get('InquilinoNombre', 'N/A')}")
        contenido.append("")
        
        # Sección 2: Información del Incidente
        contenido.append("╔═══════════════════════════════════════════════════════════════════════╗")
        contenido.append("║ 2. IDENTIFICACIÓN DEL INCIDENTE                                       ║")
        contenido.append("╚═══════════════════════════════════════════════════════════════════════╝")
        contenido.append("")
        contenido.append(f"🔴 Título del Incidente:")
        contenido.append(f"   {datos.get('Titulo', 'N/A')}")
        contenido.append("")
        contenido.append(f"📅 Fecha y Hora de Detección: {datos.get('FechaDeteccion', 'N/A')}")
        contenido.append(f"📅 Fecha y Hora de Ocurrencia: {datos.get('FechaOcurrencia', 'N/A')}")
        contenido.append("")
        contenido.append(f"⚠️  Nivel de Criticidad: {datos.get('Criticidad', 'N/A')}")
        contenido.append(f"🎯 Origen del Incidente: {datos.get('OrigenIncidente', 'N/A')}")
        contenido.append(f"📊 Estado Actual: {datos.get('EstadoActual', 'N/A')}")
        contenido.append("")
        
        # Sección 3: Descripción
        contenido.append("╔═══════════════════════════════════════════════════════════════════════╗")
        contenido.append("║ 3. DESCRIPCIÓN DETALLADA DEL INCIDENTE                               ║")
        contenido.append("╚═══════════════════════════════════════════════════════════════════════╝")
        contenido.append("")
        contenido.append("📝 Descripción:")
        desc = datos.get('DescripcionInicial', 'Sin descripción disponible')
        # Dividir descripción en líneas de máx 70 caracteres
        import textwrap
        for line in textwrap.wrap(desc, width=70):
            contenido.append(f"   {line}")
        contenido.append("")
        
        # Sección 4: Impacto
        contenido.append("╔═══════════════════════════════════════════════════════════════════════╗")
        contenido.append("║ 4. EVALUACIÓN PRELIMINAR DE IMPACTO                                  ║")
        contenido.append("╚═══════════════════════════════════════════════════════════════════════╝")
        contenido.append("")
        contenido.append("💥 Impacto Identificado:")
        impacto = datos.get('AnciImpactoPreliminar', 'Evaluación de impacto pendiente')
        for line in textwrap.wrap(impacto, width=70):
            contenido.append(f"   {line}")
        contenido.append("")
        
        # Sección 5: Acciones
        contenido.append("╔═══════════════════════════════════════════════════════════════════════╗")
        contenido.append("║ 5. MEDIDAS DE CONTENCIÓN Y ACCIONES INMEDIATAS                       ║")
        contenido.append("╚═══════════════════════════════════════════════════════════════════════╝")
        contenido.append("")
        contenido.append("🛡️ Acciones Implementadas:")
        acciones = datos.get('AccionesInmediatas', 'Sin acciones registradas')
        for line in textwrap.wrap(acciones, width=70):
            contenido.append(f"   {line}")
        contenido.append("")
        
        # Agregar secciones adicionales según tipo de informe
        if tipo_informe in ['completo', 'final']:
            contenido.append("6. ANÁLISIS DETALLADO")
            contenido.append("-" * 40)
            contenido.append("(Sección disponible en informe completo)")
            contenido.append("")
        
        if tipo_informe == 'final':
            contenido.append("7. CAUSA RAÍZ Y LECCIONES APRENDIDAS")
            contenido.append("-" * 40)
            contenido.append("(Sección disponible en informe final)")
            contenido.append("")
        
        # Información adicional según tipo de informe
        if tipo_informe == 'preliminar':
            contenido.append("╔═══════════════════════════════════════════════════════════════════════╗")
            contenido.append("║ ⚠️  RECORDATORIO - PRÓXIMOS PLAZOS ANCI                               ║")
            contenido.append("╚═══════════════════════════════════════════════════════════════════════╝")
            contenido.append("")
            contenido.append("📌 Informe COMPLETO: Dentro de 72 horas desde la detección")
            contenido.append("📌 Informe FINAL: Dentro de 30 días desde la detección")
            contenido.append("")
        
        # Campos pendientes para copiar a ANCI
        contenido.append("╔═══════════════════════════════════════════════════════════════════════╗")
        contenido.append("║ 📋 CAMPOS PARA COMPLETAR EN PLATAFORMA ANCI                          ║")
        contenido.append("╚═══════════════════════════════════════════════════════════════════════╝")
        contenido.append("")
        contenido.append("Los siguientes campos deben ser completados manualmente en la plataforma:")
        contenido.append("")
        contenido.append("✏️ Tipo de incidente (Taxonomía ANCI)")
        contenido.append("✏️ Sistemas o servicios afectados (detalle)")
        contenido.append("✏️ Número de usuarios afectados")
        contenido.append("✏️ Afectación a terceros (Sí/No)")
        contenido.append("✏️ Medidas de seguridad previas")
        if datos.get('TipoEmpresa') == 'OIV':
            contenido.append("✏️ Certificaciones de seguridad (ISO 27001, etc.)")
            contenido.append("✏️ Plan de continuidad activado")
        contenido.append("")
        
        # Pie del informe
        contenido.append("═" * 80)
        contenido.append("")
        contenido.append(f"📄 Informe {tipo_informe.upper()} generado según Ley 21.663")
        contenido.append(f"🕐 Fecha de generación: {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}")
        contenido.append(f"🏢 Sistema: AgenteDigital - Gestión de Incidentes ANCI")
        contenido.append("")
        contenido.append("═" * 80)
        
        return "\n".join(contenido)
    
    def _registrar_informe(self, incidente_id, tipo_informe, ruta_archivo, usuario_id):
        """
        Registra el informe generado en la base de datos
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener tamaño del archivo
            tamano_kb = os.path.getsize(ruta_archivo) / 1024
            
            # Primero verificar si la tabla existe
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'INFORMES_ANCI')
                BEGIN
                    -- Crear tabla temporal si no existe
                    CREATE TABLE INFORMES_ANCI (
                        InformeID INT IDENTITY(1,1) PRIMARY KEY,
                        IncidenteID INT NOT NULL,
                        TipoInforme NVARCHAR(20) NOT NULL,
                        EstadoInforme NVARCHAR(20) DEFAULT 'generado',
                        FechaGeneracion DATETIME DEFAULT GETDATE(),
                        RutaArchivo NVARCHAR(500) NOT NULL,
                        TamanoKB INT NOT NULL,
                        GeneradoPor NVARCHAR(100) NOT NULL,
                        Version INT DEFAULT 1,
                        Activo BIT DEFAULT 1
                    )
                END
            """)
            conn.commit()
            
            # Insertar registro
            query = """
            INSERT INTO INFORMES_ANCI (
                IncidenteID,
                TipoInforme,
                EstadoInforme,
                FechaGeneracion,
                RutaArchivo,
                TamanoKB,
                GeneradoPor,
                Version,
                Activo
            ) VALUES (?, ?, ?, GETDATE(), ?, ?, ?, 
                (SELECT ISNULL(MAX(Version), 0) + 1 
                 FROM INFORMES_ANCI 
                 WHERE IncidenteID = ? AND TipoInforme = ?),
                1);
            SELECT SCOPE_IDENTITY();
            """
            
            cursor.execute(query, (
                incidente_id,
                tipo_informe,
                'generado',
                ruta_archivo,
                tamano_kb,
                usuario_id,
                incidente_id,
                tipo_informe
            ))
            
            informe_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Informe registrado en BD con ID: {informe_id}")
            return informe_id
            
        except Exception as e:
            logger.error(f"Error registrando informe en BD: {str(e)}")
            # Si falla el registro en BD, igual retornamos un ID temporal
            return 999
        finally:
            if conn:
                conn.close()
    
    def validar_datos_incidente(self, incidente_id):
        """
        Valida que el incidente tenga los datos mínimos para generar informes
        """
        try:
            datos = self._obtener_datos_incidente(incidente_id)
            
            if not datos:
                return {
                    'valido': False,
                    'errores': ['Incidente no encontrado']
                }
            
            errores = []
            advertencias = []
            
            # Validar campos obligatorios
            campos_obligatorios = [
                'Titulo', 'FechaDeteccion', 'DescripcionBreve',
                'EmpresaNombre', 'EmpresaRUT'
            ]
            
            for campo in campos_obligatorios:
                if not datos.get(campo):
                    errores.append(f"Campo obligatorio faltante: {campo}")
            
            # Validar campos recomendados
            campos_recomendados = [
                'ImpactoPreliminar', 'AccionesInmediatas',
                'OrigenIncidente', 'Criticidad'
            ]
            
            for campo in campos_recomendados:
                if not datos.get(campo):
                    advertencias.append(f"Campo recomendado faltante: {campo}")
            
            return {
                'valido': len(errores) == 0,
                'errores': errores,
                'advertencias': advertencias,
                'datos_disponibles': {
                    'titulo': bool(datos.get('Titulo')),
                    'fecha_deteccion': bool(datos.get('FechaDeteccion')),
                    'descripcion': bool(datos.get('DescripcionBreve')),
                    'impacto': bool(datos.get('ImpactoPreliminar')),
                    'acciones': bool(datos.get('AccionesInmediatas'))
                }
            }
            
        except Exception as e:
            logger.error(f"Error validando datos: {str(e)}")
            return {
                'valido': False,
                'errores': [str(e)]
            }