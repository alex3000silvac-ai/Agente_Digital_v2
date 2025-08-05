#!/usr/bin/env python3
"""
Debug completo del problema de taxonomías en UI
"""

def debug_taxonomias_ui():
    """Verificar qué está pasando con las taxonomías"""
    try:
        print("🔍 DEBUG COMPLETO DE TAXONOMÍAS EN UI")
        print("=" * 80)
        
        from app.database import get_db_connection
        import json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Verificar qué hay guardado en la BD
        print("\n1️⃣ TAXONOMÍAS GUARDADAS EN BD PARA INCIDENTE 25:")
        cursor.execute("""
            SELECT 
                IT.Id_Taxonomia,
                IT.Comentarios,
                IT.FechaAsignacion,
                TI.Subcategoria_del_Incidente as Nombre
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = 25
        """)
        
        taxonomias_guardadas = cursor.fetchall()
        print(f"   Total guardadas: {len(taxonomias_guardadas)}")
        
        for tax in taxonomias_guardadas:
            print(f"\n   📋 ID: {tax[0]}")
            print(f"      Nombre: {tax[3]}")
            print(f"      Comentarios: {tax[1][:50] if tax[1] else 'SIN COMENTARIOS'}...")
            print(f"      Fecha: {tax[2]}")
        
        # 2. Simular lo que devuelve el endpoint cargar_completo
        print("\n2️⃣ SIMULACIÓN DE ENDPOINT cargar_completo:")
        
        # Query exacta del endpoint
        cursor.execute("""
            SELECT 
                IT.Id_Taxonomia,
                TI.Subcategoria_del_Incidente as Categoria_del_Incidente,
                TI.Descripcion,
                TI.AplicaTipoEmpresa,
                IT.Comentarios,
                IT.FechaAsignacion,
                IT.CreadoPor,
                TI.Categoria_del_Incidente as Categoria
            FROM INCIDENTE_TAXONOMIA IT
            INNER JOIN Taxonomia_incidentes TI ON IT.Id_Taxonomia = TI.Id_Incidente
            WHERE IT.IncidenteID = 25
        """)
        
        columns = [column[0] for column in cursor.description]
        taxonomias = []
        
        for row in cursor.fetchall():
            tax = dict(zip(columns, row))
            
            # Procesar como lo hace el endpoint
            # Parsear justificación y descripción
            if tax.get('Comentarios'):
                comentarios = tax['Comentarios']
                if 'Justificación:' in comentarios:
                    parts = comentarios.split('Justificación:', 1)
                    if len(parts) > 1:
                        justif_parts = parts[1].split('\n', 1)
                        tax['justificacion'] = justif_parts[0].strip()
                        
                        if len(justif_parts) > 1 and 'Descripción del problema:' in justif_parts[1]:
                            desc_parts = justif_parts[1].split('Descripción del problema:', 1)
                            if len(desc_parts) > 1:
                                tax['descripcionProblema'] = desc_parts[1].strip()
                            else:
                                tax['descripcionProblema'] = ''
                        else:
                            tax['descripcionProblema'] = ''
                else:
                    tax['justificacion'] = comentarios
                    tax['descripcionProblema'] = ''
            else:
                tax['justificacion'] = ''
                tax['descripcionProblema'] = ''
            
            # Agregar campos que espera el frontend
            tax['id'] = tax['Id_Taxonomia']
            tax['nombre'] = tax.get('Categoria_del_Incidente', '')
            tax['archivos'] = []  # Por ahora vacío
            
            taxonomias.append(tax)
        
        print(f"\n   Taxonomías que se enviarían: {len(taxonomias)}")
        
        # Mostrar estructura JSON
        print("\n   ESTRUCTURA JSON QUE SE ENVIARÍA:")
        # Convertir datetime a string para poder mostrar
        for tax in taxonomias:
            if tax.get('FechaAsignacion'):
                tax['FechaAsignacion'] = str(tax['FechaAsignacion'])
        
        if taxonomias:
            print(json.dumps(taxonomias[0], indent=2, ensure_ascii=False))
        
        # 3. Verificar qué espera el frontend
        print("\n3️⃣ LO QUE ESPERA EL FRONTEND:")
        print("   - Campo 'id' (string): ID de la taxonomía")
        print("   - Campo 'nombre' (string): Nombre de la taxonomía")
        print("   - Campo 'justificacion' (string): Justificación")
        print("   - Campo 'descripcionProblema' (string): Descripción del problema")
        print("   - Campo 'archivos' (array): Lista de archivos")
        
        # 4. Verificar si hay algún problema
        print("\n4️⃣ VERIFICACIÓN DE PROBLEMAS:")
        
        if len(taxonomias) == 0:
            print("   ❌ NO HAY TAXONOMÍAS GUARDADAS para el incidente 25")
        else:
            tax_ejemplo = taxonomias[0]
            campos_requeridos = ['id', 'nombre', 'justificacion', 'descripcionProblema', 'archivos']
            campos_faltantes = [c for c in campos_requeridos if c not in tax_ejemplo]
            
            if campos_faltantes:
                print(f"   ❌ Faltan campos: {campos_faltantes}")
            else:
                print("   ✅ Todos los campos requeridos están presentes")
                
            # Verificar valores
            if not tax_ejemplo.get('id'):
                print("   ❌ El campo 'id' está vacío")
            if not tax_ejemplo.get('nombre'):
                print("   ❌ El campo 'nombre' está vacío")
        
        # 5. Generar comandos para verificar en el navegador
        print("\n5️⃣ COMANDOS PARA EJECUTAR EN LA CONSOLA DEL NAVEGADOR:")
        print("""
// 1. Verificar si el componente está recibiendo las taxonomías
const vm = document.querySelector('[data-v-]').__vue__?.proxy || window.vm;
console.log('Taxonomías seleccionadas en el componente:', vm?.taxonomiasSeleccionadas);

// 2. Verificar la función que determina si está seleccionada
const taxId = 'INC_USO_PHIP_ECDP';
console.log('¿Está seleccionada?', vm?.taxonomiaSeleccionada(taxId));

// 3. Forzar que se muestre como seleccionada
const elemento = document.querySelector(`[data-taxonomy-id="${taxId}"]`);
if (elemento) {
    elemento.classList.add('seleccionada');
    console.log('✅ Taxonomía marcada manualmente como seleccionada');
}
""")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_taxonomias_ui()