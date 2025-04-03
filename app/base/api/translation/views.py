# api/translation/views.py
from app import _

def translate(input_text:str, spec_dict_names:str | None = None):
    if spec_dict_names:
        return _(input_text, spec_dict_names.split(','))
    else:
        return _(input_text)
