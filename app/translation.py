# app/translation.py
import os
import json
from flask import session, request, redirect, url_for

LangSet = ['en', 'zh']

def set_lang(lang):
    # 将选择的语言存储到 session 中
    if lang in LangSet:
        session['language'] = lang
        # 清除缓存的 translations
    else:
        print(f"Invalid language parameter: {lang}")  # 调试日志
    return redirect(request.referrer or url_for('index'))  # 重定向回上一页

def get_lang():
    # 获取用户首选语言
    lang = session.get('language')
    if not lang:
        # 使用浏览器的 Accept-Language 头
        lang = request.accept_languages.best_match(LangSet)
        print(f"Detected browser language: {lang}")  # 调试日志
        # 默认使用英文
        session['language'] = lang or 'en'
    return session.get('language')

def get_pagetext(locales):
    lang = get_lang()
    if lang in LangSet:
        BASE_DIR = os.path.join(os.getcwd(), 'app', 'base', 'static', 'pagetext')
        pagetext = {}
        if locales and len(locales) > 0:
            try:
                for locale in locales:
                    filepath = os.path.join(BASE_DIR, f'{locale}_{lang}.json')
                    with open(filepath, 'r', encoding='utf-8') as f:
                        jsonData = json.load(f)
                    pagetext.update(jsonData)
                return pagetext
            except FileNotFoundError:
                print(f"pagetext file {filepath} not found")  # 调试日志
            return None

def translate_text(input_text, pagetext, lang):
    # 分割输入文本为单词列表
    words = input_text.split()
    
    # 替换单词为翻译，如果找不到翻译则保留原单词
    translated_words = [pagetext.get(word.lower(), word) for word in words]
    
    # 将翻译后的单词重新组合成字符串
    if lang == 'en': 
        char_split = ' '
    elif lang == 'zh':
        char_split = ''
    
    return char_split.join(translated_words)
