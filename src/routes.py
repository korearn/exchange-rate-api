from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
import os
from dotenv import load_dotenv

from models import (
    ConversionResponse,
    RateResponse,
    HealthResponse,
    HistoryItem
)
from cache import (
    get_cached_rate,
    save_rate,
    save_conversion,
    get_history,
    get_cache_count
)
from frankfurter import get_rate, get_supported_currencies, validate_currency

load_dotenv()

# APIRouter agrupa endpoints relacionados
# En apps grandes tendrías un router por módulo (users, payments, rates...)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Endpoint de salud — indica si el servicio está operativo.
    Los sistemas de monitoreo en producción consultan esto cada minuto.
    """
    return HealthResponse(
        status="ok",
        version=os.getenv("APP_VERSION", "1.0.0"),
        cache_entries=get_cache_count()
    )


@router.get("/currencies")
def list_currencies():
    """Retorna las monedas disponibles para conversión."""
    return {"currencies": get_supported_currencies()}


@router.get("/rates", response_model=RateResponse)
def get_exchange_rate(
    from_currency: str = Query(..., min_length=3, max_length=3, description="Moneda origen"),
    to_currency:   str = Query(..., min_length=3, max_length=3, description="Moneda destino")
):
    """
    Retorna el tipo de cambio entre dos monedas.
    Query() define parámetros de URL: /rates?from_currency=USD&to_currency=MXN
    """
    from_currency = from_currency.upper()
    to_currency   = to_currency.upper()

    # Validar monedas antes de consultar
    if not validate_currency(from_currency) or not validate_currency(to_currency):
        # HTTPException retorna un error HTTP con código y mensaje
        # 400 Bad Request = el cliente mandó datos inválidos
        raise HTTPException(
            status_code=400,
            detail=f"Moneda no soportada. Consulta /currencies para ver las disponibles."
        )

    # Intentar caché primero
    cached = get_cached_rate(from_currency, to_currency)
    if cached:
        return RateResponse(
            base=from_currency,
            currency=to_currency,
            rate=cached,
            timestamp=datetime.utcnow(),
            cached=True
        )

    # Si no hay caché consultar Frankfurter
    result = get_rate(from_currency, to_currency)
    if not result:
        # 503 Service Unavailable = el servicio externo no está disponible
        raise HTTPException(
            status_code=503,
            detail="No se pudo obtener el tipo de cambio. Intenta de nuevo más tarde."
        )

    save_rate(from_currency, to_currency, result["rate"])

    return RateResponse(
        base=from_currency,
        currency=to_currency,
        rate=result["rate"],
        timestamp=result["timestamp"],
        cached=False
    )


@router.get("/convert", response_model=ConversionResponse)
def convert_currency(
    from_currency: str   = Query(..., min_length=3, max_length=3),
    to_currency:   str   = Query(..., min_length=3, max_length=3),
    amount:        float = Query(..., gt=0, description="Monto mayor a 0")
):
    """
    Convierte un monto de una moneda a otra.
    Ejemplo: /convert?from_currency=USD&to_currency=MXN&amount=100
    """
    from_currency = from_currency.upper()
    to_currency   = to_currency.upper()

    if not validate_currency(from_currency) or not validate_currency(to_currency):
        raise HTTPException(status_code=400, detail="Moneda no soportada.")

    # Reutilizamos la lógica de caché del endpoint anterior
    cached = get_cached_rate(from_currency, to_currency)
    is_cached = cached is not None

    if cached:
        rate = cached
    else:
        result = get_rate(from_currency, to_currency)
        if not result:
            raise HTTPException(status_code=503, detail="Servicio de tipos de cambio no disponible.")
        rate = result["rate"]
        save_rate(from_currency, to_currency, rate)

    converted = round(amount * rate, 2)

    # Guardar en historial para auditoría
    save_conversion(from_currency, to_currency, amount, converted, rate)

    return ConversionResponse(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
        converted=converted,
        rate=rate,
        timestamp=datetime.utcnow(),
        cached=is_cached
    )


@router.get("/history")
def conversion_history(limit: int = Query(20, ge=1, le=100)):
    """
    Retorna el historial de conversiones realizadas.
    ge=1 significa 'greater or equal to 1' — mínimo 1 resultado
    le=100 significa 'less or equal to 100' — máximo 100 resultados
    """
    history = get_history(limit)
    return {"history": history, "total": len(history)}