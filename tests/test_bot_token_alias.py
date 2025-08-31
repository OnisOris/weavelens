import os
import importlib
import types

def _reload_with_env(env: dict[str, str]):
    # isolate module import per test
    modname = "weavelens.settings"
    if modname in list(importlib.sys.modules.keys()):
        del importlib.sys.modules[modname]
    # patch env temporarily
    old = os.environ.copy()
    try:
        os.environ.update(env)
        s_mod = importlib.import_module(modname)
        importlib.reload(s_mod)
        return s_mod.settings
    finally:
        os.environ.clear()
        os.environ.update(old)

def test_token_from_bot_token():
    s = _reload_with_env({"BOT_TOKEN":"ABC:123"})
    assert s.tg_token == "ABC:123"

def test_token_from_tg_bot_token():
    s = _reload_with_env({"TG_BOT_TOKEN":"XYZ:777"})
    assert s.tg_token == "XYZ:777"

def test_allowlist_parsing_single_int():
    s = _reload_with_env({"TG_ALLOWLIST": "233016635"})
    assert s.tg_allowlist == [233016635]

def test_allowlist_parsing_csv():
    s = _reload_with_env({"TG_ALLOWLIST": "1,  2;3 4"})
    assert s.tg_allowlist == [1,2,3,4]

def test_weaviate_grpc_autoderive():
    s = _reload_with_env({"WEAVIATE_URL": "http://weaviate:8080"})
    assert s.weaviate_grpc_url.endswith(":50051")
