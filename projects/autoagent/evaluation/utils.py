"""Минимальные заглушки для evaluation.utils (требуется autoagent.cli)."""

def update_progress(*args, **kwargs):
    pass

def check_port_available(port: int) -> bool:
    return True

def run_evaluation(*args, **kwargs):
    return None

def clean_msg(msg: str, *args, **kwargs) -> str:
    return msg
