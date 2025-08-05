# app/database_test.py
# Base de datos en memoria para pruebas sin SQL Server

import sqlite3
import os
from datetime import datetime

DB_PATH = "/mnt/c/Pasc/Proyecto_Derecho_Digital/Desarrollos/AgenteDigital_Flask/agente_digital_api/test_agente_digital.db"

def init_test_db():
    """Inicializa la base de datos de prueba con estructura básica"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tablas básicas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Inquilinos (
            InquilinoID INTEGER PRIMARY KEY AUTOINCREMENT,
            RazonSocial TEXT NOT NULL,
            RUT TEXT UNIQUE NOT NULL,
            Estado TEXT DEFAULT 'Activo',
            FechaCreacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            Activo INTEGER DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Empresas (
            EmpresaID INTEGER PRIMARY KEY AUTOINCREMENT,
            InquilinoID INTEGER NOT NULL,
            RazonSocial TEXT NOT NULL,
            RUT TEXT UNIQUE NOT NULL,
            TipoEmpresa TEXT NOT NULL,
            NombreFantasia TEXT,
            EmailContacto TEXT,
            Telefono TEXT,
            FechaCreacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            Activo INTEGER DEFAULT 1,
            FOREIGN KEY (InquilinoID) REFERENCES Inquilinos(InquilinoID)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Incidentes (
            IncidenteID INTEGER PRIMARY KEY AUTOINCREMENT,
            EmpresaID INTEGER NOT NULL,
            Titulo TEXT NOT NULL,
            DescripcionInicial TEXT,
            TipoFlujo TEXT,
            Criticidad TEXT,
            EstadoActual TEXT DEFAULT 'Abierto',
            OrigenIncidente TEXT,
            SistemasAfectados TEXT,
            AccionesInmediatas TEXT,
            ResponsableCliente TEXT,
            FechaCreacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FechaDeteccion DATETIME,
            FOREIGN KEY (EmpresaID) REFERENCES Empresas(EmpresaID)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ReportesANCI (
            ReporteID INTEGER PRIMARY KEY AUTOINCREMENT,
            EmpresaID INTEGER NOT NULL,
            TipoReporte TEXT NOT NULL,
            Titulo TEXT NOT NULL,
            Descripcion TEXT,
            ServiciosAfectados TEXT,
            MedidasImplementadas TEXT,
            FechaIncidente DATETIME,
            Estado TEXT DEFAULT 'Reportado',
            NumeroReporteANCI TEXT,
            FechaCreacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (EmpresaID) REFERENCES Empresas(EmpresaID)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Base de datos de prueba inicializada: {DB_PATH}")

def get_db_connection():
    """Retorna conexión a la base de datos de prueba SQLite"""
    if not os.path.exists(DB_PATH):
        init_test_db()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        # Configurar para devolver resultados como dict
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Error conectando a base de datos de prueba: {e}")
        return None

def reset_test_db():
    """Reinicia la base de datos de prueba"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_test_db()

if __name__ == "__main__":
    # Crear base de datos de prueba
    reset_test_db()