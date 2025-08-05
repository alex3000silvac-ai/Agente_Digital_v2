#!/usr/bin/env python3
"""
Sistema Dinámico de Incidentes ANCI
Maneja acordeones variables según tipo de empresa (OIV/PSE)
Las secciones se ajustan dinámicamente según las taxonomías aplicables
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..core.database import get_db_connection

@dataclass
class SeccionConfig:
    """Configuración de una sección del formulario"""
    seccion_id: int
    codigo_seccion: str
    tipo_seccion: str  # FIJA o TAXONOMIA
    numero_orden: int
    titulo: str
    descripcion: str
    campos_json: str
    aplica_oiv: bool
    aplica_pse: bool
    activo: bool
    color_indicador: str
    icono_seccion: str
    max_comentarios: int
    max_archivos: int
    max_size_mb: int


class SistemaDinamicoIncidentes:
    """
    Gestiona incidentes con secciones dinámicas según tipo de empresa
    """
    
    def __init__(self):
        self.base_path = os.environ.get('ARCHIVOS_PATH', '/archivos')
        
    def obtener_secciones_empresa(self, empresa_id: int) -> List[SeccionConfig]:
        """
        Obtiene las secciones aplicables según el tipo de empresa
        Devuelve entre 6 y 41 secciones dependiendo si es OIV, PSE o AMBAS
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener tipo de empresa
            cursor.execute("""
                SELECT Tipo_Empresa FROM Empresas WHERE EmpresaID = ?
            """, (empresa_id,))
            
            tipo_empresa = cursor.fetchone()
            if not tipo_empresa:
                raise ValueError(f"Empresa {empresa_id} no encontrada")
            
            tipo = tipo_empresa[0]  # OIV, PSE o AMBAS
            
            # Obtener secciones según tipo de empresa
            query = """
                SELECT 
                    SeccionID, CodigoSeccion, TipoSeccion, NumeroOrden,
                    Titulo, Descripcion, CamposJSON, AplicaOIV, AplicaPSE,
                    Activo, ColorIndicador, IconoSeccion, MaxComentarios,
                    MaxArchivos, MaxSizeMB
                FROM ANCI_SECCIONES_CONFIG
                WHERE Activo = 1
                AND (
                    TipoSeccion = 'FIJA'  -- Las 6 fijas siempre aparecen
                    OR (
                        TipoSeccion = 'TAXONOMIA' 
                        AND (
                            (? = 'OIV' AND AplicaOIV = 1)
                            OR (? = 'PSE' AND AplicaPSE = 1)
                            OR (? = 'AMBAS')  -- Si es AMBAS, mostrar todas
                        )
                    )
                )
                ORDER BY NumeroOrden
            """
            
            cursor.execute(query, (tipo, tipo, tipo))
            secciones = []
            
            for row in cursor.fetchall():
                seccion = SeccionConfig(
                    seccion_id=row[0],
                    codigo_seccion=row[1],
                    tipo_seccion=row[2],
                    numero_orden=row[3],
                    titulo=row[4],
                    descripcion=row[5],
                    campos_json=row[6],
                    aplica_oiv=bool(row[7]),
                    aplica_pse=bool(row[8]),
                    activo=bool(row[9]),
                    color_indicador=row[10],
                    icono_seccion=row[11],
                    max_comentarios=row[12],
                    max_archivos=row[13],
                    max_size_mb=row[14]
                )
                secciones.append(seccion)
            
            print(f"✅ Empresa tipo {tipo}: {len(secciones)} secciones aplicables")
            return secciones
            
        finally:
            if conn:
                conn.close()
    
    def crear_incidente_completo(self, incidente_id: int, empresa_id: int, datos_iniciales: dict) -> dict:
        """
        Crea la estructura completa del incidente con todas las secciones aplicables
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener secciones aplicables
            secciones = self.obtener_secciones_empresa(empresa_id)
            
            # Crear registro para cada sección aplicable
            for seccion in secciones:
                # Datos iniciales según tipo de sección
                datos_seccion = {}
                if seccion.tipo_seccion == 'FIJA':
                    # Para secciones fijas, tomar datos del dict inicial si existen
                    datos_seccion = datos_iniciales.get(seccion.codigo_seccion, {})
                
                cursor.execute("""
                    INSERT INTO INCIDENTES_SECCIONES_DATOS 
                    (IncidenteID, SeccionID, DatosJSON, EstadoSeccion, PorcentajeCompletado, ActualizadoPor)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    incidente_id,
                    seccion.seccion_id,
                    json.dumps(datos_seccion),
                    'VACIO' if not datos_seccion else 'PARCIAL',
                    0 if not datos_seccion else 50,
                    datos_iniciales.get('usuario', 'Sistema')
                ))
            
            conn.commit()
            
            return {
                'success': True,
                'incidente_id': incidente_id,
                'secciones_creadas': len(secciones),
                'tipo_empresa': self._get_tipo_empresa(cursor, empresa_id)
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def guardar_seccion(self, incidente_id: int, seccion_id: int, datos: dict, usuario: str) -> dict:
        """
        Guarda los datos de una sección específica
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar que la sección existe y está activa
            cursor.execute("""
                SELECT CodigoSeccion, TipoSeccion FROM ANCI_SECCIONES_CONFIG 
                WHERE SeccionID = ? AND Activo = 1
            """, (seccion_id,))
            
            seccion = cursor.fetchone()
            if not seccion:
                raise ValueError(f"Sección {seccion_id} no válida")
            
            # Actualizar o insertar datos
            cursor.execute("""
                MERGE INCIDENTES_SECCIONES_DATOS AS target
                USING (SELECT ? AS IncidenteID, ? AS SeccionID) AS source
                ON target.IncidenteID = source.IncidenteID AND target.SeccionID = source.SeccionID
                WHEN MATCHED THEN
                    UPDATE SET 
                        DatosJSON = ?,
                        EstadoSeccion = ?,
                        PorcentajeCompletado = ?,
                        FechaActualizacion = GETDATE(),
                        ActualizadoPor = ?
                WHEN NOT MATCHED THEN
                    INSERT (IncidenteID, SeccionID, DatosJSON, EstadoSeccion, PorcentajeCompletado, ActualizadoPor)
                    VALUES (?, ?, ?, ?, ?, ?);
            """, (
                incidente_id, seccion_id,
                json.dumps(datos),
                self._calcular_estado_seccion(datos),
                self._calcular_porcentaje_completado(datos),
                usuario,
                incidente_id, seccion_id,
                json.dumps(datos),
                self._calcular_estado_seccion(datos),
                self._calcular_porcentaje_completado(datos),
                usuario
            ))
            
            # Auditoría
            self._registrar_auditoria(cursor, incidente_id, seccion_id, 'EDITAR_SECCION', {
                'datos_nuevos': datos,
                'usuario': usuario
            })
            
            conn.commit()
            
            return {
                'success': True,
                'seccion_id': seccion_id,
                'estado': self._calcular_estado_seccion(datos)
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def agregar_comentario(self, incidente_id: int, seccion_id: int, comentario: str, 
                          tipo_comentario: str, usuario: str) -> dict:
        """
        Agrega un comentario a una sección (máximo 6 por sección)
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar límite de comentarios
            if not self._verificar_limite(cursor, incidente_id, seccion_id, 'COMENTARIO'):
                raise ValueError("Se alcanzó el límite de comentarios para esta sección")
            
            # Obtener siguiente número
            cursor.execute("""
                SELECT ISNULL(MAX(NumeroComentario), 0) + 1 
                FROM INCIDENTES_COMENTARIOS 
                WHERE IncidenteID = ? AND SeccionID = ?
            """, (incidente_id, seccion_id))
            
            numero = cursor.fetchone()[0]
            
            # Insertar comentario
            cursor.execute("""
                INSERT INTO INCIDENTES_COMENTARIOS 
                (IncidenteID, SeccionID, NumeroComentario, Comentario, TipoComentario, CreadoPor)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (incidente_id, seccion_id, numero, comentario, tipo_comentario, usuario))
            
            # Auditoría
            self._registrar_auditoria(cursor, incidente_id, seccion_id, 'AGREGAR_COMENTARIO', {
                'comentario': comentario,
                'tipo': tipo_comentario,
                'usuario': usuario
            })
            
            conn.commit()
            
            return {
                'success': True,
                'comentario_numero': numero
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def subir_archivo(self, incidente_id: int, seccion_id: int, archivo_info: dict, usuario: str) -> dict:
        """
        Sube un archivo a una sección (máximo 10 por sección, 10MB cada uno)
        archivo_info debe contener: nombre_original, contenido_bytes, tipo_mime
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar límites
            if not self._verificar_limite(cursor, incidente_id, seccion_id, 'ARCHIVO'):
                raise ValueError("Se alcanzó el límite de archivos para esta sección")
            
            # Verificar tamaño
            tamano_mb = len(archivo_info['contenido_bytes']) / (1024 * 1024)
            cursor.execute("""
                SELECT MaxSizeMB FROM ANCI_SECCIONES_CONFIG WHERE SeccionID = ?
            """, (seccion_id,))
            max_size = cursor.fetchone()[0]
            
            if tamano_mb > max_size:
                raise ValueError(f"El archivo excede el límite de {max_size}MB")
            
            # Obtener empresa ID para la ruta
            cursor.execute("""
                SELECT EmpresaID, IDVisible FROM Incidentes WHERE IncidenteID = ?
            """, (incidente_id,))
            empresa_id, id_visible = cursor.fetchone()
            
            # Crear estructura de carpetas
            ruta_empresa = os.path.join(self.base_path, f"empresa_{empresa_id}")
            ruta_incidente = os.path.join(ruta_empresa, f"incidente_{id_visible}")
            ruta_seccion = os.path.join(ruta_incidente, f"seccion_{seccion_id}")
            
            os.makedirs(ruta_seccion, exist_ok=True)
            
            # Generar nombre único
            hash_archivo = hashlib.sha256(archivo_info['contenido_bytes']).hexdigest()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            extension = os.path.splitext(archivo_info['nombre_original'])[1]
            nombre_servidor = f"{timestamp}_{hash_archivo[:8]}{extension}"
            
            # Guardar archivo
            ruta_completa = os.path.join(ruta_seccion, nombre_servidor)
            with open(ruta_completa, 'wb') as f:
                f.write(archivo_info['contenido_bytes'])
            
            # Obtener número siguiente
            cursor.execute("""
                SELECT ISNULL(MAX(NumeroArchivo), 0) + 1 
                FROM INCIDENTES_ARCHIVOS 
                WHERE IncidenteID = ? AND SeccionID = ?
            """, (incidente_id, seccion_id))
            
            numero = cursor.fetchone()[0]
            
            # Registrar en BD
            cursor.execute("""
                INSERT INTO INCIDENTES_ARCHIVOS 
                (IncidenteID, SeccionID, NumeroArchivo, NombreOriginal, NombreServidor,
                 RutaArchivo, TipoArchivo, TamanoKB, HashArchivo, Descripcion, SubidoPor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incidente_id, seccion_id, numero,
                archivo_info['nombre_original'],
                nombre_servidor,
                ruta_completa,
                archivo_info.get('tipo_mime', 'application/octet-stream'),
                len(archivo_info['contenido_bytes']) // 1024,
                hash_archivo,
                archivo_info.get('descripcion', ''),
                usuario
            ))
            
            # Auditoría
            self._registrar_auditoria(cursor, incidente_id, seccion_id, 'SUBIR_ARCHIVO', {
                'archivo': archivo_info['nombre_original'],
                'tamano_kb': len(archivo_info['contenido_bytes']) // 1024,
                'usuario': usuario
            })
            
            conn.commit()
            
            return {
                'success': True,
                'archivo_numero': numero,
                'nombre_servidor': nombre_servidor,
                'hash': hash_archivo
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            # Si falló, intentar eliminar el archivo
            if 'ruta_completa' in locals() and os.path.exists(ruta_completa):
                os.remove(ruta_completa)
            raise e
        finally:
            if conn:
                conn.close()
    
    def cargar_incidente_completo(self, incidente_id: int) -> dict:
        """
        Carga toda la información del incidente con sus secciones dinámicas
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Datos básicos del incidente
            cursor.execute("""
                SELECT i.*, e.Tipo_Empresa 
                FROM Incidentes i
                INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
                WHERE i.IncidenteID = ?
            """, (incidente_id,))
            
            incidente = cursor.fetchone()
            if not incidente:
                raise ValueError(f"Incidente {incidente_id} no encontrado")
            
            incidente_dict = dict(zip([column[0] for column in cursor.description], incidente))
            tipo_empresa = incidente_dict['Tipo_Empresa']
            
            # Cargar secciones aplicables con sus datos
            cursor.execute("""
                SELECT 
                    sc.SeccionID, sc.CodigoSeccion, sc.TipoSeccion, sc.NumeroOrden,
                    sc.Titulo, sc.Descripcion, sc.ColorIndicador, sc.IconoSeccion,
                    sd.DatosJSON, sd.EstadoSeccion, sd.PorcentajeCompletado,
                    (SELECT COUNT(*) FROM INCIDENTES_COMENTARIOS 
                     WHERE IncidenteID = ? AND SeccionID = sc.SeccionID AND Activo = 1) as TotalComentarios,
                    (SELECT COUNT(*) FROM INCIDENTES_ARCHIVOS 
                     WHERE IncidenteID = ? AND SeccionID = sc.SeccionID AND Activo = 1) as TotalArchivos
                FROM ANCI_SECCIONES_CONFIG sc
                LEFT JOIN INCIDENTES_SECCIONES_DATOS sd 
                    ON sd.IncidenteID = ? AND sd.SeccionID = sc.SeccionID
                WHERE sc.Activo = 1
                AND (
                    sc.TipoSeccion = 'FIJA'
                    OR (
                        sc.TipoSeccion = 'TAXONOMIA' 
                        AND (
                            (? = 'OIV' AND sc.AplicaOIV = 1)
                            OR (? = 'PSE' AND sc.AplicaPSE = 1)
                            OR (? = 'AMBAS')
                        )
                    )
                )
                ORDER BY sc.NumeroOrden
            """, (incidente_id, incidente_id, incidente_id, tipo_empresa, tipo_empresa, tipo_empresa))
            
            secciones = []
            for row in cursor.fetchall():
                seccion = {
                    'seccion_id': row[0],
                    'codigo': row[1],
                    'tipo': row[2],
                    'orden': row[3],
                    'titulo': row[4],
                    'descripcion': row[5],
                    'color': row[6] if row[10] > 0 else '#6c757d',  # Color según completado
                    'icono': row[7],
                    'datos': json.loads(row[8]) if row[8] else {},
                    'estado': row[9] or 'VACIO',
                    'porcentaje': row[10] or 0,
                    'total_comentarios': row[11],
                    'total_archivos': row[12],
                    'tiene_contenido': (row[11] + row[12]) > 0 or bool(row[8])
                }
                
                # Cargar comentarios de la sección
                seccion['comentarios'] = self._cargar_comentarios_seccion(cursor, incidente_id, row[0])
                
                # Cargar archivos de la sección
                seccion['archivos'] = self._cargar_archivos_seccion(cursor, incidente_id, row[0])
                
                secciones.append(seccion)
            
            return {
                'success': True,
                'incidente': incidente_dict,
                'secciones': secciones,
                'total_secciones': len(secciones),
                'secciones_con_contenido': sum(1 for s in secciones if s['tiene_contenido'])
            }
            
        finally:
            if conn:
                conn.close()
    
    def eliminar_incidente_completo(self, incidente_id: int, usuario: str) -> dict:
        """
        Elimina completamente un incidente, sus datos y archivos
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener info para eliminar archivos físicos
            cursor.execute("""
                SELECT DISTINCT RutaArchivo 
                FROM INCIDENTES_ARCHIVOS 
                WHERE IncidenteID = ?
            """, (incidente_id,))
            
            archivos_eliminar = [row[0] for row in cursor.fetchall()]
            
            # Auditoría antes de eliminar
            self._registrar_auditoria(cursor, incidente_id, None, 'ELIMINAR_INCIDENTE', {
                'usuario': usuario,
                'total_archivos': len(archivos_eliminar)
            })
            
            # Eliminar en orden inverso a las foreign keys
            tablas_eliminar = [
                'INCIDENTES_ARCHIVOS',
                'INCIDENTES_COMENTARIOS',
                'INCIDENTES_SECCIONES_DATOS',
                'INCIDENTE_TAXONOMIA',
                'Incidentes'
            ]
            
            for tabla in tablas_eliminar:
                cursor.execute(f"DELETE FROM {tabla} WHERE IncidenteID = ?", (incidente_id,))
            
            conn.commit()
            
            # Eliminar archivos físicos
            for archivo in archivos_eliminar:
                try:
                    if os.path.exists(archivo):
                        os.remove(archivo)
                except Exception as e:
                    print(f"⚠️ Error eliminando archivo {archivo}: {e}")
            
            return {
                'success': True,
                'archivos_eliminados': len(archivos_eliminar)
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    # Métodos auxiliares privados
    
    def _get_tipo_empresa(self, cursor, empresa_id: int) -> str:
        cursor.execute("SELECT Tipo_Empresa FROM Empresas WHERE EmpresaID = ?", (empresa_id,))
        result = cursor.fetchone()
        return result[0] if result else 'AMBAS'
    
    def _calcular_estado_seccion(self, datos: dict) -> str:
        if not datos:
            return 'VACIO'
        # Contar campos llenos
        campos_llenos = sum(1 for v in datos.values() if v)
        total_campos = len(datos)
        if campos_llenos == 0:
            return 'VACIO'
        elif campos_llenos == total_campos:
            return 'COMPLETO'
        else:
            return 'PARCIAL'
    
    def _calcular_porcentaje_completado(self, datos: dict) -> int:
        if not datos:
            return 0
        campos_llenos = sum(1 for v in datos.values() if v)
        total_campos = len(datos)
        return int((campos_llenos / total_campos) * 100) if total_campos > 0 else 0
    
    def _verificar_limite(self, cursor, incidente_id: int, seccion_id: int, tipo: str) -> bool:
        if tipo == 'COMENTARIO':
            cursor.execute("""
                SELECT dbo.fn_VerificarLimites(?, ?, 'COMENTARIO')
            """, (incidente_id, seccion_id))
        else:
            cursor.execute("""
                SELECT dbo.fn_VerificarLimites(?, ?, 'ARCHIVO')
            """, (incidente_id, seccion_id))
        
        return bool(cursor.fetchone()[0])
    
    def _cargar_comentarios_seccion(self, cursor, incidente_id: int, seccion_id: int) -> list:
        cursor.execute("""
            SELECT NumeroComentario, Comentario, TipoComentario, 
                   FechaCreacion, CreadoPor
            FROM INCIDENTES_COMENTARIOS
            WHERE IncidenteID = ? AND SeccionID = ? AND Activo = 1
            ORDER BY NumeroComentario
        """, (incidente_id, seccion_id))
        
        comentarios = []
        for row in cursor.fetchall():
            comentarios.append({
                'numero': row[0],
                'texto': row[1],
                'tipo': row[2],
                'fecha': row[3].isoformat() if row[3] else None,
                'usuario': row[4]
            })
        return comentarios
    
    def _cargar_archivos_seccion(self, cursor, incidente_id: int, seccion_id: int) -> list:
        cursor.execute("""
            SELECT NumeroArchivo, NombreOriginal, NombreServidor,
                   TipoArchivo, TamanoKB, Descripcion, FechaSubida, SubidoPor
            FROM INCIDENTES_ARCHIVOS
            WHERE IncidenteID = ? AND SeccionID = ? AND Activo = 1
            ORDER BY NumeroArchivo
        """, (incidente_id, seccion_id))
        
        archivos = []
        for row in cursor.fetchall():
            archivos.append({
                'numero': row[0],
                'nombre_original': row[1],
                'nombre_servidor': row[2],
                'tipo': row[3],
                'tamano_kb': row[4],
                'descripcion': row[5],
                'fecha': row[6].isoformat() if row[6] else None,
                'usuario': row[7]
            })
        return archivos
    
    def _registrar_auditoria(self, cursor, incidente_id: int, seccion_id: Optional[int], 
                           tipo_accion: str, datos: dict):
        cursor.execute("""
            INSERT INTO INCIDENTES_AUDITORIA 
            (IncidenteID, SeccionID, TipoAccion, DatosNuevos, Usuario, FechaAccion)
            VALUES (?, ?, ?, ?, ?, GETDATE())
        """, (
            incidente_id,
            seccion_id,
            tipo_accion,
            json.dumps(datos),
            datos.get('usuario', 'Sistema')
        ))