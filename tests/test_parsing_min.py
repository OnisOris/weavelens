import os
import json

def parse_allowlist(value):
    # Имитируем типичное чтение из env для Pydantic: допускаем int, CSV и JSON-лист
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    s = str(value).strip()
    # JSON-массив
    if s.startswith("[") and s.endswith("]"):
        return list(json.loads(s))
    # CSV
    return [int(x.strip()) for x in s.split(",") if x.strip()]

def parse_extra_scan_dirs(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value]
    s = str(value).strip()
    if s.startswith("[") and s.endswith("]"):
        return list(json.loads(s))
    # CSV
    return [x.strip() for x in s.split(",") if x.strip()]

def test_allowlist_variants():
    assert parse_allowlist("233016635") == [233016635]
    assert parse_allowlist("[233016635, 111]") == [233016635, 111]
    assert parse_allowlist("233016635,111") == [233016635, 111]
    assert parse_allowlist(233016635) == [233016635]
    assert parse_allowlist("") == []
    assert parse_allowlist(None) == []

def test_extra_scan_dirs_variants():
    assert parse_extra_scan_dirs("/data/inbox") == ["/data/inbox"]
    assert parse_extra_scan_dirs("/a, /b ,/c") == ["/a","/b","/c"]
    assert parse_extra_scan_dirs(["/a","/b"]) == ["/a","/b"]
    assert parse_extra_scan_dirs('["/a","/b"]') == ["/a","/b"]
    assert parse_extra_scan_dirs("") == []
    assert parse_extra_scan_dirs(None) == []
