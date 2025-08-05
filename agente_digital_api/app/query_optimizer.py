# app/query_optimizer.py
# Optimizador de queries para escalabilidad y performance

import logging
import time
from functools import wraps
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from sqlalchemy import text

from .cache_manager import cache_manager, cached
from .database_pool import db_manager

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Optimizador de queries con caching inteligente y monitoreo de performance"""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 segundo
        
    def _log_query_performance(self, query_name: str, execution_time: float, result_count: int = 0):
        """Registrar performance de queries"""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = {
                'total_executions': 0,
                'total_time': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf'),
                'slow_queries': 0
            }
        
        stats = self.query_stats[query_name]
        stats['total_executions'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['total_executions']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)
        
        if execution_time > self.slow_query_threshold:
            stats['slow_queries'] += 1
            logger.warning(f"Query lenta detectada: {query_name} - {execution_time:.2f}s - {result_count} resultados")
        
        logger.debug(f"Query {query_name}: {execution_time:.3f}s - {result_count} resultados")

def monitor_query(query_name: str):
    """Decorador para monitorear performance de queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            result_count = 0
            if isinstance(result, (list, tuple)):
                result_count = len(result)
            elif result is not None:
                result_count = 1
                
            query_optimizer._log_query_performance(query_name, execution_time, result_count)
            return result
        return wrapper
    return decorator

# Instancia global
query_optimizer = QueryOptimizer()

# ============================================================================
# QUERIES OPTIMIZADAS PARA INQUILINOS
# ============================================================================

@monitor_query("get_inquilinos_list")
@cached(timeout=1800, namespace="inquilinos")  # 30 minutos
def get_inquilinos_optimized(filtros: Optional[Dict] = None) -> List[Dict]:
    """Obtener lista de inquilinos con filtros optimizada"""
    
    base_query = """
    SELECT 
        i.InquilinoID,
        i.RazonSocial,
        i.RUT,
        i.Email,
        i.Telefono,
        i.Activo,
        i.FechaCreacion,
        COUNT(DISTINCT e.EmpresaID) as TotalEmpresas,
        COUNT(DISTINCT u.UsuarioID) as TotalUsuarios
    FROM Inquilinos i
    LEFT JOIN Empresas e ON i.InquilinoID = e.InquilinoID
    LEFT JOIN Usuarios u ON i.InquilinoID = u.InquilinoID
    """
    
    where_conditions = ["i.Activo = 1"]  # Solo inquilinos activos
    params = {}
    
    if filtros:
        if filtros.get('busqueda'):
            where_conditions.append("(i.RazonSocial LIKE :busqueda OR i.RUT LIKE :busqueda)")
            params['busqueda'] = f"%{filtros['busqueda']}%"
        
        if filtros.get('activo') is not None:
            where_conditions[-1] = "i.Activo = :activo"  # Reemplazar condición por defecto
            params['activo'] = 1 if filtros['activo'] else 0
    
    if where_conditions:
        base_query += " WHERE " + " AND ".join(where_conditions)
    
    base_query += """
    GROUP BY i.InquilinoID, i.RazonSocial, i.RUT, i.Email, i.Telefono, i.Activo, i.FechaCreacion
    ORDER BY i.RazonSocial
    """
    
    return db_manager.execute_query(base_query, params, fetch_all=True)

@monitor_query("get_inquilino_detail")
@cached(timeout=900, namespace="inquilinos")  # 15 minutos
def get_inquilino_detail_optimized(inquilino_id: int) -> Optional[Dict]:
    """Obtener detalles de un inquilino específico"""
    
    query = """
    SELECT 
        i.InquilinoID,
        i.RazonSocial,
        i.RUT,
        i.Email,
        i.Telefono,
        i.Direccion,
        i.Ciudad,
        i.Region,
        i.CodigoPostal,
        i.Activo,
        i.FechaCreacion,
        i.FechaActualizacion,
        COUNT(DISTINCT e.EmpresaID) as TotalEmpresas,
        COUNT(DISTINCT u.UsuarioID) as TotalUsuarios,
        COUNT(DISTINCT inc.IncidenteID) as TotalIncidentes
    FROM Inquilinos i
    LEFT JOIN Empresas e ON i.InquilinoID = e.InquilinoID
    LEFT JOIN Usuarios u ON i.InquilinoID = u.InquilinoID
    LEFT JOIN Incidentes inc ON e.EmpresaID = inc.EmpresaID
    WHERE i.InquilinoID = :inquilino_id
    GROUP BY i.InquilinoID, i.RazonSocial, i.RUT, i.Email, i.Telefono, 
             i.Direccion, i.Ciudad, i.Region, i.CodigoPostal, i.Activo, 
             i.FechaCreacion, i.FechaActualizacion
    """
    
    return db_manager.execute_query(query, {'inquilino_id': inquilino_id}, fetch_one=True)

# ============================================================================
# QUERIES OPTIMIZADAS PARA EMPRESAS
# ============================================================================

@monitor_query("get_empresas_by_inquilino")
@cached(timeout=900, namespace="empresas")  # 15 minutos
def get_empresas_by_inquilino_optimized(inquilino_id: int) -> List[Dict]:
    """Obtener empresas de un inquilino con estadísticas"""
    
    query = """
    SELECT 
        e.EmpresaID,
        e.InquilinoID,
        e.RazonSocial,
        e.NombreComercial,
        e.RUT,
        e.TipoEmpresa,
        e.Sector,
        e.Email,
        e.Telefono,
        e.Activo,
        e.FechaCreacion,
        COUNT(DISTINCT u.UsuarioID) as TotalUsuarios,
        COUNT(DISTINCT inc.IncidenteID) as TotalIncidentes,
        COUNT(DISTINCT CASE WHEN inc.EstadoActual = 'Abierto' THEN inc.IncidenteID END) as IncidentesAbiertos,
        COUNT(DISTINCT ce.ObligacionID) as TotalObligaciones
    FROM Empresas e
    LEFT JOIN Usuarios u ON e.EmpresaID = u.EmpresaID
    LEFT JOIN Incidentes inc ON e.EmpresaID = inc.EmpresaID
    LEFT JOIN CumplimientoEmpresa ce ON e.EmpresaID = ce.EmpresaID
    WHERE e.InquilinoID = :inquilino_id AND e.Activo = 1
    GROUP BY e.EmpresaID, e.InquilinoID, e.RazonSocial, e.NombreComercial, 
             e.RUT, e.TipoEmpresa, e.Sector, e.Email, e.Telefono, e.Activo, e.FechaCreacion
    ORDER BY e.RazonSocial
    """
    
    return db_manager.execute_query(query, {'inquilino_id': inquilino_id}, fetch_all=True)

@monitor_query("get_empresa_dashboard")
@cached(timeout=600, namespace="empresas")  # 10 minutos
def get_empresa_dashboard_optimized(empresa_id: int) -> Dict:
    """Obtener datos del dashboard de empresa optimizado"""
    
    # Query principal para estadísticas
    stats_query = """
    SELECT 
        e.EmpresaID,
        e.RazonSocial,
        e.TipoEmpresa,
        COUNT(DISTINCT u.UsuarioID) as TotalUsuarios,
        COUNT(DISTINCT inc.IncidenteID) as TotalIncidentes,
        COUNT(DISTINCT CASE WHEN inc.EstadoActual = 'Abierto' THEN inc.IncidenteID END) as IncidentesAbiertos,
        COUNT(DISTINCT CASE WHEN inc.EstadoActual = 'Cerrado' THEN inc.IncidenteID END) as IncidentesCerrados,
        COUNT(DISTINCT CASE WHEN inc.Criticidad = 'Alta' AND inc.EstadoActual = 'Abierto' THEN inc.IncidenteID END) as IncidentesCriticos,
        COUNT(DISTINCT ce.ObligacionID) as TotalObligaciones,
        AVG(CASE WHEN ce.PorcentajeAvance IS NOT NULL THEN ce.PorcentajeAvance END) as PromedioAvance
    FROM Empresas e
    LEFT JOIN Usuarios u ON e.EmpresaID = u.EmpresaID
    LEFT JOIN Incidentes inc ON e.EmpresaID = inc.EmpresaID
    LEFT JOIN CumplimientoEmpresa ce ON e.EmpresaID = ce.EmpresaID
    WHERE e.EmpresaID = :empresa_id
    GROUP BY e.EmpresaID, e.RazonSocial, e.TipoEmpresa
    """
    
    # Query para incidentes recientes
    recent_incidents_query = """
    SELECT TOP 5
        inc.IncidenteID,
        inc.Titulo,
        inc.EstadoActual,
        inc.Criticidad,
        inc.FechaCreacion
    FROM Incidentes inc
    WHERE inc.EmpresaID = :empresa_id
    ORDER BY inc.FechaCreacion DESC
    """
    
    # Ejecutar queries
    stats = db_manager.execute_query(stats_query, {'empresa_id': empresa_id}, fetch_one=True)
    recent_incidents = db_manager.execute_query(recent_incidents_query, {'empresa_id': empresa_id}, fetch_all=True)
    
    return {
        'stats': dict(stats) if stats else {},
        'recent_incidents': [dict(row) for row in recent_incidents]
    }

# ============================================================================
# QUERIES OPTIMIZADAS PARA INCIDENTES
# ============================================================================

@monitor_query("get_incidentes_list")
@cached(timeout=300, namespace="incidentes")  # 5 minutos
def get_incidentes_by_empresa_optimized(empresa_id: int, filtros: Optional[Dict] = None) -> List[Dict]:
    """Obtener incidentes con filtros optimizada"""
    
    base_query = """
    SELECT 
        inc.IncidenteID,
        inc.IDVisible,
        inc.Titulo,
        inc.DescripcionInicial,
        inc.EstadoActual,
        inc.Criticidad,
        inc.TipoFlujo,
        inc.FechaCreacion,
        inc.FechaDeteccion,
        inc.FechaCierre,
        inc.CreadoPor,
        inc.ResponsableCliente,
        inc.SistemasAfectados,
        inc.OrigenIncidente,
        e.RazonSocial as EmpresaRazonSocial,
        COUNT(DISTINCT ei.EvidenciaIncidenteID) as TotalEvidencias
    FROM Incidentes inc
    INNER JOIN Empresas e ON inc.EmpresaID = e.EmpresaID
    LEFT JOIN EvidenciasIncidentes ei ON inc.IncidenteID = ei.IncidenteID
    """
    
    where_conditions = ["inc.EmpresaID = :empresa_id"]
    params = {'empresa_id': empresa_id}
    
    if filtros:
        if filtros.get('estado'):
            where_conditions.append("inc.EstadoActual = :estado")
            params['estado'] = filtros['estado']
        
        if filtros.get('criticidad'):
            where_conditions.append("inc.Criticidad = :criticidad")
            params['criticidad'] = filtros['criticidad']
        
        if filtros.get('busqueda'):
            where_conditions.append("(inc.Titulo LIKE :busqueda OR inc.DescripcionInicial LIKE :busqueda)")
            params['busqueda'] = f"%{filtros['busqueda']}%"
        
        if filtros.get('fecha_desde'):
            where_conditions.append("inc.FechaCreacion >= :fecha_desde")
            params['fecha_desde'] = filtros['fecha_desde']
        
        if filtros.get('fecha_hasta'):
            where_conditions.append("inc.FechaCreacion <= :fecha_hasta")
            params['fecha_hasta'] = filtros['fecha_hasta']
    
    base_query += " WHERE " + " AND ".join(where_conditions)
    base_query += """
    GROUP BY inc.IncidenteID, inc.IDVisible, inc.Titulo, inc.DescripcionInicial, 
             inc.EstadoActual, inc.Criticidad, inc.TipoFlujo, inc.FechaCreacion, 
             inc.FechaDeteccion, inc.FechaCierre, inc.CreadoPor, inc.ResponsableCliente,
             inc.SistemasAfectados, inc.OrigenIncidente, e.RazonSocial
    ORDER BY inc.FechaCreacion DESC
    """
    
    return db_manager.execute_query(base_query, params, fetch_all=True)

# ============================================================================
# QUERIES OPTIMIZADAS PARA CUMPLIMIENTO
# ============================================================================

@monitor_query("get_cumplimiento_empresa")
@cached(timeout=900, namespace="cumplimiento")  # 15 minutos
def get_cumplimiento_by_empresa_optimized(empresa_id: int) -> List[Dict]:
    """Obtener datos de cumplimiento con estadísticas"""
    
    query = """
    SELECT 
        ce.CumplimientoID,
        ce.EmpresaID,
        ce.ObligacionID,
        ce.EstadoCumplimiento,
        ce.PorcentajeAvance,
        ce.FechaVencimiento,
        ce.FechaUltimaActualizacion,
        ce.ResponsableAsignado,
        ce.Comentarios,
        ce.ContactoTecnicoComercial,
        o.Descripcion as ObligacionDescripcion,
        o.AplicaPara,
        o.TipoExigencia,
        o.Frecuencia,
        o.Marco,
        COUNT(DISTINCT ec.EvidenciaID) as TotalEvidencias
    FROM CumplimientoEmpresa ce
    INNER JOIN OBLIGACIONES o ON ce.ObligacionID = o.ObligacionID
    LEFT JOIN EvidenciasCumplimiento ec ON ce.CumplimientoID = ec.CumplimientoID
    WHERE ce.EmpresaID = :empresa_id
    GROUP BY ce.CumplimientoID, ce.EmpresaID, ce.ObligacionID, ce.EstadoCumplimiento,
             ce.PorcentajeAvance, ce.FechaVencimiento, ce.FechaUltimaActualizacion,
             ce.ResponsableAsignado, ce.Comentarios, ce.ContactoTecnicoComercial,
             o.Descripcion, o.AplicaPara, o.TipoExigencia, o.Frecuencia, o.Marco
    ORDER BY ce.FechaVencimiento ASC, ce.PorcentajeAvance ASC
    """
    
    return db_manager.execute_query(query, {'empresa_id': empresa_id}, fetch_all=True)

# ============================================================================
# QUERIES OPTIMIZADAS PARA TAXONOMÍAS
# ============================================================================

@monitor_query("get_taxonomias_cache")
@cached(timeout=86400, namespace="taxonomias")  # 24 horas
def get_taxonomias_optimized(tipo_empresa: Optional[str] = None) -> List[Dict]:
    """Obtener taxonomías con cache de larga duración"""
    
    base_query = """
    SELECT 
        ti.TaxonomiaIncidenteID,
        ti.CodigoTaxonomia,
        ti.NombreTaxonomia,
        ti.DescripcionTaxonomia,
        ti.AplicaParaTipo,
        ti.CategoriaSecundaria,
        ti.SubcategoriaDetallada,
        ti.Activo
    FROM TAXONOMIA_INCIDENTES ti
    WHERE ti.Activo = 1
    """
    
    params = {}
    
    if tipo_empresa:
        base_query += " AND (ti.AplicaParaTipo = :tipo_empresa OR ti.AplicaParaTipo = 'AMBAS')"
        params['tipo_empresa'] = tipo_empresa
    
    base_query += " ORDER BY ti.CodigoTaxonomia"
    
    return db_manager.execute_query(base_query, params, fetch_all=True)

# ============================================================================
# FUNCIONES DE UTILIDAD PARA PERFORMANCE
# ============================================================================

def invalidate_cache_patterns(patterns: List[str]):
    """Invalidar múltiples patrones de cache"""
    for pattern in patterns:
        cache_manager.delete_pattern(pattern)

def invalidate_company_related_cache(empresa_id: int):
    """Invalidar todo el cache relacionado con una empresa"""
    patterns = [
        f"empresas:*empresa_id:{empresa_id}*",
        f"incidentes:*empresa_id:{empresa_id}*",
        f"cumplimiento:*empresa_id:{empresa_id}*",
        f"company_cache:company:{empresa_id}:*"
    ]
    invalidate_cache_patterns(patterns)

def invalidate_inquilino_related_cache(inquilino_id: int):
    """Invalidar todo el cache relacionado con un inquilino"""
    patterns = [
        f"inquilinos:*inquilino_id:{inquilino_id}*",
        f"empresas:*inquilino_id:{inquilino_id}*",
        f"user_cache:*inquilino_id:{inquilino_id}*"
    ]
    invalidate_cache_patterns(patterns)

def get_query_stats() -> Dict[str, Any]:
    """Obtener estadísticas de performance de queries"""
    return query_optimizer.query_stats.copy()

def get_slow_queries(threshold: float = None) -> Dict[str, Any]:
    """Obtener queries lentas"""
    threshold = threshold or query_optimizer.slow_query_threshold
    slow_queries = {}
    
    for query_name, stats in query_optimizer.query_stats.items():
        if stats['avg_time'] > threshold or stats['slow_queries'] > 0:
            slow_queries[query_name] = stats
    
    return slow_queries

# ============================================================================
# ÍNDICES RECOMENDADOS PARA OPTIMIZACIÓN
# ============================================================================

RECOMMENDED_INDEXES = """
-- Índices recomendados para optimización de queries

-- Índices para tabla Inquilinos
CREATE NONCLUSTERED INDEX IX_Inquilinos_Activo_RazonSocial 
ON Inquilinos (Activo, RazonSocial);

CREATE NONCLUSTERED INDEX IX_Inquilinos_RUT 
ON Inquilinos (RUT);

-- Índices para tabla Empresas
CREATE NONCLUSTERED INDEX IX_Empresas_InquilinoID_Activo 
ON Empresas (InquilinoID, Activo);

CREATE NONCLUSTERED INDEX IX_Empresas_TipoEmpresa 
ON Empresas (TipoEmpresa);

-- Índices para tabla Incidentes
CREATE NONCLUSTERED INDEX IX_Incidentes_EmpresaID_FechaCreacion 
ON Incidentes (EmpresaID, FechaCreacion DESC);

CREATE NONCLUSTERED INDEX IX_Incidentes_EstadoActual_Criticidad 
ON Incidentes (EstadoActual, Criticidad);

CREATE NONCLUSTERED INDEX IX_Incidentes_FechaCreacion 
ON Incidentes (FechaCreacion DESC);

-- Índices para tabla CumplimientoEmpresa
CREATE NONCLUSTERED INDEX IX_CumplimientoEmpresa_EmpresaID_FechaVencimiento 
ON CumplimientoEmpresa (EmpresaID, FechaVencimiento);

CREATE NONCLUSTERED INDEX IX_CumplimientoEmpresa_EstadoCumplimiento 
ON CumplimientoEmpresa (EstadoCumplimiento);

-- Índices para tabla Usuarios
CREATE NONCLUSTERED INDEX IX_Usuarios_InquilinoID_EmpresaID 
ON Usuarios (InquilinoID, EmpresaID);

CREATE NONCLUSTERED INDEX IX_Usuarios_Email 
ON Usuarios (Email);

-- Índices para tabla EvidenciasIncidentes
CREATE NONCLUSTERED INDEX IX_EvidenciasIncidentes_IncidenteID 
ON EvidenciasIncidentes (IncidenteID);

-- Índices para tabla EvidenciasCumplimiento
CREATE NONCLUSTERED INDEX IX_EvidenciasCumplimiento_CumplimientoID 
ON EvidenciasCumplimiento (CumplimientoID);
"""