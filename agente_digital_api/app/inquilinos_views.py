# app/inquilinos_views.py

# --- Parte 1: Importaciones y Configuración ---
# Descripción: Creamos el Blueprint para manejar todo lo relacionado con inquilinos y empresas.
#-----------------------------------------------------------------------------------
from flask import Blueprint, jsonify
from app.database import get_db_connection

inquilinos_bp = Blueprint('inquilinos', __name__, url_prefix='/api/inquilinos')


# --- Parte 2: Ruta para Obtener Todos los Inquilinos ---
# Descripción: Devuelve una lista de todos los inquilinos registrados.
#-----------------------------------------------------------------------------------
@inquilinos_bp.route('/', methods=['GET'])
def get_inquilinos():
    conn = get_db_connection()
    inquilinos = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT InquilinoID, NombreInquilino FROM Inquilinos WHERE Activo = 1 ORDER BY NombreInquilino")
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        inquilinos = [dict(zip(columns, row)) for row in rows]
        conn.close()
    return jsonify(inquilinos)


# --- Parte 3: Ruta para Obtener las Empresas de un Inquilino ---
# Descripción: Devuelve una lista de empresas asociadas a un InquilinoID específico.
#-----------------------------------------------------------------------------------
@inquilinos_bp.route('/<int:inquilino_id>/empresas', methods=['GET'])
def get_empresas_por_inquilino(inquilino_id):
    conn = get_db_connection()
    empresas = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT EmpresaID, NombreEmpresa FROM Empresas WHERE InquilinoID = ? ORDER BY NombreEmpresa", (inquilino_id,))
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        empresas = [dict(zip(columns, row)) for row in rows]
        conn.close()
    return jsonify(empresas)