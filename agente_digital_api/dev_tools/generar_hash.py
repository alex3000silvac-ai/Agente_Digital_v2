from werkzeug.security import generate_password_hash

# Pide al usuario que ingrese la contraseña en la terminal.
password_plano = input("admin123")

# Genera el hash con el método recomendado.
hash_generado = generate_password_hash(password_plano, method='pbkdf2:sha256')

print("\nCopia este hash y pégalo en la columna PasswordHash de tu base de datos:")
print(hash_generado)