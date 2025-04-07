import requests

URL_SEARCH = "http://127.0.0.1:4000/api/search?term={}&dict={}"

URL_SUGGEST = "http://127.0.0.1:4000/api/getSuggest?term={}&dict={}&input={}"

def get_translation(term, dict):
    resp = []
    url = URL_SEARCH.format(term, dict)
    resp = requests.get(url)
    return resp

def get_suggestion(term, dict, input_alp):
    sugg = []
    if len(term) < 3:
        return sugg
    
    url = URL_SUGGEST.format(term, dict, input_alp)
    resp = requests.get(url)
    if resp.status_code // 10 == 20 and resp.text:
        sugg = resp.json()
    if not sugg or len(sugg) == 0:
        for i in range(1, 4 if len(term) > 3 else 3):
            url = URL_SUGGEST.format(term[0: -i], dict, input_alp)
            resp = requests.get(url)
            if resp.status_code // 10 == 20 and resp.text:
                sugg = resp.json()
            if sugg and len(sugg) != 0:
                break
    
    return sugg