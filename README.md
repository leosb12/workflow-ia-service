# IA Service

Microservicio FastAPI para convertir texto en un workflow JSON de politicas de negocio usando DeepSeek.

## Ejecutar

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8001
```

## Endpoint

`POST /api/ia/texto-a-flujo`

```json
{
  "descripcion": "Describir aqui la politica de negocio"
}
```

## Configuracion DeepSeek

- `DEEPSEEK_MAX_TOKENS=0`: sin limite explicito de tokens enviados al proveedor.
- `DEEPSEEK_TIMEOUT_SECONDS=0`: sin timeout del cliente HTTP (espera indefinida).

Si DeepSeek falla, devuelve contenido vacio o JSON invalido, el servicio genera un workflow fallback valido para evitar error del endpoint.
