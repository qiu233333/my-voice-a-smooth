"""Punctuation-aware phrasing for the A smooth voice; no word rewriting."""
import re

def prepare_fluent_text(text):
    segments = []
    for paragraph in text.splitlines():
        for sentence in re.split(r'(?<=[。！？!?；;])|(?<=\.)(?=\s+[A-Z])', paragraph):
            sentence = sentence.strip()
            if not sentence:
                continue
            # Keep normal sentences together. Split unusually long Chinese
            # sentences only at existing commas, retaining every punctuation mark.
            if len(sentence) <= 55:
                segments.append(sentence)
                continue
            pending = ''
            for clause in re.split(r'(?<=，)', sentence):
                pending += clause
                if len(pending) >= 36:
                    segments.append(pending)
                    pending = ''
            if pending:
                if segments and len(pending) < 5:
                    segments[-1] += pending
                else:
                    segments.append(pending)
    result = '\n'.join(segments)
    if re.sub(r'\s+', '', result) != re.sub(r'\s+', '', text):
        raise ValueError('Phrasing must preserve all text and punctuation.')
    return result
