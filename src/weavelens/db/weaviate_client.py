from __future__ import annotations
import weaviate
from weaviate.classes.config import Property, DataType, Configure
from .schema import SCHEMA
from ..settings import Settings

_client: weaviate.WeaviateClient | None = None

def get_client() -> weaviate.WeaviateClient:
    global _client
    if _client is not None:
        return _client
    s = Settings()
    if s.profile == "embedded":
        try:
            from weaviate.embedded import EmbeddedOptions
        except Exception as e:
            raise RuntimeError("Install weaviate-embedded for embedded profile") from e
        _client = weaviate.WeaviateClient(embedded_options=EmbeddedOptions(persistence_data_path=s.weaviate_embedded_path))
    else:
        _client = weaviate.connect_to_local(
            host=s.weaviate_host,
            port=s.weaviate_port,
            grpc_port=50051,
            http_secure=False,
            grpc_secure=False,
        )
    ensure_schema(_client)
    return _client

def ensure_schema(client: weaviate.WeaviateClient) -> None:
    existing = {c.name for c in client.collections.list_all()}
    for col in SCHEMA:
        if col["name"] not in existing:
            client.collections.create(**col)
