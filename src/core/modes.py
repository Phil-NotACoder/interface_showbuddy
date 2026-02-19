READ = "read"
WRITE = "write"

def normalize_mode(value: str) -> str:
    v = (value or "").strip().lower()
    return WRITE if v == WRITE else READ