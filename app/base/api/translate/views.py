# api/translate/views.py
from app.utils.common import _

def translate_g(input_text:str):
    return _(input_text, True)

def translate_s(input_text:str):
    return _(input_text, is_spec=True)
