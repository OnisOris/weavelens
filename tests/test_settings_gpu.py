from weavelens.settings import pick_ollama_model

def test_pick_explicit_wins():
    assert pick_ollama_model("gpu", "cpu_model", "gpu_model", explicit="manual") == "manual"

def test_pick_gpu_when_toggle_gpu():
    assert pick_ollama_model("gpu", "cpu_model", "gpu_model") == "gpu_model"

def test_pick_cpu_when_toggle_cpu():
    assert pick_ollama_model("cpu", "cpu_model", "gpu_model") == "cpu_model"

def test_pick_cpu_when_toggle_missing():
    assert pick_ollama_model(None, "cpu_model", "gpu_model") == "cpu_model"
