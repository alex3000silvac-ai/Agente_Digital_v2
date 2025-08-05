#!/usr/bin/env python3
"""
Script para generar hash de contraseña para admin123
"""

def generar_hash_password():
    """Genera el hash correcto para la contraseña admin123"""
    
    try:
        import bcrypt
        print("✅ bcrypt disponible")
        
        password = "admin123"
        
        # Generar hash con bcrypt
        salt = bcrypt.gensalt()
        hash_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        hash_str = hash_password.decode('utf-8')
        
        print(f"🔐 Hash generado para 'admin123':")
        print(f"Hash: {hash_str}")
        
        # Verificar que el hash funciona
        if bcrypt.checkpw(password.encode('utf-8'), hash_password):
            print("✅ Hash verificado correctamente")
        else:
            print("❌ Error en la verificación del hash")
        
        return hash_str
        
    except ImportError:
        print("❌ bcrypt no está instalado")
        print("💡 Instalar con: pip install bcrypt")
        
        # Alternativa con hashlib si bcrypt no está disponible
        try:
            import hashlib
            import secrets
            
            print("🔄 Usando hashlib como alternativa...")
            
            password = "admin123"
            salt = secrets.token_hex(16)
            hash_str = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            final_hash = f"pbkdf2_sha256$100000${salt}${hash_str.hex()}"
            
            print(f"🔐 Hash alternativo generado:")
            print(f"Hash: {final_hash}")
            
            return final_hash
            
        except Exception as e:
            print(f"❌ Error generando hash: {e}")
            return None

def verificar_sistema_auth():
    """Verifica el sistema de autenticación de la aplicación"""
    print("\n🔍 VERIFICANDO SISTEMA DE AUTENTICACIÓN")
    print("="*50)
    
    try:
        # Intentar importar auth_utils
        import sys
        import os
        sys.path.append('.')
        
        from app.auth_utils import hash_password, verify_password
        
        print("✅ auth_utils importado correctamente")
        
        # Probar hash y verificación
        test_password = "admin123"
        hashed = hash_password(test_password)
        
        print(f"🔐 Hash generado por auth_utils:")
        print(f"Hash: {hashed}")
        
        # Verificar
        if verify_password(test_password, hashed):
            print("✅ Verificación exitosa con auth_utils")
            return hashed
        else:
            print("❌ Fallo en verificación con auth_utils")
            return None
        
    except ImportError as e:
        print(f"❌ No se pudo importar auth_utils: {e}")
        return None
    except Exception as e:
        print(f"❌ Error en auth_utils: {e}")
        return None

def main():
    print("🔐 GENERADOR DE HASH PARA CONTRASEÑA")
    print("="*40)
    print("Contraseña: admin123")
    print("Usuario: admin@demo.cl")
    print()
    
    # Método 1: Usar el sistema de la aplicación
    hash_app = verificar_sistema_auth()
    
    # Método 2: Generar hash independiente
    hash_independiente = generar_hash_password()
    
    print("\n📋 RESUMEN:")
    print("="*30)
    
    if hash_app:
        print("🎯 USAR ESTE HASH (del sistema de la app):")
        print(f"'{hash_app}'")
        hash_final = hash_app
    elif hash_independiente:
        print("🎯 USAR ESTE HASH (generado independiente):")
        print(f"'{hash_independiente}'")
        hash_final = hash_independiente
    else:
        print("❌ No se pudo generar hash")
        return
    
    # Generar SQL
    print(f"\n📝 SQL PARA ACTUALIZAR USUARIO:")
    print("="*40)
    sql = f"""
UPDATE Usuarios 
SET PasswordHash = '{hash_final}'
WHERE Email = 'admin@demo.cl';
"""
    print(sql)
    
    print("\n💡 PASOS SIGUIENTES:")
    print("1. Ejecutar el SQL de arriba")
    print("2. Reiniciar servidor Flask si es necesario")
    print("3. Intentar login con admin@demo.cl / admin123")

if __name__ == "__main__":
    main()