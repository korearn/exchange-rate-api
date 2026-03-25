import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(__file__).parent.parent / "cache.db"
# TTL = Time To Live - para las tasas de cambio en minutos
# Después de ese tiempo se considera que la tasa de cambio está obsoleta y se debe obtener una nueva de la API externa
TTL_MINUTES = int(os.getenv("CACHE_TTL_MINUTES", 60))

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_cache():
    """
    Crea las tablas necesarias si no existen.
    Se llama una vez al iniciar el server.
    """
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rate_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            rate REAL NOT NULL,
            fetched_at DATETIME NOT NULL,
            expires_at DATETIME NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            amount REAL NOT NULL,
            converted REAL NOT NULL,
            rate REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # indice para acelerar consultas por moneda origen y destino
    # sin indice, la consulta para obtener la tasa de cambio puede ser lenta a medida que crece la cantidad de registros
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rate_cache_currencies 
        ON rate_cache(from_currency, to_currency)
    """)
    conn.commit()
    conn.close()

def get_cached_rate(from_currency: str, to_currency: str) -> Optional[float]:
    """
    Busca un rate válida en el cach´´e.
    Retorna el rate si existe y no ha expirado, None si no hay o expiró.
    """
    conn = get_connection()
    now = datetime.utcnow().isoformat()

    row = conn.execute("""
        SELECT rate FROM rate_cache
        WHERE from_currency = ? 
            AND to_currency = ? 
            AND expires_at  > ?
        ORDER BY fetched_at DESC
        LIMIT 1
    """, (from_currency, to_currency, now)).fetchone()
    
    conn.close()
    return row["rate"] if row else None

def save_rate(from_currency: str, to_currency: str, rate: float):
    """
    Guarda un nuevo rate en el caché con su fecha de expiración.
    timedelta se usa para calcular la fecha de expiración sumando el TTL a la fecha actual.
    """
    conn = get_connection()
    now = datetime.utcnow()
    expires = now + timedelta(minutes=TTL_MINUTES)

    conn.execute("""
        INSERT INTO rate_cache (from_currency, to_currency, rate, fetched_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (from_currency, to_currency, rate, now.isoformat(), expires.isoformat()))
    conn.commit()
    conn.close()

def save_conversion(from_currency: str, to_currency: str,
                    amount: float, converted: float, rate: float):
    """Guarda cada conversión en el historial para auditoría."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO conversion_history (from_currency, to_currency, amount, converted, rate)
        VALUES (?, ?, ?, ?, ?)
    """, (from_currency, to_currency, amount, converted, rate))
    conn.commit()
    conn.close()

def get_history(limit: int = 20) -> list:
    """Retorna las últimas conversiones realizadas."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM conversion_history ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_cache_count() -> int:
    """Retorna la cantidad de entradas actualmente en el caché. Usando el endpoint /health."""
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    count = conn.execute("""
        SELECT COUNT(*) FROM rate_cache WHERE expires_at > ?
    """, (now,)).fetchone()[0]
    conn.close()
    return count