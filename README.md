# GetMeTo API

A minimal FastAPI starter configured through environment variables and ready for Docker.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
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

All settings can come from the process environment (or a local `.env` file for development):

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `GetMeTo API` | API title and welcome message |
| `APP_ENV` | `development` | Environment returned by `/health` |
| `DEBUG` | `false` | Enables FastAPI debug mode |
| `PORT` | `8000` | Port the application listens on inside its container |
| `HOST_PORT` | `8000` | Host port published by Docker Compose |
