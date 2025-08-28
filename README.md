# weavelens

Установка:
```
uv pip install .
```

Поднимаем weaviate:
```
cd deployment
docker compose down -v
docker compose up -d
docker ps
```

Проверяем работу
```
curl http://localhost:8080/v1/meta
```

Запускаем скрипт проверки векторной бд:

```
uv run ./scripts/weaviate_script.py
```
