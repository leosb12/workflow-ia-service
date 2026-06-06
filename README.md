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
# CU-35 Clasificar solicitud

`ia-service` orquesta el CU-35 mediante:

```http
POST /api/ia/clasificar-solicitud
```

Este endpoint recibe el texto del usuario, el canal y las politicas activas reales enviadas por Spring Boot. No carga TensorFlow ni modelos pesados; llama por HTTP a `ia-deep-learning-service` usando `IA_DEEP_LEARNING_SERVICE_URL` (por defecto `http://localhost:8010`).

Si `ia-deep-learning-service` no responde, devuelve un error controlado:

```json
{
  "error": "IA_DEEP_LEARNING_NO_DISPONIBLE"
}
```

La carpeta `app/modules/clasificador_solicitudes_orquestador/` queda preparada para agregar mas adelante DeepSeek como explicador o fallback, sin implementarlo todavia.
