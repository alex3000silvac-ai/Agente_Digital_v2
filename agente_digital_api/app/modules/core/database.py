# modules/core/database.py
# Funcionalidades centrales de base de datos

from ...database import get_db_connection, TEST_MODE
from ...db_validator import db_validator

__all__ = ['get_db_connection', 'TEST_MODE', 'db_validator']