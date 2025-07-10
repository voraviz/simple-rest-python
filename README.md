# Very Simple Python REST API App
Python web application built with Flask that acts as a proxy to a backend service. It is designed to be container-friendly and includes health check and Prometheus metrics endpoints for observability.
```json
{
    "endpoints": {
        "/api": "Proxy endpoint - forwards to backend API",
        "/health": "Health check endpoint",
        "/metrics": "Prometheus metrics endpoint"
    },
    "service": "simple-rest-python",
    "version": "1.0"
}
```
## Features

*   **API Proxy**: send GET requests from the `/api` endpoint to a configurable backend service.
*   **Health Check**: A `/health` endpoint to monitor the service's status, perfect for Kubernetes liveness/readiness probes.
*   **Prometheus Metrics**: Exposes detailed request/response metrics at the `/metrics` endpoint for monitoring and alerting.
*   **Production-Ready**: Uses `waitress` as a production-grade WSGI server.
*   **Configurable**: Easily configured through environment variables.

## Endpoints

| Method | Path       | Description                                                                                             |
|--------|------------|---------------------------------------------------------------------------------------------------------|
| `GET`  | `/`        | Displays basic information about the service and its endpoints.                                         |
| `GET`  | `/api`     | Proxies GET requests to the backend service defined by the `BACKEND` environment variable.                |
| `GET`  | `/health`  | Returns a `200 OK` with the service status. Example: `{"status": "healthy", "service": "...", "version": "..."}`. |
| `GET`  | `/metrics` | Exposes application and request metrics in Prometheus format.                                           |

## Configuration

The application is configured using the following environment variables:

| Variable  | Required | Description                                            | Default |
|-----------|----------|--------------------------------------------------------|---------|
| `BACKEND` | **Yes**  | The full URL of the backend service to proxy requests to. | `null`  |
| `PORT`    | No       | The port to run the application on.                    | `5000`  |


This code is mostly wrote by Claude and Gemini