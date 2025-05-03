import json
import os

def sort_json_dict(*filename: str):
    for fn in filename:
        if not os.path.isfile(fn):
            raise FileNotFoundError(f"File {fn} does not exist.")
        with open(fn, 'r', encoding='utf-8') as f:
            data = json.load(f)

        phrases = {k.lower(): v for k, v in data.items() if ' ' in k}
        singles = {k.lower(): v for k, v in data.items() if ' ' not in k}

        sorted_phrases = dict(sorted(phrases.items()))
        sorted_singles = dict(sorted(singles.items()))

        sorted_dict = {**sorted_phrases, **sorted_singles}

        base, ext = os.path.splitext(fn)
        backup_name = f"{base}_backup{ext}"

        if os.path.isfile(backup_name):
            os.remove(backup_name)
        os.rename(fn, backup_name)

        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(sorted_dict, f, ensure_ascii=False, indent=4)

        print(f"Backup file: {backup_name}")
        print(f"Sorted file written to: {fn}")

if __name__ == "__main__":
    sort_json_dict(
        'asset_zh.json',
        'asset_en.json',
        'contract_zh.json',
        'contract_en.json',
        'locale_zh.json',
        'locale_en.json',
        'user_zh.json',
        'user_en.json'
    )
