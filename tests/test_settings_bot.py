
from weavelens.settings import Settings

def test_bot_settings_present():
    s = Settings()
    assert hasattr(s, "bot_api_url")
    assert hasattr(s, "bot_token")

def test_allowlist_parsing():
    assert Settings(TG_ALLOWLIST="233, 42;  7").tg_allowlist == [233,42,7]
    assert Settings(TG_ALLOWLIST=123).tg_allowlist == [123]
    assert Settings(TG_ALLOWLIST="[1,2,3]").tg_allowlist == [1,2,3]

def test_weaviate_grpc_derived():
    s = Settings(WEAVIATE_URL="http://weaviate:8080", WEAVIATE_GRPC_URL=None)
    assert s.weaviate_grpc_url.startswith("grpc://")
