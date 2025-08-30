
WeaveLens API Patch
--------------------
This patch adds the missing API routes:
  - POST /api/search
  - POST /api/ask
  - POST /api/ingest/scan
and introduces a simple Weaviate v4 BM25-backed storage with file-path tracking,
plus an Ollama client.

How to apply:
  1) Unzip into your project root so that 'src/weavelens/...' files are created/overwritten.
  2) Rebuild and start the API container:
       sudo docker compose -f deployment/docker-compose.yml build api
       sudo docker compose -f deployment/docker-compose.yml up -d api
  3) Start the bot after API is healthy:
       sudo docker compose -f deployment/docker-compose.yml up -d --no-deps bot

Smoke tests:
  curl -s http://localhost:8000/api/live
  curl -s http://localhost:8000/api/ready
  curl -s http://localhost:8000/api/health

  curl -s -X POST http://localhost:8000/api/ingest/scan -H 'Content-Type: application/json' -d '{"paths":["data/inbox"]}'
  curl -s -X POST http://localhost:8000/api/search -H 'Content-Type: application/json' -d '{"q":"пример","k":6}'
  curl -s -X POST http://localhost:8000/api/ask -H 'Content-Type: application/json' -d '{"q":"пример","k":6}'
