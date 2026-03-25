# Exchange Rate API 💱

Microservicio REST para conversión de tipos de cambio en tiempo real.
Construido con FastAPI, SQLite y Docker. Consume Frankfurter API con sistema
de fallback automático cuando el servicio externo no está disponible.

## ¿Qué hace?

- Retorna tipos de cambio entre divisas en tiempo real
- Convierte montos entre monedas con un solo endpoint
- Cachea resultados en SQLite para reducir llamadas externas
- Registra historial de conversiones para auditoría
- Incluye endpoint `/health` para monitoreo del servicio

## Stack técnico

- **Python 3.12** — lenguaje principal
- **FastAPI** — framework REST moderno con documentación automática
- **Uvicorn** — servidor ASGI de alto rendimiento
- **Pydantic** — validación automática de datos de entrada y salida
- **SQLite** — caché y persistencia sin servidor externo
- **Frankfurter API** — tipos de cambio gratuitos sin API key
- **Docker** — containerización para despliegue portable

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/health` | Estado del servicio y entradas en caché |
| GET | `/api/v1/currencies` | Lista de monedas disponibles |
| GET | `/api/v1/rates` | Tipo de cambio entre dos monedas |
| GET | `/api/v1/convert` | Conversión de monto entre monedas |
| GET | `/api/v1/history` | Historial de conversiones realizadas |

## Monedas soportadas

`USD` · `EUR` · `GBP` · `MXN` · `BRL` · `ARS` · `COP` · `CLP` · `PEN` · `JPY` · `CAD` · `CHF`

## Instalación
```bash
git clone https://github.com/korearn/exchange-rate-api
cd exchange-rate-api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

### Ejecución local
```bash
cd src
uvicorn main:app --reload
```

Documentación interactiva disponible en: `http://localhost:8000/docs`

### Ejecución con Docker
```bash
docker build -t exchange-rate-api .
docker run -p 8000:8000 exchange-rate-api
```

## Ejemplos de uso

### Tipo de cambio
```bash
curl "http://localhost:8000/api/v1/rates?from_currency=USD&to_currency=MXN"
```
```json
{
  "base": "USD",
  "currency": "MXN",
  "rate": 17.89,
  "timestamp": "2026-03-25T19:52:32",
  "cached": false
}
```

### Conversión
```bash
curl "http://localhost:8000/api/v1/convert?from_currency=USD&to_currency=MXN&amount=500"
```
```json
{
  "from_currency": "USD",
  "to_currency": "MXN",
  "amount": 500,
  "converted": 8945.0,
  "rate": 17.89,
  "timestamp": "2026-03-25T19:52:32",
  "cached": true
}
```

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `APP_NAME` | Nombre del servicio | Exchange Rate API |
| `APP_VERSION` | Versión actual | 1.0.0 |
| `CACHE_TTL_MINUTES` | Minutos de validez del caché | 60 |
| `FRANKFURTER_BASE_URL` | URL base de la API externa | https://api.frankfurter.app |

## Arquitectura
```
exchange-rate-api/
├── src/
│   ├── main.py           # Servidor FastAPI + lifespan
│   ├── routes.py         # Endpoints REST
│   ├── models.py         # Schemas Pydantic
│   ├── cache.py          # Caché SQLite con TTL
│   └── frankfurter.py    # Cliente API externa + fallback
├── Dockerfile
└── requirements.txt
```

## Notas técnicas

- El caché expira automáticamente según `CACHE_TTL_MINUTES`
- Si Frankfurter no está disponible, el sistema usa rates de respaldo predefinidos
- El campo `cached: true/false` en la respuesta indica la fuente del dato
- La API está versionada en `/api/v1/` para permitir cambios futuros sin romper clientes