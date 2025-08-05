#!/usr/bin/env python3
"""Script para cargar incidentes de ejemplo para Sub empresa Surtika spa"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.modules.core.database import get_db_connection
from datetime import datetime, timedelta
import random

def cargar_incidentes_surtika():
    conn = get_db_connection()
    if not conn:
        print("❌ Error de conexión")
        return
        
    cursor = conn.cursor()
    
    try:
        print("\n=== CARGANDO INCIDENTES DE EJEMPLO PARA SURTIKA SPA ===\n")
        
        # Tipos de incidentes de ciberseguridad
        tipos_incidentes = [
            ("Malware", "Detección de software malicioso"),
            ("Phishing", "Intento de suplantación de identidad"),
            ("Acceso no autorizado", "Intento de acceso sin permisos"),
            ("Fuga de información", "Posible filtración de datos"),
            ("Ransomware", "Intento de cifrado malicioso"),
            ("DDoS", "Ataque de denegación de servicio"),
            ("Vulnerabilidad", "Vulnerabilidad detectada en sistema")
        ]
        
        # Estados posibles
        estados = ["Abierto", "Cerrado", "Pendiente", "En Investigación"]
        
        # Criticidades
        criticidades = ["Alta", "Media", "Baja"]
        
        # Sistemas afectados ficticios
        sistemas = [
            "ERP Principal",
            "Sistema de Facturación",
            "Portal Web Corporativo",
            "Servidor de Correo",
            "Base de Datos Clientes",
            "Sistema de Respaldos",
            "Red WiFi Corporativa"
        ]
        
        # Crear 15 incidentes en los últimos 90 días
        incidentes_creados = 0
        
        for i in range(15):
            # Fecha aleatoria en los últimos 90 días
            dias_atras = random.randint(0, 90)
            fecha_creacion = datetime.now() - timedelta(days=dias_atras)
            
            # Seleccionar tipo y estado
            tipo_flujo, descripcion_base = random.choice(tipos_incidentes)
            estado_actual = random.choice(estados)
            criticidad = random.choice(criticidades)
            
            # Si es alta criticidad, más probabilidad de estar abierto
            if criticidad == "Alta" and random.random() > 0.3:
                estado_actual = "Abierto"
            
            # Si el incidente es viejo, más probabilidad de estar cerrado
            if dias_atras > 60 and random.random() > 0.4:
                estado_actual = "Cerrado"
            
            # Generar descripción detallada
            sistema_afectado = random.choice(sistemas)
            descripcion = f"{descripcion_base} detectado en {sistema_afectado}"
            
            # Detalles adicionales según el tipo
            detalles_map = {
                "Malware": f"Se detectó presencia de malware tipo Trojan en {sistema_afectado}. Antivirus corporativo alertó a las {random.randint(8,18)}:{random.randint(0,59):02d}.",
                "Phishing": f"Usuario reportó correo sospechoso simulando ser del área de TI solicitando credenciales. {random.randint(3,15)} usuarios afectados.",
                "Acceso no autorizado": f"Logs muestran {random.randint(10,100)} intentos fallidos de acceso desde IP externa {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.",
                "Fuga de información": f"Detectada transferencia inusual de {random.randint(100,5000)}MB desde {sistema_afectado} hacia servicio externo.",
                "Ransomware": f"Intento de cifrado detectado y bloqueado por sistema de prevención. {random.randint(5,50)} archivos en cuarentena.",
                "DDoS": f"Pico de tráfico anómalo de {random.randint(1000,10000)} requests/segundo hacia {sistema_afectado}.",
                "Vulnerabilidad": f"Scanner de seguridad detectó vulnerabilidad CVE-2024-{random.randint(1000,9999)} en {sistema_afectado}."
            }
            
            descripcion_detallada = detalles_map.get(tipo_flujo, descripcion)
            
            # Impacto
            impactos = [
                f"Afectación parcial de {sistema_afectado}",
                f"Degradación del servicio en un {random.randint(10,50)}%",
                f"{random.randint(5,50)} usuarios afectados",
                "Sin impacto significativo en operaciones",
                f"Interrupción de servicio por {random.randint(15,120)} minutos"
            ]
            
            impacto_operacional = random.choice(impactos)
            
            # Generar ID único
            correlativo = f"INC-{datetime.now().year}-{str(i+1).zfill(4)}"
            
            try:
                cursor.execute("""
                    INSERT INTO Incidentes (
                        EmpresaID, TipoFlujo, FechaCreacion,
                        Titulo, IDVisible, DescripcionInicial, EstadoActual, 
                        Criticidad, ResponsableCliente, SistemasAfectados,
                        FechaDeteccion, FechaOcurrencia, DuracionEstimadaHoras,
                        DescripcionCompleta, CausaRaiz, LeccionesAprendidas
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    3,                             # EmpresaID (Surtika)
                    tipo_flujo,                    # TipoFlujo
                    fecha_creacion,                # FechaCreacion
                    f"Incidente {tipo_flujo} - {sistema_afectado}",  # Titulo
                    correlativo,                   # IDVisible
                    descripcion_detallada,         # DescripcionInicial
                    estado_actual,                 # EstadoActual
                    criticidad,                    # Criticidad
                    "Juan Pérez - Gerente TI",     # ResponsableCliente
                    sistema_afectado,              # SistemasAfectados
                    fecha_creacion,                # FechaDeteccion
                    fecha_creacion,                # FechaOcurrencia
                    random.randint(1, 8),          # DuracionEstimadaHoras
                    f"{descripcion_detallada}\n\nImpacto: {impacto_operacional}",  # DescripcionCompleta
                    f"Análisis pendiente para {tipo_flujo}",  # CausaRaiz
                    f"Reforzar controles de {tipo_flujo.lower()}"  # LeccionesAprendidas
                ))
                
                incidentes_creados += 1
                
            except Exception as e:
                print(f"   ⚠️ Error insertando incidente: {e}")
        
        conn.commit()
        print(f"\n✅ {incidentes_creados} incidentes creados exitosamente")
        
        # Verificar resultados
        print("\n📊 Resumen de incidentes creados:")
        
        # Por tipo
        cursor.execute("""
            SELECT TipoFlujo, COUNT(*) as Cantidad
            FROM Incidentes
            WHERE EmpresaID = 3
            GROUP BY TipoFlujo
            ORDER BY Cantidad DESC
        """)
        
        print("\nPor tipo:")
        for row in cursor.fetchall():
            print(f"  - {row.TipoFlujo}: {row.Cantidad}")
        
        # Por estado
        cursor.execute("""
            SELECT EstadoActual, COUNT(*) as Cantidad
            FROM Incidentes
            WHERE EmpresaID = 3
            GROUP BY EstadoActual
            ORDER BY Cantidad DESC
        """)
        
        print("\nPor estado:")
        for row in cursor.fetchall():
            print(f"  - {row.EstadoActual}: {row.Cantidad}")
        
        # Por criticidad
        cursor.execute("""
            SELECT Criticidad, COUNT(*) as Cantidad
            FROM Incidentes
            WHERE EmpresaID = 3
            GROUP BY Criticidad
            ORDER BY 
                CASE Criticidad
                    WHEN 'Alta' THEN 1
                    WHEN 'Media' THEN 2
                    WHEN 'Baja' THEN 3
                    ELSE 4
                END
        """)
        
        print("\nPor criticidad:")
        for row in cursor.fetchall():
            print(f"  - {row.Criticidad}: {row.Cantidad}")
        
        # Últimos 60 días
        cursor.execute("""
            SELECT COUNT(*) as Total
            FROM Incidentes
            WHERE EmpresaID = 3 
            AND FechaCreacion >= DATEADD(day, -60, GETDATE())
        """)
        
        total_60_dias = cursor.fetchone().Total
        print(f"\nIncidentes en los últimos 60 días: {total_60_dias}")
        
        print("\n=== INCIDENTES CARGADOS EXITOSAMENTE ===")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    cargar_incidentes_surtika()