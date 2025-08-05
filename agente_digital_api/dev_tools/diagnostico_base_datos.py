#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la base de datos SQL Server
sin dependencias de Flask
"""

def verificar_esquema_usuarios():
    """Verifica si la tabla Usuarios tiene los campos necesarios"""
    print("🔍 VERIFICANDO ESQUEMA DE LA TABLA USUARIOS")
    print("="*50)
    
    try:
        import pyodbc
        print("✅ pyodbc está disponible")
    except ImportError:
        print("❌ pyodbc no está instalado")
        print("💡 Instalar con: pip install pyodbc")
        return False
    
    # Configuración de conexión (usar valores por defecto)
    server = 'localhost'
    database = 'AgenteDigitalDB'
    username = 'sa'
    password = ''  # Cambiar según tu configuración
    driver = 'ODBC Driver 17 for SQL Server'
    
    print(f"📡 Intentando conectar a: {server}/{database}")
    
    try:
        # String de conexión
        conn_str = f"""
        DRIVER={{{driver}}};
        SERVER={server};
        DATABASE={database};
        UID={username};
        PWD={password};
        TrustServerCertificate=yes;
        """
        
        conn = pyodbc.connect(conn_str)
        print("✅ Conexión exitosa a SQL Server")
        
        cursor = conn.cursor()
        
        # Verificar si existe la tabla Usuarios
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'Usuarios'
        """)
        
        if cursor.fetchone():
            print("✅ Tabla 'Usuarios' existe")
            
            # Verificar columnas de la tabla Usuarios
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Usuarios'
                ORDER BY ORDINAL_POSITION
            """)
            
            print("\n📋 COLUMNAS DE LA TABLA USUARIOS:")
            print("-" * 40)
            columns = cursor.fetchall()
            
            required_columns = ['UsuarioID', 'Email', 'InquilinoID', 'EmpresaID']
            found_columns = []
            
            for col in columns:
                column_name, data_type, nullable = col
                print(f"  {column_name:<15} | {data_type:<15} | {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                found_columns.append(column_name)
            
            # Verificar columnas requeridas
            print(f"\n🔍 VERIFICANDO COLUMNAS REQUERIDAS:")
            print("-" * 40)
            missing_columns = []
            
            for req_col in required_columns:
                if req_col in found_columns:
                    print(f"✅ {req_col} - Existe")
                else:
                    print(f"❌ {req_col} - FALTA")
                    missing_columns.append(req_col)
            
            if missing_columns:
                print(f"\n⚠️  COLUMNAS FALTANTES: {', '.join(missing_columns)}")
                print("\n💡 SQL PARA AGREGAR COLUMNAS FALTANTES:")
                print("-" * 40)
                
                for col in missing_columns:
                    if col in ['InquilinoID', 'EmpresaID']:
                        print(f"ALTER TABLE Usuarios ADD {col} INT NULL;")
                
            else:
                print("\n✅ Todas las columnas requeridas están presentes")
            
            # Verificar datos de ejemplo
            cursor.execute("SELECT COUNT(*) FROM Usuarios")
            user_count = cursor.fetchone()[0]
            print(f"\n📊 Total de usuarios: {user_count}")
            
            if user_count > 0:
                cursor.execute("""
                    SELECT TOP 3 UsuarioID, Email, InquilinoID, EmpresaID 
                    FROM Usuarios
                """)
                
                print("\n👥 EJEMPLOS DE USUARIOS:")
                print("-" * 60)
                print(f"{'ID':<5} | {'Email':<25} | {'InqID':<6} | {'EmpID':<6}")
                print("-" * 60)
                
                for user in cursor.fetchall():
                    uid, email, inq_id, emp_id = user
                    print(f"{uid:<5} | {email:<25} | {inq_id or 'NULL':<6} | {emp_id or 'NULL':<6}")
        
        else:
            print("❌ Tabla 'Usuarios' NO existe")
            return False
        
        # Verificar tabla Empresas
        print(f"\n🏢 VERIFICANDO TABLA EMPRESAS")
        print("-" * 40)
        
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'Empresas'
        """)
        
        if cursor.fetchone():
            print("✅ Tabla 'Empresas' existe")
            
            cursor.execute("SELECT COUNT(*) FROM Empresas")
            empresa_count = cursor.fetchone()[0]
            print(f"📊 Total de empresas: {empresa_count}")
            
            # Verificar empresa ID 9
            cursor.execute("SELECT EmpresaID, RazonSocial, InquilinoID FROM Empresas WHERE EmpresaID = 9")
            empresa_9 = cursor.fetchone()
            
            if empresa_9:
                print(f"✅ Empresa ID 9 existe: {empresa_9[1]} (Inquilino: {empresa_9[2]})")
            else:
                print("❌ Empresa ID 9 NO existe")
                
                # Mostrar empresas existentes
                cursor.execute("SELECT TOP 5 EmpresaID, RazonSocial, InquilinoID FROM Empresas ORDER BY EmpresaID")
                print("\n🏢 EMPRESAS EXISTENTES:")
                print("-" * 50)
                for emp in cursor.fetchall():
                    print(f"  ID {emp[0]}: {emp[1]} (Inquilino: {emp[2]})")
        
        else:
            print("❌ Tabla 'Empresas' NO existe")
        
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"❌ Error de conexión: {e}")
        print("\n💡 POSIBLES SOLUCIONES:")
        print("1. Verificar que SQL Server esté ejecutándose")
        print("2. Verificar credenciales de conexión")
        print("3. Verificar nombre de la base de datos")
        print("4. Instalar ODBC Driver 17 for SQL Server")
        return False
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def sugerir_soluciones():
    """Sugiere pasos para resolver problemas"""
    print("\n🔧 PASOS PARA RESOLVER PROBLEMAS:")
    print("=" * 50)
    print("1. **Instalar dependencias de Python:**")
    print("   pip install flask flask-cors pyodbc PyJWT Werkzeug flask-login")
    print()
    print("2. **Verificar SQL Server:**")
    print("   - Que esté ejecutándose")
    print("   - Credenciales correctas en config.py")
    print("   - Base de datos 'AgenteDigitalDB' existe")
    print()
    print("3. **Agregar columnas faltantes (si las hay):**")
    print("   ALTER TABLE Usuarios ADD InquilinoID INT NULL;")
    print("   ALTER TABLE Usuarios ADD EmpresaID INT NULL;")
    print()
    print("4. **Ejecutar servidor Flask:**")
    print("   python3 run.py")

if __name__ == "__main__":
    print("🩺 DIAGNÓSTICO DE BASE DE DATOS - AGENTE DIGITAL")
    print("="*60)
    
    if verificar_esquema_usuarios():
        print("\n✅ Diagnóstico completado exitosamente")
    else:
        print("\n❌ Se encontraron problemas en el diagnóstico")
    
    sugerir_soluciones()