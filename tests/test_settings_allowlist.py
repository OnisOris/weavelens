from weavelens.settings import Settings

def test_allowlist_parsing():
    s1 = Settings(TG_ALLOWLIST="233016635")
    assert s1.tg_allowlist == [233016635]
    s2 = Settings(TG_ALLOWLIST="[1,2,3]")
    assert s2.tg_allowlist == [1,2,3]
    s3 = Settings(TG_ALLOWLIST="1, 2; 3")
    assert s3.tg_allowlist == [1,2,3]
