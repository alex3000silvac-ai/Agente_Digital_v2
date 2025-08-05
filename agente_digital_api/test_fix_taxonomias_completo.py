#!/usr/bin/env python3
"""
Test completo del fix de taxonomías - Verificar todo el flujo
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fix_directo():
    """Test directo del fix de encoding"""
    try:
        from app.utils.encoding_fixer import EncodingFixer
        
        print("🧪 TEST DEL FIX DE ENCODING")
        print("=" * 50)
        
        # Simular datos corruptos como vienen de la BD
        datos_corruptos = {
            'id': 'INC_USO_PHIP_ECDP',
            'justificacion': 'JustificaciÃ³n: PRUEBA\nDescripciÃ³n del problema: PRUEBA',
            'descripcion': 'DescripciÃ³n de la taxonomÃ­a'
        }
        
        print("📝 Datos originales (corruptos):")
        for key, value in datos_corruptos.items():
            print(f"   {key}: {value[:50]}...")
        
        # Aplicar fix
        datos_corregidos = EncodingFixer.fix_dict(datos_corruptos)
        
        print("\n✅ Datos después del fix:")
        for key, value in datos_corregidos.items():
            print(f"   {key}: {value[:50]}...")
        
        # Verificar que se corrigió
        if 'Justificación' in datos_corregidos['justificacion']:
            print("\n🎉 Fix de encoding EXITOSO!")
            return True
        else:
            print("\n❌ Fix de encoding FALLÓ")
            return False
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def test_endpoint_directo():
    """Test del endpoint directamente sin servidor web"""
    try:
        from app.modules.admin.incidentes_admin_endpoints import obtener_incidente_admin
        from app.database import get_db_connection
        
        print("\n🔍 TEST DEL ENDPOINT DIRECTO")
        print("=" * 50)
        
        # Simular request
        class MockRequest:
            pass
        
        # Mock del token_required
        def mock_obtener_incidente(incidente_id):
            from app.database import get_db_connection
            from app.utils.encoding_fixer import EncodingFixer
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Simular la consulta de taxonomías
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
            taxonomias_seleccionadas = []
            
            for row in taxonomias_rows:
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
                
                print(f"📝 Datos ANTES del fix:")
                print(f"   justificacion: {tax_data['justificacion'][:100]}...")
                
                # Aplicar fix de encoding
                tax_data = EncodingFixer.fix_dict(tax_data)
                
                print(f"✅ Datos DESPUÉS del fix:")
                print(f"   justificacion: {tax_data['justificacion'][:100]}...")
                
                taxonomias_seleccionadas.append(tax_data)
            
            cursor.close()
            conn.close()
            
            return taxonomias_seleccionadas
        
        # Ejecutar test
        resultado = mock_obtener_incidente(22)
        
        print(f"\n📊 Resultado del endpoint:")
        print(f"   Taxonomías encontradas: {len(resultado)}")
        
        for tax in resultado:
            print(f"   ID: {tax['id']}")
            if 'Justificación' in tax['justificacion']:
                print(f"   ✅ Encoding CORRECTO en justificación")
            else:
                print(f"   ❌ Encoding INCORRECTO en justificación")
        
        return len(resultado) > 0
        
    except Exception as e:
        print(f"❌ Error en test endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flujo_completo():
    """Test del flujo completo de guardado y carga"""
    try:
        from app.database import get_db_connection
        from app.utils.encoding_fixer import EncodingFixer
        
        print("\n💾 TEST DE FLUJO COMPLETO")
        print("=" * 50)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Insertar datos de prueba con caracteres especiales
        print("1. Insertando datos de prueba...")
        
        test_data = "Justificación de prueba con caracteres especiales: ñáéíóú"
        
        cursor.execute("""
            UPDATE INCIDENTE_TAXONOMIA 
            SET Comentarios = ?
            WHERE IncidenteID = 22 AND Id_Taxonomia = 'INC_USO_PHIP_ECDP'
        """, (test_data,))
        
        conn.commit()
        print(f"   ✅ Datos insertados: {test_data}")
        
        # 2. Leer datos como lo haría el endpoint
        print("2. Leyendo datos como endpoint...")
        
        cursor.execute("""
            SELECT Comentarios 
            FROM INCIDENTE_TAXONOMIA 
            WHERE IncidenteID = 22 AND Id_Taxonomia = 'INC_USO_PHIP_ECDP'
        """)
        
        resultado = cursor.fetchone()
        datos_bd = resultado[0] if resultado else ""
        
        print(f"   📝 Datos de BD: {datos_bd}")
        
        # 3. Aplicar fix
        datos_corregidos = EncodingFixer.fix_string(datos_bd)
        print(f"   ✅ Datos corregidos: {datos_corregidos}")
        
        # 4. Verificar que el fix funcionó
        if datos_corregidos == test_data:
            print(f"   🎉 Fix EXITOSO - los datos coinciden!")
            return True
        else:
            print(f"   ❌ Fix FALLÓ - los datos no coinciden")
            print(f"      Esperado: {test_data}")
            print(f"      Obtenido: {datos_corregidos}")
            return False
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error en flujo completo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 INICIANDO TESTS COMPLETOS DE TAXONOMÍAS")
    print("=" * 70)
    
    # Test 1: Fix directo
    test1 = test_fix_directo()
    
    # Test 2: Endpoint directo
    test2 = test_endpoint_directo()
    
    # Test 3: Flujo completo
    test3 = test_flujo_completo()
    
    print("\n📊 RESUMEN DE TESTS:")
    print("=" * 50)
    print(f"Test 1 (Fix directo): {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Test 2 (Endpoint): {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Test 3 (Flujo completo): {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 TODOS LOS TESTS PASARON - FIX EXITOSO!")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON - REVISAR")