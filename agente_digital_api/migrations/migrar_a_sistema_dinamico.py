#!/usr/bin/env python3
"""
Script de migración al sistema dinámico de incidentes
Migra los datos existentes al nuevo esquema con acordeones variables
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db_connection

class MigradorSistemaDinamico:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.estadisticas = {
            'incidentes_migrados': 0,
            'secciones_creadas': 0,
            'comentarios_migrados': 0,
            'archivos_migrados': 0,
            'errores': []
        }
    
    def conectar(self):
        """Establece conexión con la base de datos"""
        self.conn = get_db_connection()
        if not self.conn:
            raise Exception("No se pudo conectar a la base de datos")
        self.cursor = self.conn.cursor()
    
    def cerrar(self):
        """Cierra la conexión"""
        if self.conn:
            self.conn.close()
    
    def ejecutar_migracion(self):
        """Ejecuta el proceso completo de migración"""
        print("🚀 INICIANDO MIGRACIÓN AL SISTEMA DINÁMICO")
        print("=" * 60)
        
        try:
            self.conectar()
            
            # 1. Crear tablas si no existen
            print("\n1️⃣ Verificando estructura de tablas...")
            self.crear_tablas_si_no_existen()
            
            # 2. Cargar configuración de secciones
            print("\n2️⃣ Cargando configuración de secciones...")
            self.cargar_configuracion_secciones()
            
            # 3. Cargar taxonomías como secciones
            print("\n3️⃣ Cargando taxonomías como secciones...")
            self.cargar_taxonomias_como_secciones()
            
            # 4. Migrar incidentes existentes
            print("\n4️⃣ Migrando incidentes existentes...")
            self.migrar_incidentes()
            
            # 5. Migrar evidencias
            print("\n5️⃣ Migrando evidencias...")
            self.migrar_evidencias()
            
            # 6. Migrar comentarios de taxonomías
            print("\n6️⃣ Migrando comentarios de taxonomías...")
            self.migrar_comentarios_taxonomias()
            
            # Confirmar cambios
            self.conn.commit()
            
            # Mostrar resumen
            self.mostrar_resumen()
            
        except Exception as e:
            print(f"\n❌ ERROR EN MIGRACIÓN: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.cerrar()
    
    def crear_tablas_si_no_existen(self):
        """Verifica que las tablas existan"""
        # Verificar si las tablas ya existen
        self.cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'ANCI_SECCIONES_CONFIG'
        """)
        
        if self.cursor.fetchone()[0] == 0:
            print("   ⚠️ Las tablas no existen. Ejecute primero el script SQL crear_sistema_dinamico.sql")
            raise Exception("Tablas del sistema dinámico no encontradas")
        else:
            print("   ✅ Tablas verificadas")
    
    def cargar_configuracion_secciones(self):
        """Carga las 6 secciones fijas si no existen"""
        # Verificar si ya están cargadas
        self.cursor.execute("SELECT COUNT(*) FROM ANCI_SECCIONES_CONFIG WHERE TipoSeccion = 'FIJA'")
        count = self.cursor.fetchone()[0]
        
        if count == 0:
            print("   📝 Insertando secciones fijas...")
            secciones_fijas = [
                ('SEC_1', 'FIJA', 1, 'Información General', 'Datos básicos del incidente', 
                 '{"campos": ["titulo", "fecha_deteccion", "fecha_ocurrencia", "origen", "criticidad"]}', 'info-circle'),
                ('SEC_2', 'FIJA', 2, 'Descripción del Incidente', 'Descripción detallada del incidente', 
                 '{"campos": ["descripcion_detallada", "sistemas_afectados", "servicios_interrumpidos"]}', 'file-text'),
                ('SEC_3', 'FIJA', 3, 'Análisis del Incidente', 'Análisis técnico y de impacto', 
                 '{"campos": ["analisis_tecnico", "impacto_preliminar", "alcance_geografico"]}', 'search'),
                ('SEC_4', 'FIJA', 4, 'Acciones Inmediatas', 'Medidas tomadas inmediatamente', 
                 '{"campos": ["acciones_inmediatas", "responsable_cliente", "medidas_contencion"]}', 'shield'),
                ('SEC_5', 'FIJA', 5, 'Análisis Final', 'Análisis de causa raíz y lecciones', 
                 '{"campos": ["causa_raiz", "lecciones_aprendidas", "plan_mejora"]}', 'check-circle'),
                ('SEC_6', 'FIJA', 6, 'Información ANCI', 'Datos específicos para reporte ANCI', 
                 '{"campos": ["reporte_anci_id", "fecha_declaracion_anci", "tipo_amenaza"]}', 'file-shield')
            ]
            
            for seccion in secciones_fijas:
                self.cursor.execute("""
                    INSERT INTO ANCI_SECCIONES_CONFIG 
                    (CodigoSeccion, TipoSeccion, NumeroOrden, Titulo, Descripcion, CamposJSON, IconoSeccion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, seccion)
            
            print(f"   ✅ {len(secciones_fijas)} secciones fijas cargadas")
        else:
            print(f"   ✅ {count} secciones fijas ya existentes")
    
    def cargar_taxonomias_como_secciones(self):
        """Carga las taxonomías como secciones dinámicas"""
        # Verificar cuántas taxonomías hay como secciones
        self.cursor.execute("SELECT COUNT(*) FROM ANCI_SECCIONES_CONFIG WHERE TipoSeccion = 'TAXONOMIA'")
        count_actual = self.cursor.fetchone()[0]
        
        if count_actual == 0:
            print("   📝 Cargando taxonomías como secciones...")
            
            # Obtener taxonomías activas
            self.cursor.execute("""
                SELECT TOP 35
                    Id_Incidente,
                    Area,
                    Efecto,
                    Categoria_del_Incidente,
                    Subcategoria_del_Incidente,
                    Tipo_Empresa
                FROM TAXONOMIA_INCIDENTES
                WHERE Activo = 1
                ORDER BY Id_Incidente
            """)
            
            taxonomias = self.cursor.fetchall()
            contador = 7  # Empezar después de las 6 secciones fijas
            
            for tax in taxonomias:
                id_tax, area, efecto, categoria, subcategoria, tipo_empresa = tax
                
                # Determinar aplicabilidad
                aplica_oiv = 1 if tipo_empresa in ('OIV', 'AMBAS') else 0
                aplica_pse = 1 if tipo_empresa in ('PSE', 'AMBAS') else 0
                
                self.cursor.execute("""
                    INSERT INTO ANCI_SECCIONES_CONFIG 
                    (CodigoSeccion, TipoSeccion, NumeroOrden, Titulo, Descripcion, 
                     CamposJSON, AplicaOIV, AplicaPSE, IconoSeccion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f'TAX_{id_tax}',
                    'TAXONOMIA',
                    contador,
                    f'{area} - {efecto}',
                    f'Categoría: {categoria} | Subcategoría: {subcategoria}',
                    '{"campos": ["analisis_taxonomia", "evidencias_taxonomia"]}',
                    aplica_oiv,
                    aplica_pse,
                    'tag'
                ))
                
                contador += 1
            
            print(f"   ✅ {len(taxonomias)} taxonomías cargadas como secciones")
        else:
            print(f"   ✅ {count_actual} taxonomías ya cargadas como secciones")
    
    def migrar_incidentes(self):
        """Migra los incidentes existentes al nuevo esquema"""
        print("   📋 Obteniendo incidentes para migrar...")
        
        # Obtener incidentes que no han sido migrados
        self.cursor.execute("""
            SELECT i.IncidenteID, i.EmpresaID, e.Tipo_Empresa
            FROM Incidentes i
            INNER JOIN Empresas e ON i.EmpresaID = e.EmpresaID
            WHERE NOT EXISTS (
                SELECT 1 FROM INCIDENTES_SECCIONES_DATOS 
                WHERE IncidenteID = i.IncidenteID
            )
        """)
        
        incidentes = self.cursor.fetchall()
        print(f"   📊 Incidentes a migrar: {len(incidentes)}")
        
        for incidente_id, empresa_id, tipo_empresa in incidentes:
            try:
                self.migrar_incidente_individual(incidente_id, empresa_id, tipo_empresa)
                self.estadisticas['incidentes_migrados'] += 1
            except Exception as e:
                error_msg = f"Error migrando incidente {incidente_id}: {e}"
                print(f"   ❌ {error_msg}")
                self.estadisticas['errores'].append(error_msg)
    
    def migrar_incidente_individual(self, incidente_id, empresa_id, tipo_empresa):
        """Migra un incidente individual"""
        # Obtener datos actuales del incidente
        self.cursor.execute("""
            SELECT Titulo, DescripcionInicial, AccionesInmediatas,
                   AnciImpactoPreliminar, CausaRaiz, LeccionesAprendidas,
                   PlanMejora, ReporteAnciID, FechaDeclaracionANCI,
                   AnciTipoAmenaza, SistemasAfectados, ServiciosInterrumpidos,
                   AlcanceGeografico, ResponsableCliente
            FROM Incidentes
            WHERE IncidenteID = ?
        """, (incidente_id,))
        
        datos_incidente = self.cursor.fetchone()
        
        # Obtener secciones aplicables según tipo de empresa
        query_secciones = """
            SELECT SeccionID, CodigoSeccion, TipoSeccion
            FROM ANCI_SECCIONES_CONFIG
            WHERE Activo = 1
            AND (
                TipoSeccion = 'FIJA'
                OR (
                    TipoSeccion = 'TAXONOMIA' 
                    AND (
                        (? = 'OIV' AND AplicaOIV = 1)
                        OR (? = 'PSE' AND AplicaPSE = 1)
                        OR (? = 'AMBAS')
                    )
                )
            )
        """
        
        self.cursor.execute(query_secciones, (tipo_empresa, tipo_empresa, tipo_empresa))
        secciones = self.cursor.fetchall()
        
        # Mapear datos existentes a secciones
        for seccion_id, codigo_seccion, tipo_seccion in secciones:
            datos_seccion = {}
            estado = 'VACIO'
            porcentaje = 0
            
            if tipo_seccion == 'FIJA':
                # Mapear datos según la sección
                if codigo_seccion == 'SEC_1':  # Información General
                    datos_seccion = {
                        'titulo': datos_incidente[0] or '',
                        'criticidad': 'Media'  # Default
                    }
                elif codigo_seccion == 'SEC_2':  # Descripción
                    datos_seccion = {
                        'descripcion_detallada': datos_incidente[1] or '',
                        'sistemas_afectados': datos_incidente[10] or '',
                        'servicios_interrumpidos': datos_incidente[11] or ''
                    }
                elif codigo_seccion == 'SEC_3':  # Análisis
                    datos_seccion = {
                        'analisis_tecnico': '',
                        'impacto_preliminar': datos_incidente[3] or '',
                        'alcance_geografico': datos_incidente[12] or ''
                    }
                elif codigo_seccion == 'SEC_4':  # Acciones
                    datos_seccion = {
                        'acciones_inmediatas': datos_incidente[2] or '',
                        'responsable_cliente': datos_incidente[13] or ''
                    }
                elif codigo_seccion == 'SEC_5':  # Análisis Final
                    datos_seccion = {
                        'causa_raiz': datos_incidente[4] or '',
                        'lecciones_aprendidas': datos_incidente[5] or '',
                        'plan_mejora': datos_incidente[6] or ''
                    }
                elif codigo_seccion == 'SEC_6':  # Info ANCI
                    datos_seccion = {
                        'reporte_anci_id': datos_incidente[7] or '',
                        'fecha_declaracion_anci': str(datos_incidente[8]) if datos_incidente[8] else '',
                        'tipo_amenaza': datos_incidente[9] or ''
                    }
                
                # Calcular estado
                if any(datos_seccion.values()):
                    campos_llenos = sum(1 for v in datos_seccion.values() if v)
                    total_campos = len(datos_seccion)
                    porcentaje = int((campos_llenos / total_campos) * 100)
                    estado = 'COMPLETO' if porcentaje == 100 else 'PARCIAL'
            
            # Insertar datos de sección
            self.cursor.execute("""
                INSERT INTO INCIDENTES_SECCIONES_DATOS 
                (IncidenteID, SeccionID, DatosJSON, EstadoSeccion, PorcentajeCompletado, ActualizadoPor)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                incidente_id,
                seccion_id,
                json.dumps(datos_seccion),
                estado,
                porcentaje,
                'Migración'
            ))
            
            self.estadisticas['secciones_creadas'] += 1
    
    def migrar_evidencias(self):
        """Migra las evidencias existentes al nuevo esquema"""
        print("   📎 Migrando evidencias...")
        
        # Obtener evidencias no migradas
        self.cursor.execute("""
            SELECT ei.IncidenteID, ei.EvidenciaID, ei.NombreArchivo, 
                   ei.RutaArchivo, ei.TipoArchivo, ei.TamanoKB,
                   ei.Descripcion, ei.FechaSubida, ei.SubidoPor,
                   ei.Seccion, ei.Version
            FROM EvidenciasIncidentes ei
            WHERE NOT EXISTS (
                SELECT 1 FROM INCIDENTES_ARCHIVOS 
                WHERE IncidenteID = ei.IncidenteID 
                AND NombreOriginal = ei.NombreArchivo
            )
            ORDER BY ei.IncidenteID, ei.Seccion, ei.EvidenciaID
        """)
        
        evidencias = self.cursor.fetchall()
        print(f"   📊 Evidencias a migrar: {len(evidencias)}")
        
        # Mapeo de secciones antiguas a nuevas
        mapeo_secciones = {
            '2': 'SEC_2',  # Descripción
            '3': 'SEC_3',  # Análisis
            '4': 'SEC_4',  # Acciones
            '5': 'SEC_5',  # Análisis Final
        }
        
        evidencias_por_seccion = {}
        
        for evidencia in evidencias:
            incidente_id = evidencia[0]
            seccion_antigua = str(evidencia[9] or '2')  # Default a sección 2
            
            # Determinar código de sección nueva
            codigo_seccion = mapeo_secciones.get(seccion_antigua, 'SEC_2')
            
            # Obtener ID de la sección nueva
            self.cursor.execute("""
                SELECT SeccionID FROM ANCI_SECCIONES_CONFIG 
                WHERE CodigoSeccion = ?
            """, (codigo_seccion,))
            
            result = self.cursor.fetchone()
            if not result:
                continue
            
            seccion_id = result[0]
            
            # Contar evidencias por sección para asignar número
            key = f"{incidente_id}_{seccion_id}"
            if key not in evidencias_por_seccion:
                evidencias_por_seccion[key] = 0
            evidencias_por_seccion[key] += 1
            numero_archivo = evidencias_por_seccion[key]
            
            # Solo migrar si no excede el límite (10 archivos por sección)
            if numero_archivo <= 10:
                # Generar nombre único para servidor
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                nombre_servidor = f"MIG_{timestamp}_{evidencia[1]}_{evidencia[2]}"
                
                try:
                    self.cursor.execute("""
                        INSERT INTO INCIDENTES_ARCHIVOS 
                        (IncidenteID, SeccionID, NumeroArchivo, NombreOriginal, 
                         NombreServidor, RutaArchivo, TipoArchivo, TamanoKB, 
                         Descripcion, FechaSubida, SubidoPor)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        incidente_id,
                        seccion_id,
                        numero_archivo,
                        evidencia[2],  # NombreArchivo
                        nombre_servidor,
                        evidencia[3],  # RutaArchivo
                        evidencia[4] or 'application/octet-stream',
                        evidencia[5] or 0,
                        evidencia[6] or '',
                        evidencia[7],
                        evidencia[8] or 'Migración'
                    ))
                    
                    self.estadisticas['archivos_migrados'] += 1
                except Exception as e:
                    print(f"      ⚠️ Error migrando evidencia {evidencia[1]}: {e}")
    
    def migrar_comentarios_taxonomias(self):
        """Migra los comentarios de taxonomías al nuevo esquema"""
        print("   💬 Migrando comentarios de taxonomías...")
        
        # Obtener comentarios existentes
        self.cursor.execute("""
            SELECT ct.IncidenteID, ct.Id_Taxonomia, ct.NumeroEvidencia,
                   ct.Comentario, ct.FechaCreacion, ct.CreadoPor
            FROM COMENTARIOS_TAXONOMIA ct
            WHERE NOT EXISTS (
                SELECT 1 FROM INCIDENTES_COMENTARIOS ic
                WHERE ic.IncidenteID = ct.IncidenteID
                AND ic.Comentario = ct.Comentario
            )
            ORDER BY ct.IncidenteID, ct.Id_Taxonomia
        """)
        
        comentarios = self.cursor.fetchall()
        print(f"   📊 Comentarios a migrar: {len(comentarios)}")
        
        comentarios_por_seccion = {}
        
        for comentario in comentarios:
            incidente_id, id_taxonomia, numero_evidencia, texto, fecha, usuario = comentario
            
            # Buscar sección correspondiente a la taxonomía
            self.cursor.execute("""
                SELECT SeccionID FROM ANCI_SECCIONES_CONFIG 
                WHERE CodigoSeccion = ? AND TipoSeccion = 'TAXONOMIA'
            """, (f'TAX_{id_taxonomia}',))
            
            result = self.cursor.fetchone()
            if not result:
                continue
            
            seccion_id = result[0]
            
            # Contar comentarios por sección
            key = f"{incidente_id}_{seccion_id}"
            if key not in comentarios_por_seccion:
                comentarios_por_seccion[key] = 0
            comentarios_por_seccion[key] += 1
            numero_comentario = comentarios_por_seccion[key]
            
            # Solo migrar si no excede el límite (6 comentarios por sección)
            if numero_comentario <= 6:
                try:
                    self.cursor.execute("""
                        INSERT INTO INCIDENTES_COMENTARIOS 
                        (IncidenteID, SeccionID, NumeroComentario, Comentario, 
                         TipoComentario, FechaCreacion, CreadoPor)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        incidente_id,
                        seccion_id,
                        numero_comentario,
                        texto,
                        'TAXONOMIA',
                        fecha,
                        usuario or 'Migración'
                    ))
                    
                    self.estadisticas['comentarios_migrados'] += 1
                except Exception as e:
                    print(f"      ⚠️ Error migrando comentario: {e}")
    
    def mostrar_resumen(self):
        """Muestra el resumen de la migración"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE LA MIGRACIÓN")
        print("=" * 60)
        print(f"✅ Incidentes migrados: {self.estadisticas['incidentes_migrados']}")
        print(f"✅ Secciones creadas: {self.estadisticas['secciones_creadas']}")
        print(f"✅ Archivos migrados: {self.estadisticas['archivos_migrados']}")
        print(f"✅ Comentarios migrados: {self.estadisticas['comentarios_migrados']}")
        
        if self.estadisticas['errores']:
            print(f"\n⚠️ Errores encontrados: {len(self.estadisticas['errores'])}")
            for error in self.estadisticas['errores'][:5]:  # Mostrar solo primeros 5
                print(f"   - {error}")
            if len(self.estadisticas['errores']) > 5:
                print(f"   ... y {len(self.estadisticas['errores']) - 5} errores más")
        
        print("\n✅ MIGRACIÓN COMPLETADA")


def main():
    """Función principal"""
    print("\n🚀 MIGRADOR AL SISTEMA DINÁMICO DE INCIDENTES")
    print("=" * 60)
    
    respuesta = input("\n¿Desea continuar con la migración? (s/n): ")
    if respuesta.lower() != 's':
        print("Migración cancelada")
        return
    
    migrador = MigradorSistemaDinamico()
    try:
        migrador.ejecutar_migracion()
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()