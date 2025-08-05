#!/usr/bin/env python3
"""
Script para verificar y reparar la base de datos AgenteDigitalDB
Ejecutar desde la línea de comandos con credenciales de SQL Server
"""

import sys
import os

# Importar la configuración desde el módulo principal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agente_digital_api.config import Config

def conectar_bd():
    """Conecta a la base de datos AgenteDigitalDB usando la configuración de Config."""
    try:
        import pyodbc
    except ImportError:
        print("❌ Error: pyodbc no está instalado")
        print("💡 Instalar con: pip install pyodbc")
        return None
    
    print("* CONFIGURACIÓN DE CONEXIÓN A SQL SERVER (desde config.py)")
    print("="*50)
    
    # Usar la configuración de Config
    servidor = Config.DB_HOST
    base_datos = Config.DB_DATABASE
    usuario = Config.DB_USERNAME
    password = Config.DB_PASSWORD
    driver = Config.DB_DRIVER
    
    print("\n* Conectando a " + f"{servidor}/{base_datos} con usuario {usuario}...")
    
    try:
        conn_str = f"""
        DRIVER={{{driver}}};
        SERVER={servidor};
        DATABASE={base_datos};
        UID={usuario};
        PWD={password};
        TrustServerCertificate=yes;
        """
        
        conn = pyodbc.connect(conn_str)
        print("[OK] Conexión exitosa!")
        return conn
        
    except pyodbc.Error as e:
        print(f"❌ Error de conexión con credenciales: {e}")
        
        # Intentar con autenticación Windows si falla la primera
        print("🔄 Intentando con autenticación Windows...")
        try:
            conn_str_windows = f"""
            DRIVER={{{driver}}};
            SERVER={servidor};
            DATABASE={base_datos};
            Trusted_Connection=yes;
            TrustServerCertificate=yes;
            """
            
            conn = pyodbc.connect(conn_str_windows)
            print("✅ Conexión exitosa con autenticación Windows!")
            return conn
            
        except pyodbc.Error as e2:
            print(f"❌ Error con autenticación Windows: {e2}")
            return None


def verificar_tabla_usuarios(conn):
    """Verifica la estructura de la tabla Usuarios"""
    print("\n* VERIFICANDO TABLA USUARIOS")
    print("="*40)
    
    cursor = conn.cursor()
    
    # Verificar si existe la tabla
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'Usuarios'
    """)
    
    if cursor.fetchone()[0] == 0:
        print("❌ La tabla 'Usuarios' NO existe")
        return False
    
    print("[OK] La tabla 'Usuarios' existe")
    
    # Obtener estructura de la tabla
    cursor.execute("""
        SELECT 
            COLUMN_NAME, 
            DATA_TYPE, 
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Usuarios'
        ORDER BY ORDINAL_POSITION
    """)
    
    columnas = cursor.fetchall()
    
    print(f"\n- ESTRUCTURA ACTUAL (Total: {len(columnas)} columnas):")
    print("-" * 80)
    print(f"{'Columna':<20} | {'Tipo':<15} | {'Longitud':<8} | {'Nullable':<8} | {'Default'}")
    print("-" * 80)
    
    columnas_existentes = []
    for col in columnas:
        nombre, tipo, longitud, nullable, default = col
        columnas_existentes.append(nombre)
        longitud_str = str(longitud) if longitud else "N/A"
        default_str = str(default) if default else "NULL"
        print(f"{nombre:<20} | {tipo:<15} | {longitud_str:<8} | {nullable:<8} | {default_str}")
    
    # Verificar columnas requeridas
    columnas_requeridas = {
        'UsuarioID': 'int',
        'Email': 'nvarchar',
        'PasswordHash': 'nvarchar', 
        'InquilinoID': 'int',
        'EmpresaID': 'int'
    }
    
    print(f"\n* VERIFICANDO COLUMNAS REQUERIDAS:")
    print("-" * 40)
    
    columnas_faltantes = []
    for col_req, tipo_req in columnas_requeridas.items():
        if col_req in columnas_existentes:
            print(f"[OK] {col_req} - Existe")
        else:
            print(f"❌ {col_req} - FALTA")
            columnas_faltantes.append(col_req)
    
    if columnas_faltantes:
        print(f"\n⚠️ COLUMNAS FALTANTES: {', '.join(columnas_faltantes)}")
        return columnas_faltantes
    else:
        print("\n[OK] Todas las columnas requeridas están presentes")
        return []

def verificar_datos_usuarios(conn):
    """Verifica los datos en la tabla Usuarios"""
    print("\n* VERIFICANDO DATOS DE USUARIOS")
    print("-" * 40)
    
    cursor = conn.cursor()
    
    # Contar usuarios
    cursor.execute("SELECT COUNT(*) FROM Usuarios")
    total_usuarios = cursor.fetchone()[0]
    print(f"* Total de usuarios: {total_usuarios}")
    
    if total_usuarios == 0:
        print("⚠️ No hay usuarios en la tabla")
        return
    
    # Verificar usuarios con organización asignada
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN InquilinoID IS NOT NULL THEN 1 ELSE 0 END) as con_inquilino,
            SUM(CASE WHEN EmpresaID IS NOT NULL THEN 1 ELSE 0 END) as con_empresa,
            SUM(CASE WHEN InquilinoID IS NOT NULL AND EmpresaID IS NOT NULL THEN 1 ELSE 0 END) as completos
        FROM Usuarios
    """)
    
    stats = cursor.fetchone()
    total, con_inquilino, con_empresa, completos = stats
    
    print(f"* Usuarios con InquilinoID: {con_inquilino}/{total}")
    print(f"* Usuarios con EmpresaID: {con_empresa}/{total}")
    print(f"* Usuarios completos: {completos}/{total}")
    
    # Mostrar ejemplos
    cursor.execute("""
        SELECT TOP 5 
            UsuarioID, 
            Email, 
            InquilinoID, 
            EmpresaID 
        FROM Usuarios
    """)
    
    print("\n* EJEMPLOS DE USUARIOS:")
    print("-" * 60)
    print(f"{'ID':<5} | {'Email':<25} | {'InqID':<6} | {'EmpID':<6}")
    print("-" * 60)
    
    for user in cursor.fetchall():
        uid, email, inq_id, emp_id = user
        inq_str = str(inq_id) if inq_id is not None else "NULL"
        emp_str = str(emp_id) if emp_id is not None else "NULL"
        print(f"{uid:<5} | {email:<25} | {inq_str:<6} | {emp_str:<6}")

def verificar_tabla_empresas(conn):
    """Verifica la tabla Empresas"""
    print("\n* EJEMPLOS DE USUARIOS:")
    print("-" * 40)
    
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'Empresas'
    """)
    
    if cursor.fetchone()[0] == 0:
        print("❌ La tabla 'Empresas' NO existe")
        return False
    
    print("[OK] La tabla 'Empresas' existe")
    
    # Contar empresas
    cursor.execute("SELECT COUNT(*) FROM Empresas")
    total_empresas = cursor.fetchone()[0]
    print(f"* Total de empresas: {total_empresas}")
    
    # Verificar empresa ID 9 específicamente
    cursor.execute("""
        SELECT EmpresaID, RazonSocial, InquilinoID 
        FROM Empresas 
        WHERE EmpresaID = 9
    """)
    
    empresa_9 = cursor.fetchone()
    if empresa_9:
        print(f"✅ Empresa ID 9 existe: '{empresa_9[1]}' (Inquilino: {empresa_9[2]})")
    else:
        print("[X] Empresa ID 9 NO existe")
        
        # Mostrar empresas disponibles
        cursor.execute("""
            SELECT TOP 10 EmpresaID, RazonSocial, InquilinoID 
            FROM Empresas 
            ORDER BY EmpresaID
        """)
        
        print(f"\n* EMPRESAS DISPONIBLES:")
        print("-" * 50)
        for emp in cursor.fetchall():
            print(f"  ID {emp[0]}: {emp[1]} (Inquilino: {emp[2]})")
    
    return True

def generar_scripts_reparacion(columnas_faltantes):
    """Genera scripts SQL para reparar la base de datos"""
    if not columnas_faltantes:
        return
    
    print("\n* EMPRESAS DISPONIBLES:")
    print("=" * 40)
    
    scripts = []
    
    for columna in columnas_faltantes:
        if columna == 'InquilinoID':
            script = "ALTER TABLE Usuarios ADD InquilinoID INT NULL;"
            scripts.append(script)
            print(f"📝 {script}")
            
        elif columna == 'EmpresaID':
            script = "ALTER TABLE Usuarios ADD EmpresaID INT NULL;"
            scripts.append(script)
            print(f"📝 {script}")
    
    print(f"\n💡 SCRIPT PARA ASIGNAR VALORES INICIALES:")
    print("UPDATE Usuarios SET InquilinoID = 1 WHERE InquilinoID IS NULL;")
    print("UPDATE Usuarios SET EmpresaID = 1 WHERE EmpresaID IS NULL;")
    
    # Guardar scripts en archivo
    with open("reparar_usuarios.sql", "w", encoding="utf-8") as f:
        f.write("-- Scripts de reparación para tabla Usuarios\n")
        f.write("-- Generado automáticamente\n\n")
        
        for script in scripts:
            f.write(script + "\n")
        
        f.write("\n-- Asignar valores iniciales\n")
        f.write("UPDATE Usuarios SET InquilinoID = 1 WHERE InquilinoID IS NULL;\n")
        f.write("UPDATE Usuarios SET EmpresaID = 1 WHERE EmpresaID IS NULL;\n")
    
    print(f"\n💾 Scripts guardados en: reparar_usuarios.sql")

def main():
    """Función principal"""
    print("* DIAGNÓSTICO DE BASE DE DATOS - AGENTE DIGITAL")
    print("="*60)
    print("Base de datos: AgenteDigitalDB")
    print("Servidor: localhost")
    print()
    
    # Conectar a la base de datos
    conn = conectar_bd()
    if not conn:
        print("\n❌ No se pudo conectar a la base de datos")
        print("\n💡 VERIFICAR:")
        print("1. SQL Server está ejecutándose")
        print("2. Base de datos 'AgenteDigitalDB' existe")
        print("3. Credenciales correctas")
        print("4. ODBC Driver 17 for SQL Server instalado")
        return
    
    try:
        # Verificar tabla Usuarios
        columnas_faltantes = verificar_tabla_usuarios(conn)
        
        # Verificar datos
        verificar_datos_usuarios(conn)
        
        # Verificar tabla Empresas
        verificar_tabla_empresas(conn)
        
        # Generar scripts de reparación si es necesario
        if columnas_faltantes:
            generar_scripts_reparacion(columnas_faltantes)
        
        print("\n[OK] DIAGNÓSTICO COMPLETADO")
        
        if columnas_faltantes:
            print("\nACCIONES REQUERIDAS:")
            print("1. Ejecutar scripts de reparación generados")
            print("2. Verificar asignación de usuarios a organizaciones")
        else:
            print("\n[OK] Base de datos está correctamente configurada")
            
    except Exception as e:
        print("\n[ERROR] Error durante el diagnóstico: " + str(e))
        
    finally:
        conn.close()
        print("\n[Cerrada] Conexión cerrada")

if __name__ == "__main__":
    main()