import aiohttp
from typing import List, Any, Tuple

from config import settings
from logger import logger

# Переводим проверку успешности статуса 
def _is_success(status: int) -> bool:
    return 200 <= status < 300

async def get_forms(session: aiohttp.ClientSession, term: str, linga: str) -> Tuple[List[Any], List[Any]]:
    """
    Получение грамматических форм слова (Shabda).
    """
    ret: List[Any] = []
    sugg: List[Any] = []
    
    # 1. Запрос на получение основных форм (GET /shabda)
    url_shabda = f"{settings.API_URL}/shabda"
    params_shabda = {"term": term, "linga": linga}
    
    try:
        async with session.get(url_shabda, params=params_shabda) as resp:
            if _is_success(resp.status):
                ret = await resp.json()
                
        # 2. Если формы не найдены, запрашиваем подсказки (GET /shabda/suggest)
        if not ret:
            url_suggest = f"{settings.API_URL}/shabda/suggest"
            params_suggest = {"term": term}
            async with session.get(url_suggest, params=params_suggest) as resp:
                if _is_success(resp.status):
                    sugg = await resp.json()
                    
    except aiohttp.ClientError as e:
        logger(f"API Error (get_forms): {e}")
        
    return ret, sugg