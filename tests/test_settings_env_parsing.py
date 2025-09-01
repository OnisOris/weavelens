import os
import sys

# add src/ to path for tests that run without install
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from weavelens.settings import Settings


def test_allowlist_single_int(monkeypatch):
    monkeypatch.setenv("TG_ALLOWLIST", "233016635")
    s = Settings()
    assert s.tg_allowlist == [233016635]


def test_allowlist_csv(monkeypatch):
    monkeypatch.setenv("TG_ALLOWLIST", "1, 2,3 ; 4")
    s = Settings()
    assert s.tg_allowlist == [1, 2, 3, 4]


def test_allowlist_jsonish(monkeypatch):
    monkeypatch.setenv("TG_ALLOWLIST", "[10, 11]")
    s = Settings()
    assert s.tg_allowlist == [10, 11]


def test_extra_scan_dirs(monkeypatch):
    monkeypatch.setenv("EXTRA_SCAN_DIRS", " /data/inbox , /opt/docs ; /var/x ")
    s = Settings()
    assert s.extra_scan_dirs == ["/data/inbox", "/opt/docs", "/var/x"]


def test_api_prefix_normalized(monkeypatch):
    monkeypatch.setenv("API_PREFIX", "api")
    s = Settings()
    assert s.api_prefix == "/api"


def test_bot_token_alias(monkeypatch):
    monkeypatch.delenv("TG_BOT_TOKEN", raising=False)
    monkeypatch.setenv("BOT_TOKEN", "x123")
    s = Settings()
    assert s.tg_token == "x123"
    assert s.bot_token == "x123"


def test_weaviate_grpc_derived(monkeypatch):
    monkeypatch.setenv("WEAVIATE_URL", "http://weaviate:8080")
    monkeypatch.delenv("WEAVIATE_GRPC_URL", raising=False)
    s = Settings()
    assert s.weaviate_grpc_url == "grpc://weaviate:50051"


def test_bot_api_base_default(monkeypatch):
    monkeypatch.delenv("BOT_API_URL", raising=False)
    monkeypatch.setenv("API_PREFIX", "/api")
    s = Settings()
    assert s.bot_api_url == "http://api:8000/api"
