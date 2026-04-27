import requests
import db

WIKI_API = {
    'zh': 'https://zh.wikipedia.org/w/api.php',
    'en': 'https://en.wikipedia.org/w/api.php',
}

PARAMS = {
    'action': 'query',
    'prop': 'extracts',
    'explaintext': True,
    'redirects': 1,
    'format': 'json',
}


def fetch_wikipedia(name: str, lang: str) -> str | None:
    cached = db.get_cached(name, lang)
    if cached:
        return cached

    try:
        resp = requests.get(
            WIKI_API[lang],
            params={**PARAMS, 'titles': name},
            timeout=10,
            headers={'User-Agent': 'WriteHer/1.0 (writing-support-tool)'},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [警告] 无法获取 {lang} 维基百科内容: {e}")
        return None

    pages = data.get('query', {}).get('pages', {})
    for page_id, page in pages.items():
        if page_id == '-1':
            return None
        # Disambiguation pages often contain "(disambiguation)" or lack extracts
        extract = page.get('extract', '').strip()
        if not extract:
            return None
        db.save_cache(name, lang, extract)
        return extract

    return None
