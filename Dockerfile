FROM python:3.11-slim

WORKDIR /app

# Evitar escritura de .pyc y buffers de salida
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 2 workers es razonable con 4 vCPU en t3a.xlarge
# Para FastAPI async, workers=2 + uvicorn es suficiente para produccion
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
