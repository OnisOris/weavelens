# scripts/weaviate_script.py  (v4)
import uuid
import weaviate
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import MetadataQuery

client = weaviate.connect_to_local()  # подключение к локальному докеру
try:
    # Чистим, если коллекция уже есть
    for c in client.collections.list_all():
        if c.name == "Doc":
            client.collections.delete("Doc")
            break

    # Создаём коллекцию с "своими" векторами
    client.collections.create(
        name="Doc",
        properties=[
            Property(name="text", data_type=DataType.TEXT),
            Property(name="source", data_type=DataType.TEXT),
            Property(name="tags", data_type=DataType.TEXT_ARRAY),
        ],
        vector_config=Configure.Vectors.self_provided(),  # "none" в терминах v3
    )

    # Вставка объекта с явным вектором
    vec = [0.01] * 384
    doc = client.collections.get("Doc")
    uid = str(uuid.uuid4())
    doc.data.insert(
        properties={"text": "Пример чанка", "source": "demo", "tags": ["test"]},
        vector=vec,
        uuid=uid,
    )

    # Поиск по вектору
    res = doc.query.near_vector(
        near_vector=vec,
        limit=3,
        return_properties=["text", "source"],
        return_metadata=MetadataQuery(distance=True),
    )
    for obj in res.objects:
        print(obj.properties, obj.metadata.distance)
finally:
    client.close()
