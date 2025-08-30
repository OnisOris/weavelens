from __future__ import annotations
from typing import Any, Dict
import weaviate
from weaviate.classes.config import Property, DataType, VectorDistances

DOC_CLASS = "Document"
CHUNK_CLASS = "Chunk"

def ensure_schema(client: weaviate.WeaviateClient) -> None:
    """Ensure Weaviate has our collections with desired properties.

    Idempotent: safe to call on every startup.
    """
    coll = client.collections

    # Document
    if DOC_CLASS not in coll.list_all():
        coll.create(
            name=DOC_CLASS,
            vectorizer_config=None,
            properties=[
                Property(name="doc_id", data_type=DataType.TEXT, index_searchable=True, index_filterable=True),
                Property(name="path", data_type=DataType.TEXT, index_searchable=True, index_filterable=True),
                Property(name="filename", data_type=DataType.TEXT, index_searchable=True, index_filterable=True),
                Property(name="sha256", data_type=DataType.TEXT, index_searchable=True, index_filterable=True),
                Property(name="size", data_type=DataType.INT),
                Property(name="mtime", data_type=DataType.NUMBER),
            ],
        )

    # Chunk
    if CHUNK_CLASS not in coll.list_all():
        coll.create(
            name=CHUNK_CLASS,
            vectorizer_config=None,
            properties=[
                Property(name="chunk_id", data_type=DataType.TEXT, index_searchable=True, index_filterable=True),
                Property(name="doc_id", data_type=DataType.TEXT, index_searchable=True, index_filterable=True),
                Property(name="order", data_type=DataType.INT, index_filterable=True),
                Property(name="text", data_type=DataType.TEXT, index_searchable=True),
                Property(name="path", data_type=DataType.TEXT, index_searchable=True, index_filterable=True),
                Property(name="filename", data_type=DataType.TEXT, index_searchable=True, index_filterable=True),
            ],
            vector_index_config={"distance": VectorDistances.COSINE},
        )