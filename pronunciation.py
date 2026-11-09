"""Idempotent spoken-form rules shared by the WebUI and agent CLI."""
from pathlib import Path
import json,re

def spoken_form(text):
    path=Path(__file__).resolve().parent/'model/pronunciation_rules.json'
    if not path.exists():return text
    settings=json.loads(path.read_text(encoding='utf-8'))
    if settings.get('enabled',True):
        for rule in settings.get('rules',[]):
            text=re.sub(rule['pattern'],rule['spoken'],text,flags=re.IGNORECASE)
    return text
