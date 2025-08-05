#!/usr/bin/env python3
"""
Script para generar el archivo tablas_bd.txt con la estructura actualizada de las tablas
"""

from app.database import get_db_connection
from datetime import datetime

def obtener_estructura_tabla(cursor, tabla):
    cursor.execute(f'''
    SELECT 
        c.COLUMN_NAME,
        c.DATA_TYPE,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.IS_NULLABLE,
        c.COLUMN_DEFAULT,
        CASE 
            WHEN pk.COLUMN_NAME IS NOT NULL THEN 'PK'
            WHEN fk.COLUMN_NAME IS NOT NULL THEN 'FK'
            ELSE ''
        END as CONSTRAINT_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS c
    LEFT JOIN (
        SELECT ku.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
            ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        WHERE tc.TABLE_NAME = '{tabla}'
        AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
    ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
    LEFT JOIN (
        SELECT ku.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
            ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        WHERE tc.TABLE_NAME = '{tabla}'
        AND tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
    ) fk ON c.COLUMN_NAME = fk.COLUMN_NAME
    WHERE c.TABLE_NAME = '{tabla}'
    ORDER BY c.ORDINAL_POSITION
    ''')
    return cursor.fetchall()

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener lista de tablas principales
    tablas = ['Incidentes', 'Empresas', 'INCIDENTE_TAXONOMIA', 'Taxonomia_incidentes', 
              'INCIDENTES_ARCHIVOS', 'Usuarios', 'Inquilinos']
    
    with open('tablas_bd.txt', 'w', encoding='utf-8') as f:
        f.write('=== ESTRUCTURA DE TABLAS - AGENTE DIGITAL ===\n')
        f.write(f'Fecha de generación: {datetime.now()}\n\n')
        
        for tabla in tablas:
            f.write('\n' + '='*60 + '\n')
            f.write(f'TABLA: {tabla}\n')
            f.write('='*60 + '\n\n')
            
            estructura = obtener_estructura_tabla(cursor, tabla)
            
            if estructura:
                # Encabezados
                f.write(f'{"COLUMNA":<30} {"TIPO":<20} {"NULL":<6} {"KEY":<4} {"DEFAULT":<20}\n')
                f.write(f'{"-"*30} {"-"*20} {"-"*6} {"-"*4} {"-"*20}\n')
                
                for col in estructura:
                    nombre = col[0]
                    tipo = col[1]
                    if col[2]:  # Si tiene longitud máxima
                        tipo += f'({col[2]})'
                    nullable = 'YES' if col[3] == 'YES' else 'NO'
                    key = col[5]
                    default = str(col[4]) if col[4] else ''
                    
                    f.write(f'{nombre:<30} {tipo:<20} {nullable:<6} {key:<4} {default:<20}\n')
            else:
                f.write('Tabla no encontrada o sin columnas\n')
                
        # Agregar información adicional sobre relaciones
        f.write('\n\n=== RELACIONES ENTRE TABLAS ===\n\n')
        
        cursor.execute('''
        SELECT 
            fk.TABLE_NAME as 'Tabla',
            fk.COLUMN_NAME as 'Columna FK',
            pk.TABLE_NAME as 'Tabla Referenciada',
            pk.COLUMN_NAME as 'Columna PK'
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk
            ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
            ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
        ORDER BY fk.TABLE_NAME, fk.COLUMN_NAME
        ''')
        
        relaciones = cursor.fetchall()
        if relaciones:
            f.write(f'{"Tabla":<30} {"Columna FK":<20} {"-->":<5} {"Tabla Ref":<30} {"Columna PK":<20}\n')
            f.write(f'{"-"*30} {"-"*20} {"-"*5} {"-"*30} {"-"*20}\n')
            for rel in relaciones:
                f.write(f'{rel[0]:<30} {rel[1]:<20} {"-->":<5} {rel[2]:<30} {rel[3]:<20}\n')
                
        # Agregar notas sobre campos CSIRT
        f.write('\n\n=== NOTAS IMPORTANTES ===\n\n')
        f.write('1. CAMPOS CSIRT (Agregados recientemente):\n')
        f.write('   - SolicitarCSIRT: Indica si se solicita ayuda al CSIRT\n')
        f.write('   - TipoApoyoCSIRT: Tipo de apoyo requerido (Análisis técnico, Contención, etc.)\n')
        f.write('   - UrgenciaCSIRT: Urgencia del apoyo (Alta, Media, Normal)\n')
        f.write('   - ObservacionesCSIRT: Observaciones adicionales para el CSIRT\n')
        f.write('   - TipoRegistro: Tipo de registro del incidente (Para análisis interno, Para Auditoría, Registro General)\n\n')
        
        f.write('2. CAMPOS DE TEXTO CON CAPACIDAD EXTENDIDA (4000 caracteres):\n')
        f.write('   - DescripcionInicial\n')
        f.write('   - AnciImpactoPreliminar\n')
        f.write('   - SistemasAfectados\n')
        f.write('   - ServiciosInterrumpidos\n')
        f.write('   - AccionesInmediatas\n')
        f.write('   - CausaRaiz\n')
        f.write('   - LeccionesAprendidas\n')
        f.write('   - PlanMejora\n')
        f.write('   - ObservacionesCSIRT\n\n')
        
        f.write('3. ARCHIVOS:\n')
        f.write('   - Los archivos se almacenan temporalmente en JSON\n')
        f.write('   - La tabla INCIDENTES_ARCHIVOS está preparada para almacenamiento permanente\n')
        f.write('   - Cada archivo tiene: ID único, nombre, tamaño, tipo, descripción, comentario\n')
                
    cursor.close()
    conn.close()
    print('✅ Archivo tablas_bd.txt creado exitosamente')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()