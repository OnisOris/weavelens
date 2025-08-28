import logging, sys

def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(stream=sys.stdout)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    root = logging.getLogger()
    root.setLevel(level)
    handler.setFormatter(fmt)
    root.handlers.clear()
    root.addHandler(handler)
