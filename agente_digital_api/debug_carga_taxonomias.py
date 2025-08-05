#!/usr/bin/env python3
"""
Debug detallado de la carga de taxonomías
"""

def debug_proceso_carga():
    """Debug paso a paso del proceso de carga"""
    try:
        print("🔍 DEBUG DETALLADO - PROCESO DE CARGA DE TAXONOMÍAS")
        print("=" * 80)
        
        # Importar el módulo directamente
        import sys
        sys.path.append('/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api')
        
        from app.views.incidente_cargar_completo import cargar_incidente_completo
        from flask import Flask, g
        
        # Crear contexto Flask mínimo
        app = Flask(__name__)
        
        with app.app_context():
            # Simular usuario
            g.current_user_id = 1
            g.current_user_rol = 'admin'
            g.current_user_email = 'test@test.com'
            g.current_user_nombre = 'Test User'
            
            print("\n1️⃣ LLAMANDO A cargar_incidente_completo(25)...")
            
            try:
                response = cargar_incidente_completo(25)
                
                if hasattr(response, 'get_json'):
                    data = response.get_json()
                else:
                    data = response
                
                print("\n2️⃣ RESPUESTA RECIBIDA:")
                
                if isinstance(data, dict):
                    if 'taxonomias_seleccionadas' in data:
                        taxonomias = data['taxonomias_seleccionadas']
                        print(f"\n✅ taxonomias_seleccionadas encontradas: {len(taxonomias)} elementos")
                        
                        for i, tax in enumerate(taxonomias, 1):
                            print(f"\n📋 Taxonomía {i}:")
                            print(f"   Claves disponibles: {list(tax.keys())}")
                            print(f"   - id: '{tax.get('id', 'NO EXISTE')}'")
                            print(f"   - Id_Taxonomia: '{tax.get('Id_Taxonomia', 'NO EXISTE')}'")
                            print(f"   - justificacion: '{tax.get('justificacion', 'NO EXISTE')}'")
                            print(f"   - descripcionProblema: '{tax.get('descripcionProblema', 'NO EXISTE')}'")
                            print(f"   - nombre: '{tax.get('nombre', 'NO EXISTE')}'")
                            
                            # Verificar problemas
                            problemas = []
                            if not tax.get('id'):
                                problemas.append("FALTA campo 'id'")
                            if not tax.get('justificacion'):
                                problemas.append("FALTA justificacion")
                            if not tax.get('descripcionProblema'):
                                problemas.append("FALTA descripcionProblema")
                            
                            if problemas:
                                print(f"   ❌ PROBLEMAS: {', '.join(problemas)}")
                            else:
                                print(f"   ✅ TODOS LOS CAMPOS PRESENTES")
                    else:
                        print("\n❌ NO HAY 'taxonomias_seleccionadas' en la respuesta")
                        print(f"Claves disponibles: {list(data.keys())}")
                else:
                    print(f"\n❌ Respuesta no es un diccionario: {type(data)}")
                    
            except Exception as e:
                print(f"\n❌ Error al llamar endpoint: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_proceso_carga()