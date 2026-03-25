from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ConversionRequest(BaseModel):
    """
    Define los parámetros que espera el endpoint /convert.
    Field() permite agregar validaciones y valores por defecto.
    """
    from_currency: str = Field(..., min_length=3, max_length=3, description="Moneda origen (ej: USD)")
    to_currency:   str = Field(..., min_length=3, max_length=3, description="Moneda destino (ej: MXN)")
    amount:        float = Field(..., gt=0, description="Cantidad a convertir, debe ser mayor a 0")

class ConversionResponse(BaseModel):
    """
    Define la estructura de la respuesta del endpoint /convert.
    """
    from_currency: str
    to_currency:   str
    amount:        float
    converted:     float
    rate:          float
    timestamp:     datetime
    cached:        bool # Indica si la tasa de cambio se obtuvo de la caché o de la API externa

class RateResponse(BaseModel):
    """
    Define la estructura de la respuesta del endpoint /rates - Tipo de cambio sin conversión..
    """
    base:          str
    currency:      str
    rate:          float
    timestamp:     datetime
    cached:        bool

class HistoryItem(BaseModel):
    """
    Define la estructura de cada elemento en el historial de conversiones.
    """
    from_currency: str
    to_currency:   str
    amount:        float
    converted:     float
    rate:          float
    timestamp:     datetime

class HealthResponse(BaseModel):
    """
    Define la estructura de la respuesta del endpoint /health.
    En producción se consulta este endpoint para verificar que el servicio esté funcionando correctamente.
    """
    status: str
    version: str
    cache_entries: int