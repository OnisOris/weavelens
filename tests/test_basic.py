from weavelens.ingest.loader import _doc_id_from_sha
from weavelens.llm.ollama_client import _normalize_host, _base_url

def test_doc_id():
    sha = 'a'*64
    assert _doc_id_from_sha(sha) == 'a'*16

def test_ollama_base_url():
    assert _normalize_host('http://localhost') == 'localhost'
    assert _normalize_host('https://localhost:11434') == 'localhost:11434'
    assert _base_url('localhost', 11434).endswith(':11434')
    assert _base_url('1.2.3.4:5555', 11434).endswith('1.2.3.4:5555')