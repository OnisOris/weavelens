from prometheus_client import Counter, Histogram

REQS = Counter("weavelens_requests_total", "Requests", ["route"])
LAT = Histogram("weavelens_latency_seconds", "Latency", ["route"])
HITK = Histogram("weavelens_hit_at_k", "Hit@k", ["route"], buckets=(1,3,5,8,10,20))
