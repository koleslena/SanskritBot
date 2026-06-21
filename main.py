import asyncio
import io
import easyocr
import prettytable as pt
import torch
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from indic_transliteration import detect, sanscript
from indic_transliteration.sanscript import transliterate
import aiohttp

from PIL import Image
import io


# Импорты ваших локальных сервисов
from dicts_service import get_suggestion, get_translation
from response_parser import parse
from shabda_service import get_forms
import logging

from config import settings  

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Константы словарей
APT = "AP90"
WIL = "WIL"
MW = "MW"
PW = "PW"
PWG = "PWG"
BHS = "BHS"
DICTS = [APT, WIL, MW, PW, PWG, BHS]

VIBHACTIES = ['pr(N)', 'dv(Acc)', 'tr(I)', 'ca(D)', 'pa(Abl)', 'Sa(G)', 'sa(L)', 'samb(V)']
VACANAM = ['Sing', 'Du', 'Pl']
LINGAS = {'P': 'masc', 'N': 'neut', 'S': 'fem', 'A': 'all'}
AMARA = "AMARA"

TRANSLATE = "translate"
SYNONYMS = "amarakosha"
TRANSLIT = "translit"
SHABDA = "shabda"

SUGGEST_ANSWER = "❓"
MESSAGE_SIZE = 2000

# Инициализация EasyOCR
try:
    cuda_is_available = torch.cuda.is_available()
    if cuda_is_available:
        torch.cuda.set_per_process_memory_fraction(0.4, 0)
    reader = easyocr.Reader(['hi', 'en'], gpu=cuda_is_available)
except Exception as e:
    logging.error(f"EasyOCR Init Error: {e}")

# --- Генераторы клавиатур ---

def gen_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="/menu")
    builder.button(text="/dicts")
    builder.button(text="/ocr")
    builder.button(text="/help")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def gen_markup_actions():
    builder = InlineKeyboardBuilder()
    builder.button(text="TRANSLATE", callback_data=TRANSLATE)
    builder.button(text="AMARAKOSHA", callback_data=SYNONYMS)
    builder.button(text="SHABDA", callback_data=SHABDA)
    builder.button(text="TRANSLITERATE", callback_data=TRANSLIT)
    builder.adjust(2)
    return builder.as_markup()


def gen_markup_dicts():
    builder = InlineKeyboardBuilder()
    builder.button(text="MW", callback_data=MW)
    builder.button(text="PW", callback_data=PW)
    builder.button(text="PWG", callback_data=PWG)
    builder.button(text="WIL", callback_data=WIL)
    builder.button(text="BHS", callback_data=BHS)
    builder.button(text="APTE", callback_data=APT)
    builder.adjust(2)
    return builder.as_markup()

# --- Вспомогательные функции бизнес-логики ---

def squizee(photo_bytes):

    # файл картинки в bytes (photo_bytes)
    image = Image.open(io.BytesIO(photo_bytes))

    # Если одна из сторон больше 1500 пикселей, пропорционально уменьшаем
    max_size = 1500
    if image.width > max_size or image.height > max_size:
        image.thumbnail((max_size, max_size))
        
        # Сохраняем сжатую картинку обратно в байты для EasyOCR
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85) # quality=85 снизит вес файла
        photo_bytes = img_byte_arr.getvalue()
    
    return photo_bytes

def clean_text(text):
    return text.strip().replace(',', '').replace(';', '').replace('.', '').replace('-', '') if text else ""

def get_translit(text):
    try:
        term = clean_text(text)
        if detect.detect(term) == sanscript.DEVANAGARI:
            return transliterate(term, sanscript.DEVANAGARI, sanscript.IAST)
        elif detect.detect(term) == sanscript.IAST:
            return transliterate(term, sanscript.IAST, sanscript.DEVANAGARI)
        elif detect.detect(term) == sanscript.ITRANS:
            return transliterate(term, sanscript.DEVANAGARI, sanscript.HK)
        elif detect.detect(term) == sanscript.HK:
            return transliterate(term, sanscript.HK, sanscript.DEVANAGARI)
        else:
            return transliterate(term, sanscript.SLP1, sanscript.DEVANAGARI)
    except Exception as e:
        logging.error(e)
        return 'Ooopss..'

def transliteration(term):
    input_alp = 'slp1'
    if detect.detect(term) == sanscript.IAST:
        input_alp = 'iast'
        term = transliterate(term, sanscript.IAST, sanscript.SLP1)
    elif detect.detect(term) == sanscript.DEVANAGARI:
        input_alp = 'deva'
        term = transliterate(term, sanscript.DEVANAGARI, sanscript.SLP1)
    elif detect.detect(term) == sanscript.HK:
        input_alp = 'hk'
        term = transliterate(term, sanscript.HK, sanscript.SLP1)
    # logging.info(f"{term}, {input_alp}")
    return term, input_alp

async def get_translate_async(session: aiohttp.ClientSession, text: str, sdict: str, has_reply_markup: bool):
    """Обновленная функция: работает напрямую с асинхонным API без потоков"""
    try:
        input_alp = 'slp1'
        term = orig_term = clean_text(text)
        if not has_reply_markup:
            term, input_alp = transliteration(term)
        
        # Напрямую вызываем асинструю функцию. Она уже возвращает готовый list/dict, а не объект ответа
        ans = await get_translation(session, term, sdict)
        ret = []
        sugg = []
        
        if ans:  # Если данные успешно получены и список не пуст
            if sdict == AMARA:
                for r in ans:
                    if r and isinstance(r, dict) and 'data' in r:
                        data = transliterate(r['data'], sanscript.SLP1, sanscript.IAST)
                        ret.append(data.replace("|", ".").replace("***", " || ").replace("**", " |\n").replace("*", "\n\n") + '\n----\n')
            else:
                # Передаем чистый JSON в вашу функцию фильтрации/парсинга
                ret = parse(ans)
                
        if len(ret) == 0:
            # Напрямую вызываем асинхронный саджест
            sugg = await get_suggestion(session, orig_term, sdict, input_alp)
            
        return ret, sugg
    except Exception as e:
        logging.error(f"Error in get_translate_async: {e}")
        return ['Ooopss..😢'], []


def cut_chunk(string_data):
    """Остается без изменений (чистая синхронная функция)"""
    ancore = len(string_data)
    for i in range(len(string_data) - 2, -1, -1):
        if string_data[i] == '<' and string_data[i + 1] != '/':
            ancore = i
            break
    return (string_data[:ancore], ancore) if ancore != 2 else (string_data, len(string_data))


def cut_answer(answer):
    """Остается без изменений (чистая синхронная функция)"""
    answer_size = len(answer)
    if answer_size > MESSAGE_SIZE:
        lst = []
        chunks = 2
        chunk_size = MESSAGE_SIZE
        for i in range(2, 50):
            chunks = i
            chunk_size = answer_size // i
            if answer_size // i < MESSAGE_SIZE:
                break
        ancore = 0
        for i in range(chunks + 1):
            if ancore + chunk_size <= answer_size:
                mes, ancore_i = cut_chunk(answer[ancore: ancore + chunk_size])
                ancore += ancore_i
            else:
                mes = answer[ancore: answer_size]
            lst.append(mes)
        return lst
    return [answer]


async def handle_search_logic(session: aiohttp.ClientSession, text: str, has_reply_markup: bool, message: types.Message, state: FSMContext):
    """
    Обновленная общая асинхронная логика.
    Первым аргументом теперь принимает активную HTTP-сессию бота.
    """
    try:
        user_data = await state.get_data()
        action = user_data.get("action", TRANSLATE)
        sdict = user_data.get("sdict", MW)

        if action == TRANSLIT:
            await message.answer(get_translit(text))
            
        elif action in [TRANSLATE, SYNONYMS]:
            # Передаем сессию внутрь
            lst, sugg = await get_translate_async(session, text, sdict, has_reply_markup)
            res_answer = '\n'.join(lst)
            if len(res_answer) != 0:
                if len(res_answer) < MESSAGE_SIZE:
                    await message.answer(res_answer)
                else:
                    for answer in lst:
                        for part_answer in cut_answer(answer):
                            await message.answer(part_answer)
            else:
                if not sugg or len(sugg) == 0:
                    await message.answer("🤷")
                else:
                    builder = InlineKeyboardBuilder()
                    for s in sugg:
                        builder.button(text=s["name"], callback_data=s["value"])
                    builder.adjust(1)
                    await message.answer(SUGGEST_ANSWER, reply_markup=builder.as_markup())
                    
        elif action == SHABDA:
            terms = text.split(";")
            term = terms[0]
            if not has_reply_markup:
                term, _ = transliteration(term)
            
            lst, suggest_lst = await get_forms(session, term, "" if len(terms) == 1 else terms[1])
            
            if len(lst) == 1:
                forms = lst[0]['forms'].split(";")
                for i in range(3):
                    table = pt.PrettyTable(['Vibh', f'Form {VACANAM[i]}'])
                    table.align['Vibh'] = 'l'
                    table.align['Form'] = 'r'
                    for vibh in range(len(VIBHACTIES)):
                        form = transliterate(forms[vibh * 3 + i], sanscript.SLP1, sanscript.IAST).replace("-", ",\n")
                        table.add_row([VIBHACTIES[vibh], form])
                    await message.answer(f'<pre>{table}</pre>')
            elif len(suggest_lst) != 0 or len(lst) != 0:
                sugg = lst if len(lst) != 0 else suggest_lst
                builder = InlineKeyboardBuilder()
                for s in sugg:
                    word = s['word']
                    linga = s['linga']
                    data = transliterate(word, sanscript.SLP1, sanscript.IAST)
                    # logging.info(f"word: {word}, data: {data}")
                    builder.button(text=f'{data} ({LINGAS[linga]})', callback_data=f'{word};{linga}')
                builder.adjust(1)
                await message.answer(SUGGEST_ANSWER, reply_markup=builder.as_markup())
            else:
                await message.answer("🤷")
        else:
            await message.answer("Please use menu /menu")
    except Exception as e:
        logging.error(f"Error in handle_search_logic: {e}")
        await message.answer("❗️ something went wrong 😢 try again later")

# --- Хэндлеры Aiogram ---

bot = Bot(token=settings.SANSBOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Глобальная переменная для сессии (или можно передавать через middleware)
http_session: aiohttp.ClientSession = None

@dp.startup()
async def on_startup():
    global http_session
    # Создаем одну сессию на весь жизненный цикл бота
    http_session = aiohttp.ClientSession()

@dp.shutdown()
async def on_shutdown():
    global http_session
    if http_session:
        await http_session.close()

@dp.message(Command("ocr"))
async def handle_ocr_command(message: types.Message):
    await message.answer("Please send a photo")


@dp.message(Command("menu"))
async def handle_menu_command(message: types.Message):
    await message.answer("Please choose", reply_markup=gen_markup_actions())


@dp.message(Command("dicts"))
async def handle_dicts_command(message: types.Message):
    text = (
        "Please choose the dictionary\n\n"
        "<b>MW</b>  -- Monier-Williams Sanskrit-English Dictionary\n\n"
        "<b>PW</b>  -- Böhtlingk Sanskrit-Wörterbuch in kürzerer Fassung\n\n"
        "<b>PWG</b> -- Böhtlingk and Roth Grosses Petersburger Wörterbuch\n\n"
        "<b>APTE</b> -- Apte Practical Sanskrit-English Dictionary\n\n"
        "<b>WIL</b> -- Wilson Sanskrit-English Dictionary\n\n"
        "<b>BHS</b> -- Edgerton Buddhist Hybrid Sanskrit Dictionary"
    )
    await message.answer(text, reply_markup=gen_markup_dicts())


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    text = (
        f"Hi, <i>{message.from_user.first_name}</i>, I am SanskritBot.\n\n"
        "I can transliterate to or from DEVANAGARI\n\n"
        "translate Sanskrit -> English (MW, APTE, WIL)\n\n"
        "translate Sanskrit -> German (PW, PWG)\n\n"
        "translate Buddhist Hybrid Sanskrit -> English (BHS)\n\n"
        "find synonyms in AMARAKOSHA\n\n"
        "find noun's forms in SHABDA\n\n"
        "Please use menu /menu\n\n"
        "For choosing dictionary call /dicts, by default we use MW\n\n"
        "For help use /help command"
    )
    await message.answer(text, reply_markup=gen_main_menu())


@dp.message(Command("help"))
async def send_help(message: types.Message):
    text = (
        "I can transliterate to or from DEVANAGARI\n\n"
        "translate Sanskrit -> English (MW, APTE, WIL)\n\n"
        "translate Sanskrit -> German (PW, PWG)\n\n"
        "translate Buddhist Hybrid Sanskrit -> English (BHS)\n\n"
        "find synonyms in AMARAKOSHA\n\n"
        "find noun's forms in SHABDA\n\n"
        "Please use menu /menu\n\n"
        "For choosing dictionary call /dicts, by default we use MW\n\n"
        "Dictionaries data from https://sanskrit-lexicon.uni-koeln.de/\n\n"
        "Amarakosha data from https://ashtadhyayi.com/\n\n"
        "Questions and suggestions @ekolesnikova"
    )
    await message.answer(text, reply_markup=gen_main_menu())


@dp.callback_query()
async def callback_query_handler(call: types.CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        action = user_data.get("action", TRANSLATE)
        sdict = user_data.get("sdict", MW)

        if call.data in [TRANSLIT, TRANSLATE, SYNONYMS, SHABDA]:
            action = call.data
            if call.data == SYNONYMS:
                sdict = AMARA
            if call.data == TRANSLATE:
                sdict = MW
                
            await state.update_data(action=action, sdict=sdict)
            await call.message.edit_reply_markup(reply_markup=None)
            
            text = f"{call.data} selected. Send your word" if call.data in [TRANSLIT, SYNONYMS, SHABDA] else f"{call.data} selected. Send your word or choose the dictionary"
            await call.message.answer(text)

        elif call.data in DICTS:
            sdict = call.data
            await state.update_data(sdict=sdict)
            await call.message.edit_reply_markup(reply_markup=None)
            await call.message.answer(f"{call.data} selected. Send your text")

        else:
            if call.message.text == SUGGEST_ANSWER:
                has_reply_markup = bool(call.message.reply_markup)
                # Передаем инлайн-клик как готовый текст для поиска
                await handle_search_logic(http_session, call.data, has_reply_markup, call.message, state)
            else:
                await call.message.answer("🤷")
                
        await call.answer()
    except Exception as e:
        logging.error(e)
        await call.message.answer('❗️ something went wrong try again later')


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    try:
        # Получаем файл фотографии наилучшего качества в буфер памяти
        photo = message.photo[-1]
        file_buffer = io.BytesIO()
        await bot.download(photo, destination=file_buffer)
        file_bytes = file_buffer.getvalue()

        file_bytes = squizee(file_bytes)
        
        # EasyOCR вычисления выносим в отдельный поток, чтобы не блокировать цикл событий
        result = await asyncio.to_thread(reader.readtext, file_bytes, canvas_size=1500, batch_size=1, detail=0)
        
        await message.answer(f"{' '.join(result)}")
    except Exception as e:
        logging.error(e)
        await message.answer('❗️ something went wrong try again later')


@dp.message(F.text)
@dp.edited_message(F.text)
async def handle_message_or_edit(message: types.Message, state: FSMContext):
    """Хэндлер для обычного текста и отредактированных сообщений"""
    has_reply_markup = bool(message.reply_markup)
    await handle_search_logic(http_session, message.text, has_reply_markup, message, state)


async def main():
    logging.warning("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())