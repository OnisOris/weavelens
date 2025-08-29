# Weavelens docker-compose (server & embedded)

## Quick start (server profile)

```bash
cd deployment
docker compose up -d weaviate ollama api bot
```

> Avoid `--no-deps` for the first bring-up. `depends_on` with healthchecks ensures `api` waits for Weaviate to be ready, and `bot` waits for `api`.

### Sanity checks

```bash
curl -sS http://localhost:8000/api/live
curl -sS http://localhost:8000/api/ready
curl -sS http://localhost:8000/api/health
```

### Rebuild just API (if code changed)

```bash
docker compose up -d --build api
```

If you *must* use `--no-deps`, ensure `weaviate` is already up and healthy:
```bash
docker compose ps
docker logs deployment-weaviate-1 --since=1m
```

## Embedded profile

To run without external Weaviate:
```bash
docker compose --profile embedded up -d api-embedded bot
```

Bot still calls `http://api:8000/api` if you start `api` instead of `api-embedded`. Adjust `BOT_API_URL` if you rename services.
