# timezone_utils.py
"""
Utilidades centralizadas para manejo de timezone
Zona horaria oficial: Chile (America/Santiago)
"""

from datetime import datetime, timezone, timedelta
import pytz
from typing import Optional

# Zona horaria oficial de Chile
CHILE_TZ = pytz.timezone('America/Santiago')

def get_chile_time() -> datetime:
    """
    Obtener tiempo actual en zona horaria de Chile
    Maneja automáticamente horario de verano/invierno
    """
    return datetime.now(CHILE_TZ)

def get_chile_time_str(format_str: str = '%d/%m/%Y %H:%M') -> str:
    """
    Obtener tiempo actual de Chile como string formateado
    """
    return get_chile_time().strftime(format_str)

def get_utc_time() -> datetime:
    """
    Obtener tiempo UTC actual
    """
    return datetime.now(timezone.utc)

def convert_to_chile_time(utc_datetime: datetime) -> datetime:
    """
    Convertir datetime UTC a hora de Chile
    """
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    return utc_datetime.astimezone(CHILE_TZ)

def convert_to_utc(chile_datetime: datetime) -> datetime:
    """
    Convertir datetime de Chile a UTC
    """
    if chile_datetime.tzinfo is None:
        chile_datetime = CHILE_TZ.localize(chile_datetime)
    return chile_datetime.astimezone(timezone.utc)

def format_chile_datetime(dt: datetime, format_str: str = '%d/%m/%Y %H:%M') -> str:
    """
    Formatear datetime en zona horaria de Chile
    """
    if dt.tzinfo is None:
        dt = CHILE_TZ.localize(dt)
    chile_dt = dt.astimezone(CHILE_TZ)
    return chile_dt.strftime(format_str)

def get_chile_timestamp() -> str:
    """
    Obtener timestamp de Chile para archivos
    """
    return get_chile_time().strftime('%Y%m%d_%H%M%S')

def get_chile_iso_timestamp() -> str:
    """
    Obtener timestamp ISO de Chile
    """
    return get_chile_time().isoformat()

def calculate_deadline_chile(hours_from_now: int) -> datetime:
    """
    Calcular deadline en horas desde ahora en zona horaria de Chile
    """
    now = get_chile_time()
    return now + timedelta(hours=hours_from_now)

def is_business_hours_chile() -> bool:
    """
    Verificar si estamos en horario laboral de Chile (8:00 - 18:00)
    """
    now = get_chile_time()
    return 8 <= now.hour < 18 and now.weekday() < 5  # Lunes a Viernes

def get_timezone_info() -> dict:
    """
    Obtener información completa de timezone
    """
    now_chile = get_chile_time()
    now_utc = get_utc_time()
    
    return {
        'chile_time': now_chile.isoformat(),
        'utc_time': now_utc.isoformat(),
        'timezone_name': 'America/Santiago',
        'offset_hours': now_chile.utcoffset().total_seconds() / 3600,
        'is_dst': bool(now_chile.dst()),
        'business_hours': is_business_hours_chile()
    }