# Imagen base oficial de Python — slim
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

# Puerto que expone el contenedor
EXPOSE 8000

# Comando que corre al iniciar el contenedor
# --host 0.0.0.0 permite conexiones desde fuera del contenedor
# Sin esto el servidor solo escucha dentro del contenedor y no es accesible
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]