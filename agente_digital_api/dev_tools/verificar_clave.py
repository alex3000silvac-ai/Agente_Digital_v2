from werkzeug.security import generate_password_hash, check_password_hash

# --- INGRESA AQUÍ LA CONTRASEÑA EXACTA QUE ESTÁS USANDO PARA PROBAR ---
password_en_texto_plano = "admin123" # Reemplaza "admin123" con tu clave real
# --------------------------------------------------------------------

print(f"1. Verificando la contraseña: '{password_en_texto_plano}'")

# Generamos un hash nuevo en este mismo momento
hash_generado_ahora = generate_password_hash(password_en_texto_plano, method='pbkdf2:sha256')
print(f"2. Hash generado para la prueba: {hash_generado_ahora}")

# Comparamos la contraseña en texto plano contra el hash que acabamos de crear
es_valido = check_password_hash(hash_generado_ahora, password_en_texto_plano)

print("\n--- RESULTADO DE LA VERIFICACIÓN ---")
if es_valido:
    print("✅ PRUEBA EXITOSA: El hash se generó y verificó correctamente.")
    print("Esto confirma que la librería Werkzeug funciona bien en tu ambiente.")
else:
    print("❌ PRUEBA FALLIDA: Algo está mal con la librería Werkzeug o el proceso de hash.")