# app/translation.py
from csv import Error
import logging
import os
import json
from flask import session, request, redirect, url_for

LangSet = ['en', 'zh']

def set_lang(lang):
    if lang in LangSet:
        session['language'] = lang
    else:
        raise ValueError(f"Invalid language: {lang}. Expected one of {LangSet}.")
    return redirect(request.referrer or url_for('index'))

def get_lang():
    lang = session.get('language')
    if not lang:
        lang = request.accept_languages.best_match(LangSet)
        logging.info(f"Detected browser language: {lang}")
        session['language'] = lang or 'en'
    return session.get('language')

def get_dbman_dict(locales: list[str] = []) -> dict[str, str]:
    lang = get_lang()
    if lang not in LangSet:
        raise ValueError(f"Invalid language: {lang}. Expected one of {LangSet}.")
    BASE_DIR = os.path.join(os.getcwd(), 'app', 'base', 'static', 'dbman_dict')
    dbman_dict = {}
    if locales:
        try:
            for locale in locales:
                filepath = os.path.join(BASE_DIR, f'{locale}_{lang}.json')
                with open(filepath, 'r', encoding='utf-8') as f:
                    jsonData = json.load(f)
                dbman_dict.update(jsonData)
        except Error as e:
            raise FileNotFoundError(f"Error {e} occurred while loading dbman_dict file: {filepath}") # type: ignore
    return dbman_dict

import re

def translate_text(input_text, dbman_dict, lang):
    # 预处理：先替换掉多词短语或含特殊字符的短语
    # 例如，处理包含空格或撇号的键
    multi_word_keys = [key for key in dbman_dict if ' ' in key or "'" in key]
    for phrase in multi_word_keys:
        # 使用 re.escape 处理可能的特殊字符，忽略大小写匹配
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        input_text = pattern.sub(dbman_dict[phrase], input_text)
    
    # 正常拆分文本并逐词翻译
    tokens = re.split(r'(\W+)', input_text)
    translated_tokens = []
    for token in tokens:
        if token.isalpha():
            translated_tokens.append(dbman_dict.get(token.lower(), token))
        else:
            if token.isspace():
                translated_tokens.append(token)
            else:
                translated_tokens.append(dbman_dict.get(token.lower(), token))
    
    if lang == 'zh':
        return ''.join(token for token in translated_tokens if not token.isspace())
    else:
        return ''.join(translated_tokens)

