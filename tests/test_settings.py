
from weavelens.settings import Settings

def run():
    s = Settings(TG_ALLOWLIST="1,2;3")
    assert s.tg_allowlist == [1,2,3]
    assert s.api_prefix.startswith("/")
    assert s.inbox_dir
    assert s.weaviate_url.startswith("http")
    print("OK")

if __name__ == "__main__":
    run()
