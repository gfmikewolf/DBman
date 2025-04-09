# app/utils/translation_mj.py
import re
from flask import session

class TranslationMJ:

    def __init__(self, 
                 lang_set:list[str],
                 lang: str,
                 general_dict: dict[str, dict[str, str]] = {}, 
                 spec_dict: dict[str, dict[str, str]] = {}) -> None:
        self.lang_set = lang_set
        self.lang = lang
        self.general_dict = general_dict
        self.spec_dict = spec_dict

    def translate(self, input_text: str, is_spec: bool = False):
        # 预处理：先替换掉多词短语或含特殊字符的短语
        # 例如，处理包含空格或撇号的键
        lang = session.get('LANG', self.lang)
        if is_spec:
            dbman_dict = self.spec_dict[lang]
        else:
            dbman_dict = self.general_dict[lang]
            
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

