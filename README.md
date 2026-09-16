# GetMeTo API

A minimal FastAPI starter configured through environment variables and ready for Docker.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app
```

Open `http://localhost:8000/docs`. The health check is at `GET /health`.

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Or build and run directly:

```bash
docker build -t getmeto-api .
docker run --rm --env-file .env -p 8000:8000 getmeto-api
```

## Configuration

The app has **no configuration defaults**. It exits during startup if any setting is absent or invalid. `pydantic-settings` maps each field to its uppercase environment variable; `.env` is read only as a local-development convenience. Kubernetes injects the same variables into the container process through a ConfigMap, so it does not need a `.env` file.

| Variable | Required value | Purpose |
| --- | --- | --- |
| `APP_NAME` | string | API title and welcome message |
| `APP_ENV` | string | Environment returned by `/health` |
| `APP_DEBUG` | `true` or `false` | Enables FastAPI debug/reload mode |
| `APP_HOST` | IP address, normally `0.0.0.0` | Interface the server binds to |
| `APP_PORT` | integer | Port the application listens on |
| `HOST_PORT` | optional; defaults to `8000` in Compose only | Host port published by Docker Compose |

Process environment takes precedence over `.env`, so a deployment platform can override local values without changing the image.

## Kubernetes

The manifests in [`k8s/`](k8s/) deploy two replicas, configure health probes, run with restricted permissions, and provide an internal Service. Before applying them, replace the image in [`k8s/deployment.yaml`](k8s/deployment.yaml) with your registry image and tag, then set the appropriate non-secret values in [`k8s/configmap.yaml`](k8s/configmap.yaml).

```bash
kubectl apply -k k8s/
```

For each environment, use a separate ConfigMap (or Kustomize overlay) containing its `APP_*` values. Put secrets in a Kubernetes Secret and reference it with `envFrom` or individual `valueFrom.secretKeyRef` entries; do not add secrets to this ConfigMap or bake them into the image.
