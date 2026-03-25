from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from routes import router
from cache import init_cache

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan maneja eventos de inicio y cierre del servidor.
    El código ANTES del yield corre al arrancar.
    El código DESPUÉS del yield corre al apagar.
    Es el lugar correcto para inicializar recursos como la base de datos.
    """
    print("🚀 Iniciando servidor...")
    init_cache()
    print("✓ Caché inicializado")
    yield
    print("👋 Servidor apagado")


app = FastAPI(
    title=os.getenv("APP_NAME", "Exchange Rate API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="""
API REST para conversión de tipos de cambio en tiempo real.

## Endpoints disponibles

- **/health** — Estado del servicio
- **/currencies** — Monedas soportadas
- **/rates** — Tipo de cambio entre dos monedas
- **/convert** — Conversión de monto entre monedas
- **/history** — Historial de conversiones realizadas
    """,
    lifespan=lifespan
)

# CORS permite que navegadores web consuman tu API desde otros dominios
# En desarrollo permitimos todo — en producción especificarías dominios exactos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra todos los routes definidos en routes.py
# prefix="/api/v1" significa que todos los endpoints quedan en /api/v1/convert etc.
# Versionar la API es buena práctica — permite hacer cambios sin romper clientes existentes
app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    """Redirect informativo a la documentación."""
    return {
        "message": "Exchange Rate API",
        "docs":    "http://localhost:8000/docs",
        "version": os.getenv("APP_VERSION", "1.0.0")
    }