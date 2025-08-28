from __future__ import annotations
from weaviate.classes.config import Property, DataType, Configure

# Two collections: Document (metadata), Chunk (text+vector)
DOC = dict(
    name="Document",
    properties=[
        Property(name="doc_id", data_type=DataType.TEXT),
        Property(name="title", data_type=DataType.TEXT),
        Property(name="path", data_type=DataType.TEXT),
        Property(name="source", data_type=DataType.TEXT),
        Property(name="collection", data_type=DataType.TEXT),
        Property(name="tags", data_type=DataType.TEXT_ARRAY),
        Property(name="created_at", data_type=DataType.DATE),
    ],
    vector_config=Configure.Vectors.self_provided(),
)

CHUNK = dict(
    name="Chunk",
    properties=[
        Property(name="doc_id", data_type=DataType.TEXT),
        Property(name="text", data_type=DataType.TEXT),
        Property(name="chunk_id", data_type=DataType.TEXT),
        Property(name="section", data_type=DataType.TEXT),
        Property(name="order", data_type=DataType.INT),
        Property(name="tokens", data_type=DataType.INT),
        Property(name="keywords", data_type=DataType.TEXT_ARRAY),
        Property(name="meta", data_type=DataType.TEXT),
    ],
    vector_config=Configure.Vectors.self_provided(),
)

SCHEMA = [DOC, CHUNK]
