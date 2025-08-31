from weavelens.settings import Settings

def test_allowlist_int_to_list(monkeypatch):
    monkeypatch.setenv("TG_ALLOWLIST", "233016635")
    s = Settings()
    assert s.tg_allowlist == [233016635]

def test_allowlist_csv_to_list(monkeypatch):
    monkeypatch.setenv("TG_ALLOWLIST", "1, 2,3")
    s = Settings()
    assert s.tg_allowlist == [1,2,3]

def test_allowlist_json_to_list(monkeypatch):
    monkeypatch.setenv("TG_ALLOWLIST", "[10, 11]")
    s = Settings()
    assert s.tg_allowlist == [10,11]

def test_extra_dirs_csv(monkeypatch):
    monkeypatch.setenv("EXTRA_SCAN_DIRS", "/data/a, /data/b")
    s = Settings()
    assert s.extra_scan_dirs == ["/data/a", "/data/b"]

def test_weaviate_grpc_autoderive(monkeypatch):
    monkeypatch.delenv("WEAVIATE_GRPC_URL", raising=False)
    monkeypatch.setenv("WEAVIATE_URL", "http://weaviate:8080")
    s = Settings()
    assert s.weaviate_grpc_url.startswith("http://weaviate:50051")
