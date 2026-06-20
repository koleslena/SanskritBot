import aiohttp
from typing import List, Dict, Any
from config import settings
from logger import logger


# Переводим проверку успешности статуса 
def _is_success(status: int) -> bool:
    return 200 <= status < 300


async def get_translation(session: aiohttp.ClientSession, term: str, dict_name: str) -> List[Dict[str, Any]]:
    """
    Получение полнотекстового поиска / перевода слова.
    Посылает GET-запрос на /search согласно спецификации нашего нового API.
    """
    url = f"{settings.API_URL}/search"
    params = {"term": term, "dict": dict_name}
    
    try:
        async with session.get(url, params=params) as resp:
            if _is_success(resp.status):
                return await resp.json()
    except aiohttp.ClientError as e:
        logger(f"API Error (get_translation): {e}")
        
    return []


async def get_suggestion(session: aiohttp.ClientSession, term: str, dict_name: str, input_alp: str) -> List[str]:
    """
    Получение подсказок (автодополнения) для строки поиска.
    Если точного совпадения нет, функция рекурсивно усекает слово с конца.
    """
    if len(term) < 3:
        return []
    
    url = f"{settings.API_URL}/suggest"
    params = {"term": term, "dict": dict_name, "input": input_alp}
    
    try:
        # 1. Первая попытка с полным словом
        async with session.get(url, params=params) as resp:
            if _is_success(resp.status):
                sugg = await resp.json()
            else:
                sugg = []
                
        # 2. Если подсказок нет, пробуем усекать слово 
        if not sugg:
            max_iterations = 4 if len(term) > 3 else 3
            for i in range(1, max_iterations):
                params["term"] = term[0: -i]
                async with session.get(url, params=params) as resp:
                    if _is_success(resp.status):
                        sugg = await resp.json()
                    if sugg:
                        break
        return sugg if sugg else []
        
    except aiohttp.ClientError as e:
        logger(f"API Error (get_suggestion): {e}")
        return []

