#!/usr/bin/env python3
"""
Sistema de Clonado Perfecto para Incidentes
Lo que guardas es EXACTAMENTE lo que obtienes al editar
Con corrección automática de encoding UTF-8
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from ...database import get_db_connection
from ...utils.encoding_fixer import EncodingFixer

class IncidenteClonadorPerfecto:
    """
    Sistema que funciona como CTRL+C y CTRL+V perfecto
    Con corrección automática de problemas de encoding
    """
    
    def __init__(self):
        self.ruta_fotografias = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'fotografias_incidentes'
        )
        os.makedirs(self.ruta_fotografias, exist_ok=True)
    
    def crear_fotografia_completa(self, incidente_id):
        """
        Crea una "fotografía" EXACTA de TODO el incidente
        """
        print(f"📸 Creando fotografía completa del incidente {incidente_id}...")
        
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                raise Exception("No se pudo conectar a la BD")
            
            cursor = conn.cursor()
            
            # 1. Datos principales del incidente
            cursor.execute("SELECT * FROM Incidentes WHERE IncidenteID = ?", (incidente_id,))
            columnas = [desc[0] for desc in cursor.description]
            fila = cursor.fetchone()
            
            if not fila:
                raise Exception(f"Incidente {incidente_id} no encontrado")
            
            datos_principales = dict(zip(columnas, fila))
            # Corregir encoding
            datos_principales = EncodingFixer.fix_dict(datos_principales)
            
            # 2. TODAS las evidencias generales
            cursor.execute("""
                SELECT * FROM EvidenciasIncidentes 
                WHERE IncidenteID = ?
                ORDER BY SeccionFormulario, FechaSubida
            """, (incidente_id,))
            
            evidencias_generales = []
            columnas_ev = [desc[0] for desc in cursor.description]
            for evidencia in cursor.fetchall():
                ev_dict = dict(zip(columnas_ev, evidencia))
                ev_dict = EncodingFixer.fix_dict(ev_dict)
                evidencias_generales.append(ev_dict)
            
            # 3. Taxonomías seleccionadas
            cursor.execute("""
                SELECT IT.*, TI.Area, TI.Efecto, TI.Categoria_del_Incidente, 
                       TI.Subcategoria_del_Incidente, TI.Tipo_Empresa
                FROM INCIDENTE_TAXONOMIA IT
                LEFT JOIN TAXONOMIA_INCIDENTES TI ON IT.Id_Taxonomia = TI.Id_Incidente
                WHERE IT.IncidenteID = ?
            """, (incidente_id,))
            
            taxonomias = []
            columnas_tax = [desc[0] for desc in cursor.description]
            for taxonomia in cursor.fetchall():
                tax_dict = dict(zip(columnas_tax, taxonomia))
                tax_dict = EncodingFixer.fix_dict(tax_dict)
                taxonomias.append(tax_dict)
            
            # 4. Evidencias de taxonomías
            cursor.execute("""
                SELECT * FROM EVIDENCIAS_TAXONOMIA 
                WHERE IncidenteID = ?
                ORDER BY Id_Taxonomia, NumeroEvidencia
            """, (incidente_id,))
            
            evidencias_taxonomias = []
            if cursor.description:
                columnas_et = [desc[0] for desc in cursor.description]
                for ev_tax in cursor.fetchall():
                    et_dict = dict(zip(columnas_et, ev_tax))
                    et_dict = EncodingFixer.fix_dict(et_dict)
                    evidencias_taxonomias.append(et_dict)
            
            # 5. Comentarios de taxonomías
            cursor.execute("""
                SELECT * FROM COMENTARIOS_TAXONOMIA 
                WHERE IncidenteID = ?
            """, (incidente_id,))
            
            comentarios_taxonomias = []
            if cursor.description:
                columnas_ct = [desc[0] for desc in cursor.description]
                for comentario in cursor.fetchall():
                    ct_dict = dict(zip(columnas_ct, comentario))
                    ct_dict = EncodingFixer.fix_dict(ct_dict)
                    comentarios_taxonomias.append(ct_dict)
            
            # Crear fotografía completa
            fotografia = {
                "metadata": {
                    "version": "2.0",
                    "incidente_id": incidente_id,
                    "fecha_fotografia": datetime.now().isoformat(),
                    "encoding": "UTF-8",
                    "correccion_aplicada": True
                },
                "datos_principales": datos_principales,
                "evidencias_generales": evidencias_generales,
                "taxonomias": taxonomias,
                "evidencias_taxonomias": evidencias_taxonomias,
                "comentarios_taxonomias": comentarios_taxonomias,
                "resumen": {
                    "total_evidencias": len(evidencias_generales),
                    "total_taxonomias": len(taxonomias),
                    "total_evidencias_tax": len(evidencias_taxonomias),
                    "total_comentarios": len(comentarios_taxonomias)
                }
            }
            
            print(f"✅ Fotografía creada exitosamente")
            print(f"📊 Resumen: {fotografia['resumen']}")
            
            return fotografia
            
        except Exception as e:
            print(f"❌ Error creando fotografía: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def guardar_fotografia(self, incidente_id, indice_unico, fotografia, tipo="actual"):
        """
        Guarda la fotografía en archivo JSON
        """
        # Crear carpeta para el incidente
        carpeta_incidente = os.path.join(self.ruta_fotografias, str(incidente_id))
        os.makedirs(carpeta_incidente, exist_ok=True)
        
        # Nombre del archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"fotografia_{tipo}_{timestamp}.json"
        ruta_completa = os.path.join(carpeta_incidente, nombre_archivo)
        
        # Guardar JSON con formato legible
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            json.dump(fotografia, f, ensure_ascii=False, indent=2, default=str)
        
        # También guardar como "ultima" para acceso rápido
        ruta_ultima = os.path.join(carpeta_incidente, f"fotografia_{tipo}_ultima.json")
        shutil.copy2(ruta_completa, ruta_ultima)
        
        print(f"💾 Fotografía guardada en: {ruta_completa}")
        return ruta_completa
    
    def cargar_fotografia_ultima(self, incidente_id, tipo="actual"):
        """
        Carga la última fotografía guardada
        """
        carpeta_incidente = os.path.join(self.ruta_fotografias, str(incidente_id))
        ruta_ultima = os.path.join(carpeta_incidente, f"fotografia_{tipo}_ultima.json")
        
        if not os.path.exists(ruta_ultima):
            print(f"⚠️ No existe fotografía previa, creando nueva...")
            return None
        
        try:
            with open(ruta_ultima, 'r', encoding='utf-8') as f:
                fotografia = json.load(f)
            
            print(f"📂 Fotografía cargada desde: {ruta_ultima}")
            return fotografia
            
        except Exception as e:
            print(f"❌ Error cargando fotografía: {e}")
            return None
    
    def clonar_para_editar(self, incidente_id):
        """
        Crea un clon perfecto para edición
        """
        # 1. Crear fotografía actual
        fotografia = self.crear_fotografia_completa(incidente_id)
        
        # 2. Guardar como "editando"
        self.guardar_fotografia(incidente_id, None, fotografia, "editando")
        
        # 3. Retornar la fotografía para el frontend
        return fotografia
    
    def guardar_cambios(self, incidente_id, datos_editados):
        """
        Guarda los cambios y crea nueva fotografía "actual"
        """
        # 1. Aplicar cambios a la BD
        # (Aquí iría la lógica de actualización)
        
        # 2. Crear nueva fotografía con los cambios aplicados
        nueva_fotografia = self.crear_fotografia_completa(incidente_id)
        
        # 3. Guardar como nueva versión "actual"
        self.guardar_fotografia(incidente_id, None, nueva_fotografia, "actual")
        
        # 4. Limpiar archivo de edición
        carpeta_incidente = os.path.join(self.ruta_fotografias, str(incidente_id))
        archivo_editando = os.path.join(carpeta_incidente, "fotografia_editando_ultima.json")
        if os.path.exists(archivo_editando):
            os.remove(archivo_editando)
        
        return nueva_fotografia
    
    def obtener_historial_fotografias(self, incidente_id):
        """
        Obtiene el historial de todas las fotografías
        """
        carpeta_incidente = os.path.join(self.ruta_fotografias, str(incidente_id))
        
        if not os.path.exists(carpeta_incidente):
            return []
        
        archivos = []
        for archivo in os.listdir(carpeta_incidente):
            if archivo.endswith('.json') and not archivo.endswith('_ultima.json'):
                ruta_completa = os.path.join(carpeta_incidente, archivo)
                info = {
                    'archivo': archivo,
                    'fecha': datetime.fromtimestamp(os.path.getmtime(ruta_completa)),
                    'tamaño': os.path.getsize(ruta_completa),
                    'ruta': ruta_completa
                }
                archivos.append(info)
        
        # Ordenar por fecha descendente
        archivos.sort(key=lambda x: x['fecha'], reverse=True)
        return archivos