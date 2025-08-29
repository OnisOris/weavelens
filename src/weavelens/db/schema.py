# src/weavelens/db/schema.py
from weaviate.classes.config import Property, DataType, Configure

SCHEMA = [
    {
        "name": "Document",
        "description": "Source document",
        "properties": [
            Property(name="doc_id", data_type=DataType.TEXT, index_filterable=True, index_searchable=True),
            Property(name="title",  data_type=DataType.TEXT, index_filterable=True, index_searchable=True),
            Property(name="path",   data_type=DataType.TEXT, index_filterable=True, index_searchable=True),
            Property(name="source", data_type=DataType.TEXT, index_filterable=True, index_searchable=True),
            Property(name="collection", data_type=DataType.TEXT, index_filterable=True, index_searchable=True),
            Property(name="tags",   data_type=DataType.TEXT_ARRAY, index_filterable=True, index_searchable=True),
            Property(name="created_at", data_type=DataType.DATE, index_filterable=True),
        ],
        "vector_config": Configure.Vectors.self_provided(),  # мы кладём свои вектора
    },
    {
        "name": "Chunk",
        "description": "Text chunk",
        "properties": [
            Property(name="doc_id",  data_type=DataType.TEXT, index_filterable=True),
            Property(name="text",    data_type=DataType.TEXT, index_filterable=True, index_searchable=True),
            Property(name="chunk_id",data_type=DataType.TEXT, index_filterable=True),
            Property(name="section", data_type=DataType.TEXT, index_filterable=True),
            Property(name="order",   data_type=DataType.INT,  index_filterable=True),
            Property(name="tokens",  data_type=DataType.INT,  index_filterable=True),
            Property(name="keywords",data_type=DataType.TEXT_ARRAY, index_filterable=True, index_searchable=True),
            Property(name="meta",    data_type=DataType.TEXT, index_filterable=True, index_searchable=True),
        ],
        "vector_config": Configure.Vectors.self_provided(),
    },
]
