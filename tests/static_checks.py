import re, pathlib

root = pathlib.Path(__file__).resolve().parents[1]

def ok(name): print(f"[OK] {name}")
def fail(name, msg): 
    print(f"[FAIL] {name}: {msg}")
    raise SystemExit(1)

# 1. main.py uses settings.api_prefix for routers
main = (root / "src/weavelens/api/main.py").read_text(encoding="utf-8")
if re.search(r'include_router\(\s*health\.router\s*,\s*prefix\s*=\s*settings\.api_prefix', main):
    ok("main.py mounts health with settings.api_prefix")
else:
    fail("main.py mounts health", "settings.api_prefix not used for health")

if re.search(r'include_router\(\s*search\.router\s*,\s*prefix\s*=\s*settings\.api_prefix', main):
    ok("main.py mounts search with settings.api_prefix")
else:
    fail("main.py mounts search", "settings.api_prefix not used for search")

# 2. health.py defines endpoints live/ready/health
hp = (root / "src/weavelens/api/routers/health.py").read_text(encoding="utf-8")
for ep in ("live", "ready", "health"):
    if re.search(rf'@router\.get\("/{ep}"\)', hp):
        ok(f"health.py defines /{ep}")
    else:
        fail("health endpoints", f"/{ep} not found")

# 3. weaviate_client.py must not contain 'http_secure'
wvp = (root / "src/weavelens/db/weaviate_client.py").read_text(encoding="utf-8")
if "http_secure" not in wvp:
    ok("weaviate_client.py has no http_secure")
else:
    fail("weaviate_client.py cleanup", "http_secure still present")

print("STATIC CHECKS PASSED")