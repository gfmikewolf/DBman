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
        lang = session.get('LANG', self.lang)
        if is_spec:
            dbman_dict = self.spec_dict[lang]
        else:
            dbman_dict = self.general_dict[lang]

        # 预处理：多词短语或含特殊字符短语，按长度降序
        multi_word_keys = sorted(
            (key for key in dbman_dict if ' ' in key or "'" in key),
            key=lambda x: len(x),
            reverse=True
        )
        for phrase in multi_word_keys:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            input_text = pattern.sub(dbman_dict[phrase], input_text)

        tokens = re.split(r'(\W+)', input_text)
        translated_tokens: list[tuple[str, bool]] = []
        for token in tokens:
            lower = token.lower()
            if lower in dbman_dict:
                translated_tokens.append((dbman_dict[lower], True))
            else:
                translated_tokens.append((token, False))

        # 重建最终字符串
        # 只有目标语言是中文时，才删除相邻翻译词之间的空格
        if lang == 'zh':
            result: list[str] = []
            n = len(translated_tokens)
            for i, (token, _) in enumerate(translated_tokens):
                if token.isspace():
                    # 如果该空格两侧均为翻译成功的词，就跳过它
                    if i > 0 and i < n-1 and translated_tokens[i-1][1] and translated_tokens[i+1][1]:
                        continue
                result.append(token)
            return ''.join(result)
        else:
            # 非中文目标语言，直接保留所有空格
            return ''.join(token for token, _ in translated_tokens)

