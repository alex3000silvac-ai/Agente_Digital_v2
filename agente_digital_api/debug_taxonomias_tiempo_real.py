#!/usr/bin/env python3
"""
Debug en tiempo real del guardado de taxonomías
Monitoreará la BD antes y después de guardar para ver exactamente qué pasa
"""

import time
from datetime import datetime

def monitorear_taxonomias(incidente_id=22):
    """Monitorear estado de taxonomías en tiempo real"""
    try:
        from app.database import get_db_connection
        
        print(f"🔍 MONITOREANDO TAXONOMÍAS EN TIEMPO REAL")
        print(f"📋 Incidente ID: {incidente_id}")
        print("=" * 60)
        
        def obtener_estado_actual():
            """Obtener estado actual de las taxonomías"""
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Obtener todas las taxonomías del incidente
            cursor.execute("""
                SELECT 
                    IT.ID,
                    IT.IncidenteID,
                    IT.Id_Taxonomia,
                    IT.Comentarios,
                    IT.FechaAsignacion,
                    IT.CreadoPor,
                    TI.Categoria_del_Incidente,
                    TI.Subcategoria_del_Incidente
                FROM INCIDENTE_TAXONOMIA IT
                LEFT JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
                WHERE IT.IncidenteID = ?
                ORDER BY IT.FechaAsignacion DESC
            """, (incidente_id,))
            
            resultados = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return resultados
        
        # Estado inicial
        print(f"📸 ESTADO INICIAL - {datetime.now().strftime('%H:%M:%S')}")
        estado_inicial = obtener_estado_actual()
        
        print(f"   Taxonomías encontradas: {len(estado_inicial)}")
        for i, tax in enumerate(estado_inicial):
            print(f"   {i+1}. ID_BD: {tax[0]}, Taxonomía: {tax[2]}")
            print(f"      Comentarios: {tax[3][:50] if tax[3] else 'Sin comentarios'}...")
            print(f"      Fecha: {tax[4]}")
            print(f"      Usuario: {tax[5]}")
            print()
        
        # Monitoreo continuo
        print("🔄 INICIANDO MONITOREO CONTINUO...")
        print("   (Haga cambios en el frontend ahora)")
        print("   (Presione Ctrl+C para detener)")
        
        estado_anterior = estado_inicial
        
        while True:
            time.sleep(2)  # Verificar cada 2 segundos
            
            estado_actual = obtener_estado_actual()
            
            # Detectar cambios
            if len(estado_actual) != len(estado_anterior):
                print(f"\n🚨 CAMBIO DETECTADO - {datetime.now().strftime('%H:%M:%S')}")
                print(f"   Taxonomías: {len(estado_anterior)} → {len(estado_actual)}")
                
                if len(estado_actual) > len(estado_anterior):
                    print("   ✅ TAXONOMÍA AGREGADA:")
                    for tax in estado_actual:
                        if tax not in estado_anterior:
                            print(f"      + ID_BD: {tax[0]}, Taxonomía: {tax[2]}")
                            print(f"        Comentarios: {tax[3][:50] if tax[3] else 'Sin comentarios'}...")
                
                elif len(estado_actual) < len(estado_anterior):
                    print("   ❌ TAXONOMÍA ELIMINADA:")
                    for tax in estado_anterior:
                        if tax not in estado_actual:
                            print(f"      - ID_BD: {tax[0]}, Taxonomía: {tax[2]}")
                
                estado_anterior = estado_actual
            
            else:
                # Verificar cambios en comentarios
                cambios_comentarios = False
                for i, tax_actual in enumerate(estado_actual):
                    if i < len(estado_anterior):
                        tax_anterior = estado_anterior[i]
                        if tax_actual[3] != tax_anterior[3]:  # Comentarios cambiaron
                            cambios_comentarios = True
                            print(f"\n📝 COMENTARIO MODIFICADO - {datetime.now().strftime('%H:%M:%S')}")
                            print(f"   Taxonomía: {tax_actual[2]}")
                            print(f"   Antes: {tax_anterior[3][:50] if tax_anterior[3] else 'Sin comentarios'}...")
                            print(f"   Ahora: {tax_actual[3][:50] if tax_actual[3] else 'Sin comentarios'}...")
                
                if cambios_comentarios:
                    estado_anterior = estado_actual
    
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoreo detenido por el usuario")
        
        # Estado final
        print(f"\n📸 ESTADO FINAL - {datetime.now().strftime('%H:%M:%S')}")
        estado_final = obtener_estado_actual()
        
        print(f"   Taxonomías encontradas: {len(estado_final)}")
        for i, tax in enumerate(estado_final):
            print(f"   {i+1}. ID_BD: {tax[0]}, Taxonomía: {tax[2]}")
            print(f"      Comentarios: {tax[3][:50] if tax[3] else 'Sin comentarios'}...")
            print(f"      Fecha: {tax[4]}")
        
    except Exception as e:
        print(f"❌ Error en monitoreo: {e}")
        import traceback
        traceback.print_exc()

def verificar_endpoint_carga():
    """Verificar qué devuelve el endpoint de carga"""
    try:
        print(f"\n🔍 VERIFICANDO ENDPOINT DE CARGA")
        print("=" * 50)
        
        # Simular llamada al endpoint
        from app.modules.admin.incidentes_admin_endpoints import incidentes_admin_bp
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        
        incidente_id = 22
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ejecutar la misma query que usa el endpoint
        cursor.execute("""
            SELECT 
                it.Id_Taxonomia,
                COALESCE(ti.Categoria_del_Incidente + ' - ' + ti.Subcategoria_del_Incidente, ti.Categoria_del_Incidente) as Nombre,
                ti.Area,
                ti.Efecto,
                ti.Categoria_del_Incidente as Categoria,
                ti.Subcategoria_del_Incidente as Subcategoria,
                ti.AplicaTipoEmpresa as Tipo,
                ti.Descripcion,
                it.Comentarios as Justificacion,
                '' as DescripcionProblema,
                it.FechaAsignacion
            FROM INCIDENTE_TAXONOMIA it
            INNER JOIN Taxonomia_incidentes ti ON it.Id_Taxonomia = ti.Id_Incidente
            WHERE it.IncidenteID = ?
        """, (incidente_id,))
        
        taxonomias_rows = cursor.fetchall()
        
        print(f"📊 Query del endpoint encontró: {len(taxonomias_rows)} taxonomías")
        
        for i, row in enumerate(taxonomias_rows):
            tax_data = {
                'id': row[0],
                'nombre': row[1],
                'area': row[2],
                'efecto': row[3],
                'categoria': row[4],
                'subcategoria': row[5],
                'tipo': row[6],
                'descripcion': row[7],
                'justificacion': row[8] or '',
                'descripcionProblema': row[9] or '',
                'fechaSeleccion': row[10].isoformat() if row[10] else None
            }
            
            # Aplicar fix de encoding como en el endpoint real
            tax_data = EncodingFixer.fix_dict(tax_data)
            
            print(f"   {i+1}. ID: {tax_data['id']}")
            print(f"      Nombre: {tax_data['nombre'][:50]}...")
            print(f"      Justificación: {tax_data['justificacion'][:50] if tax_data['justificacion'] else 'Sin justificación'}...")
            print(f"      Fecha: {tax_data['fechaSeleccion']}")
            print()
        
        cursor.close()
        conn.close()
        
        return taxonomias_rows
        
    except Exception as e:
        print(f"❌ Error verificando endpoint: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("🧪 DEBUG EN TIEMPO REAL DE TAXONOMÍAS")
    print("=" * 70)
    
    # Verificar estado del endpoint primero
    verificar_endpoint_carga()
    
    # Luego monitorear cambios
    monitorear_taxonomias()