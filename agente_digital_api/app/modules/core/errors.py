# modules/core/errors.py
# Sistema centralizado de manejo de errores

from ...error_handlers import (
    robust_endpoint, 
    safe_endpoint, 
    ErrorResponse, 
    DatabaseHealthChecker,
    register_error_handlers
)

__all__ = [
    'robust_endpoint', 
    'safe_endpoint', 
    'ErrorResponse', 
    'DatabaseHealthChecker',
    'register_error_handlers'
]