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
    # 使用正则表达式拆分文本，同时保留非字母分隔符
    # (\W+) 捕获所有非字母数字下划线的连续字符（包括空格、标点等）
    tokens = re.split(r'(\W+)', input_text)
    
    translated_tokens = []
    for token in tokens:
        # 如果 token 全为字母（isalpha 判断排除数字和标点），就翻译单词（忽略大小写）
        if token.isalpha():
            translated_tokens.append(dbman_dict.get(token.lower(), token))
        else:
        # 对于连续空格，保留原样，不进行翻译，对于非空格的其他字符，直接翻译
            if token.isspace():
                translated_tokens.append(token)
            else:
                translated_tokens.append(dbman_dict.get(token.lower(), token))
    
    # 如果目标语言为中文，则删除翻译结果中所有仅包含空格的 token，
    # 这样翻译成中文的句子就不会有英文句内的空格
    if lang == 'zh':
        return ''.join(token for token in translated_tokens if not token.isspace())
    else:
        return ''.join(translated_tokens)

