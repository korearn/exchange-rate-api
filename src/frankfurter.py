import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("FRANKFURTER_BASE_URL", "https://api.frankfurter.app")

# Monedas soportadas -  las más comunes en contexto latinoamericano
SUPPORTED_CURRENCIES = {
    "USD", "EUR", "GBP", "MXN", "BRL", "ARS",
    "COP", "CLP", "PEN", "JPY", "CAD", "CHF"
}

# Rates de respaldo — se usan cuando Frankfurter no está disponible
# Basados en rates reales aproximados contra USD
FALLBACK_RATES = {
    ("USD", "MXN"): 17.89, ("MXN", "USD"): 0.0559,
    ("USD", "EUR"): 0.92,  ("EUR", "USD"): 1.087,
    ("USD", "GBP"): 0.79,  ("GBP", "USD"): 1.266,
    ("USD", "BRL"): 5.76,  ("BRL", "USD"): 0.174,
    ("USD", "COP"): 4180.0,("COP", "USD"): 0.000239,
    ("USD", "CLP"): 945.0, ("CLP", "USD"): 0.00106,
    ("USD", "JPY"): 149.5, ("JPY", "USD"): 0.00669,
    ("USD", "CAD"): 1.36,  ("CAD", "USD"): 0.735,
    ("USD", "CHF"): 0.90,  ("CHF", "USD"): 1.111,
    ("EUR", "MXN"): 19.45, ("MXN", "EUR"): 0.0514,
    ("EUR", "GBP"): 0.86,  ("GBP", "EUR"): 1.163,
    ("EUR", "BRL"): 6.26,  ("BRL", "EUR"): 0.160,
}

def validate_currency(currency: str) -> bool:
    return currency.upper() in SUPPORTED_CURRENCIES


def get_fallback_rate(from_currency: str, to_currency: str) -> Optional[dict]:
    """
    Retorna un rate de respaldo cuando Frankfurter no está disponible.
    Intenta el par directo primero, luego conversión via USD como moneda puente.
    """
    direct = FALLBACK_RATES.get((from_currency, to_currency))
    if direct:
        return {
            "rate":      direct,
            "timestamp": datetime.utcnow(),
            "source":    "fallback"
        }

    # Conversión via USD como puente: FROM → USD → TO
    to_usd   = FALLBACK_RATES.get((from_currency, "USD"))
    from_usd = FALLBACK_RATES.get(("USD", to_currency))
    if to_usd and from_usd:
        return {
            "rate":      round(to_usd * from_usd, 6),
            "timestamp": datetime.utcnow(),
            "source":    "fallback_bridged"
        }

    return None


def get_rate(from_currency: str, to_currency: str) -> Optional[dict]:
    """
    Consulta el tipo de cambio actual.
    Intenta Frankfurter primero — si falla usa rates de respaldo.
    """
    from_currency = from_currency.upper()
    to_currency   = to_currency.upper()

    if not validate_currency(from_currency) or not validate_currency(to_currency):
        return None

    if from_currency == to_currency:
        return {
            "rate":      1.0,
            "timestamp": datetime.utcnow(),
            "source":    "direct"
        }

    # Intentar Frankfurter
    try:
        response = requests.get(
            f"{BASE_URL}/latest",
            params={"from": from_currency, "to": to_currency},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        rate = data["rates"].get(to_currency)

        if rate:
            return {
                "rate":      rate,
                "timestamp": datetime.utcnow(),
                "source":    "frankfurter"
            }

    except Exception:
        # Si Frankfurter falla por cualquier razón, usamos fallback
        pass

    # Fallback cuando Frankfurter no está disponible
    fallback = get_fallback_rate(from_currency, to_currency)
    if fallback:
        print(f"⚠️  Usando rate de respaldo para {from_currency}/{to_currency}")
        return fallback

    return None


def get_supported_currencies() -> list:
    return sorted(list(SUPPORTED_CURRENCIES))