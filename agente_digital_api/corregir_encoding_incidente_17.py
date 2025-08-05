#!/usr/bin/env python3
"""
Script para corregir el encoding del incidente 17 directamente en la BD
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection

def corregir_texto(texto):
    """Corrige texto mal codificado"""
    if not texto:
        return texto
    
    # Reemplazos específicos para corregir UTF-8 mal interpretado
    reemplazos = {
        # Vocales con tilde
        'Ã¡': 'á',
        'Ã©': 'é',
        'Ã­': 'í', 
        'Ã³': 'ó',
        'Ãº': 'ú',
        'Ã±': 'ñ',
        # Mayúsculas
        'Ã': 'Á',
        'Ã‰': 'É',
        'Ã': 'Í',
        'Ã"': 'Ó',
        'Ãš': 'Ú',
        # Casos específicos completos
        'taxonomÃ­as': 'taxonomías',
        'secciÃ³n': 'sección',
        'descripciÃ³n': 'descripción',
        'informaciÃ³n': 'información',
        'configuraciÃ³n': 'configuración',
        'aplicaciÃ³n': 'aplicación',
        'exfiltraciÃ³n': 'exfiltración',
        'exposiciÃ³n': 'exposición',
        'tambiÃ©n': 'también',
        'mÃ¡s': 'más',
        'asÃ­': 'así',
        'categorÃ­a': 'categoría',
        'gestiÃ³n': 'gestión',
        'validaciÃ³n': 'validación',
        'implementaciÃ³n': 'implementación',
        'documentaciÃ³n': 'documentación',
        'autenticaciÃ³n': 'autenticación',
        'actualizaciÃ³n': 'actualización',
        'eliminaciÃ³n': 'eliminación',
        'integraciÃ³n': 'integración',
        'mitigaciÃ³n': 'mitigación',
        'detecciÃ³n': 'detección',
        'prevenciÃ³n': 'prevención',
        'evaluaciÃ³n': 'evaluación',
        'investigaciÃ³n': 'investigación',
        'clasificaciÃ³n': 'clasificación',
        'notificaciÃ³n': 'notificación'
    }
    
    texto_corregido = texto
    for mal, bien in reemplazos.items():
        texto_corregido = texto_corregido.replace(mal, bien)
    
    return texto_corregido

def corregir_incidente():
    """Corrige el encoding del incidente 17"""
    
    incidente_id = 17
    print(f"🔧 CORRIGIENDO ENCODING DEL INCIDENTE {incidente_id}")
    print("=" * 60)
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Error de conexión a BD")
            return
            
        cursor = conn.cursor()
        
        # 1. Obtener datos actuales
        print("\n1️⃣ OBTENIENDO DATOS ACTUALES...")
        cursor.execute("""
            SELECT Titulo, DescripcionInicial, AccionesInmediatas, 
                   AnciImpactoPreliminar, AnciTipoAmenaza, CausaRaiz,
                   LeccionesAprendidas, PlanMejora
            FROM Incidentes 
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        row = cursor.fetchone()
        if not row:
            print("❌ Incidente no encontrado")
            return
        
        # 2. Corregir cada campo
        print("\n2️⃣ CORRIGIENDO CAMPOS...")
        campos_corregidos = []
        
        campos = ['Titulo', 'DescripcionInicial', 'AccionesInmediatas', 
                 'AnciImpactoPreliminar', 'AnciTipoAmenaza', 'CausaRaiz',
                 'LeccionesAprendidas', 'PlanMejora']
        
        for i, campo in enumerate(campos):
            valor_original = row[i]
            if valor_original:
                valor_corregido = corregir_texto(valor_original)
                if valor_original != valor_corregido:
                    print(f"   ✅ {campo}:")
                    print(f"      Antes: {valor_original[:50]}...")
                    print(f"      Después: {valor_corregido[:50]}...")
                    campos_corregidos.append((campo, valor_corregido))
                else:
                    print(f"   ⚪ {campo}: Sin cambios necesarios")
        
        # 3. Actualizar en BD
        if campos_corregidos:
            print(f"\n3️⃣ ACTUALIZANDO {len(campos_corregidos)} CAMPOS EN BD...")
            
            for campo, valor in campos_corregidos:
                query = f"UPDATE Incidentes SET {campo} = ? WHERE IncidenteID = ?"
                cursor.execute(query, (valor, incidente_id))
            
            conn.commit()
            print("✅ Cambios guardados exitosamente")
        else:
            print("\n✅ No se necesitaron correcciones")
        
        # 4. Verificar estructura de evidencias
        print("\n4️⃣ VERIFICANDO ESTRUCTURA DE EVIDENCIAS...")
        
        # Verificar columnas disponibles
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'EvidenciasIncidentes'
            ORDER BY ORDINAL_POSITION
        """)
        
        columnas = [row[0] for row in cursor.fetchall()]
        print(f"   Columnas disponibles: {columnas}")
        
        # Buscar evidencias
        cursor.execute("""
            SELECT EvidenciaID, NombreArchivo, Descripcion, Version
            FROM EvidenciasIncidentes 
            WHERE IncidenteID = ?
            ORDER BY EvidenciaID
        """, (incidente_id,))
        
        evidencias = cursor.fetchall()
        print(f"\n   Total evidencias: {len(evidencias)}")
        
        # Agrupar por descripción para detectar sección
        evidencias_por_seccion = {
            'descripcion': [],
            'analisis': [],
            'acciones': [],
            'analisis-final': []
        }
        
        for ev in evidencias:
            ev_id, nombre, desc, version = ev
            desc_str = str(desc or '')
            
            # Clasificar por descripción numérica
            if desc_str in ['1', '2']:
                seccion = 'descripcion'
            elif desc_str == '3':
                seccion = 'analisis'
            elif desc_str == '4':
                seccion = 'acciones'
            elif desc_str == '12':
                seccion = 'analisis-final'
            else:
                # Por defecto a descripción
                seccion = 'descripcion'
            
            evidencias_por_seccion[seccion].append({
                'id': ev_id,
                'nombre': nombre,
                'descripcion': desc,
                'version': version
            })
        
        print("\n   DISTRIBUCIÓN DE EVIDENCIAS:")
        for seccion, archivos in evidencias_por_seccion.items():
            print(f"   - {seccion}: {len(archivos)} archivos")
            for archivo in archivos:
                print(f"      • ID:{archivo['id']} | {archivo['nombre']} | Desc: {archivo['descripcion']}")
        
        # 5. Verificar taxonomías
        print("\n5️⃣ VERIFICANDO TAXONOMÍAS...")
        cursor.execute("""
            SELECT COUNT(*) FROM INCIDENTE_TAXONOMIA WHERE IncidenteID = ?
        """, (incidente_id,))
        num_taxonomias = cursor.fetchone()[0]
        print(f"   Taxonomías asignadas: {num_taxonomias}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM EVIDENCIAS_TAXONOMIA WHERE IncidenteID = ?
        """, (incidente_id,))
        num_ev_tax = cursor.fetchone()[0]
        print(f"   Evidencias de taxonomías: {num_ev_tax}")
        
        print("\n✅ PROCESO COMPLETADO")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    corregir_incidente()