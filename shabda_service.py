import requests

URL_SHABDA = "http://127.0.0.1:4000/api/shabda?term={}&linga={}"
URL_SHABDA_SUGGEST= "http://127.0.0.1:4000/api/shabda/suggest?term={}"

def get_forms(term, linga):
    ret = sugg = []
    url = URL_SHABDA.format(term, linga)
    resp = requests.get(url)
    if resp.status_code // 10 == 20 and resp.text:
        ret = resp.json()
    if len(ret) == 0:
        url = URL_SHABDA_SUGGEST.format(term)
        resp = requests.get(url)
        if resp.status_code // 10 == 20 and resp.text:
            sugg = resp.json()
    return ret, sugg
