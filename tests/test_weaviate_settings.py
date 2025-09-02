from weavelens.settings import get_settings


def test_weaviate_urls_defaults():
    get_settings.cache_clear()
    s = get_settings()
    assert s.weaviate_url == "http://weaviate:8080"
    assert s.weaviate_grpc_url == "http://weaviate:50051"
