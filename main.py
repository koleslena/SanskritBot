from indic_transliteration import sanscript, detect
from indic_transliteration.sanscript import transliterate

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import datetime
import os
import logging
from response_parser import parse
from dicts_service import get_translation, get_suggestion

APT = "AP90"
WIL = "WIL"
MW = "MW"
PW = "PW"
PWG = "PWG"
BHS = "BHS"

DICTS = [APT, WIL, MW, PW, PWG, BHS]

AMARA = "AMARA"

TRANSLATE = "translate"
SYNONYMS = "amarakosha"
TRANSLIT = "translit"

logger = telebot.logger

formatter = '[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)'
logging.basicConfig(
    filename=f'bot-from-{datetime.datetime.now().date()}.log',
    filemode='w',
    format=formatter,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
)

TOKEN = os.environ.get("sansbot_token")

message_size = 2000

SUGGEST_ANSWER = "❓"

class Settings:
    def __init__(self, action):
        self.action = action
        self.sdict = MW
        
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
selectedAction = {}

def gen_main_menu():
    markup = ReplyKeyboardMarkup(True, False)
    # markup.row_width = 2
    markup.add(KeyboardButton("/menu"),
               KeyboardButton("/dicts"),
               KeyboardButton("/help"))
    return markup


def gen_markup_actions():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("TRANSLATE", callback_data=TRANSLATE),
               InlineKeyboardButton("AMARAKOSHA", callback_data=SYNONYMS),
               InlineKeyboardButton("TRANSLITERATE", callback_data=TRANSLIT))
    return markup


def gen_markup_dicts():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("MW", callback_data=MW),
               InlineKeyboardButton("PW", callback_data=PW),
               InlineKeyboardButton("PWG", callback_data=PWG),
               InlineKeyboardButton("WIL", callback_data=WIL),
               InlineKeyboardButton("BHS", callback_data=BHS),
               InlineKeyboardButton("APTE", callback_data=APT),
               )
    return markup

def clean_text(text):
    return text.strip().lstrip().rstrip().replace(',', '').replace(';', '').replace('.', '').replace('-', '') if text else ""

def get_translit(message):
    try:
        term = clean_text(message.text)
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
        logger.error(e)
        return 'Ooopss..'

def get_translate(message):
    try:
        input_alp = 'slp1'
        term = orig_term = clean_text(message.text)
        if not message.reply_markup:
            if detect.detect(term) == sanscript.IAST:
                input_alp = 'iast'
                term = transliterate(term, sanscript.IAST, sanscript.SLP1)
            elif detect.detect(term) == sanscript.DEVANAGARI:
                input_alp = 'deva'
                term = transliterate(term, sanscript.DEVANAGARI, sanscript.SLP1)
            elif detect.detect(term) == sanscript.HK:
                input_alp = 'hk'
                term = transliterate(term, sanscript.HK, sanscript.SLP1)
        chat_id = message.chat.id
        sdict = selectedAction[chat_id].sdict if selectedAction[chat_id].sdict else MW
        resp = get_translation(term, sdict)
        ret = sugg = []
        if resp.status_code // 10 == 20 and resp.text:
            if sdict == AMARA:
                ret = resp.json()
                if len(ret) != 0:
                    ret = ret[0]
                    if len(ret) != 0 and 'data' in ret.keys():
                        data = transliterate(ret['data'], sanscript.SLP1, sanscript.IAST)
                        ret = [data.replace("|", ".").replace("***", " || ").replace("**", " |\n").replace("*", "\n\n")]
            else:
                ret = parse(resp.json())
        if len(ret) == 0:
            sugg = get_suggestion(orig_term, sdict, input_alp)
        return ret, sugg
    except Exception as e:
        logger.error(e)
        return ['Ooopss..😢'], []

def cut_chunk(str):
    ancore = len(str)
    for i in range(len(str) - 2, -1, -1):
        if str[i] == '<' and str[i + 1] != '/':
            ancore = i
            break
    return (str[:ancore], ancore) if ancore != 2 else (str, len(str))

def cut_answer(answer):
    answer_size = len(answer)

    if answer_size > message_size:
        lst = []
        chunks = 2
        chunk_size = message_size
        for i in range(2, 50):
            chunks = i
            chunk_size = answer_size // i
            if answer_size // i < message_size:
                break
        ancore = 0
        for i in range(chunks + 1):
            if ancore+chunk_size <= answer_size:
                mes, ancore_i = cut_chunk(answer[ancore: ancore+chunk_size])
                ancore += ancore_i
            else:
                mes = answer[ancore: answer_size]
            lst.append(mes)
        return lst
    return [answer]

def get_answer(message):
    try:
        chat_id = message.chat.id
        if chat_id not in selectedAction:
            selectedAction[chat_id] = Settings(TRANSLATE)
        if selectedAction[chat_id].action == TRANSLIT:
            bot.send_message(message.chat.id, get_translit(message))
        elif selectedAction[chat_id].action in [TRANSLATE, SYNONYMS]:
            lst, sugg = get_translate(message)
            res_answer = '\n'.join(lst)
            if len(res_answer) != 0:
                if len(res_answer) < message_size:
                    bot.send_message(message.chat.id, res_answer)
                else:
                    for answer in lst:
                        for part_answer in cut_answer(answer):
                            bot.send_message(message.chat.id, part_answer)
            else:
                if not sugg or len(sugg) == 0:
                    bot.send_message(message.chat.id, "🤷")
                else:
                    markup = InlineKeyboardMarkup()
                    markup.row_width = 1
                    for s in sugg:
                        markup.add(InlineKeyboardButton(s["name"], callback_data=s["value"]))
                    bot.send_message(message.chat.id, SUGGEST_ANSWER, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Please use menu /menu")
    except Exception as e:
        logger.error(e)
        bot.send_message(message.chat.id, "something went wrong 😢 try again later")


# Handle '/menu'
@bot.message_handler(commands=['menu'])
def handle_actions(message):
    msg = bot.send_message(message.chat.id, f"""\
    Please choose \
    """, reply_markup=gen_markup_actions())


# Handle '/dicts'
@bot.message_handler(commands=['dicts'])
def handle_dicts(message):
    msg = bot.send_message(message.chat.id, f"""\
    Please choose the dictionary \
    \n\n<b>MW</b>  -- Monier-Williams Sanskrit-English Dictionary \
    \n\n<b>PW</b>  -- Böhtlingk Sanskrit-Wörterbuch in kürzerer Fassung \
    \n\n<b>PWG</b> -- Böhtlingk and Roth Grosses Petersburger Wörterbuch \
    \n\n<b>APTE</b> -- Apte Practical Sanskrit-English Dictionary \
    \n\n<b>WIL</b> -- Wilson Sanskrit-English Dictionary \
    \n\n<b>BHS</b> -- Edgerton Buddhist Hybrid Sanskrit Dictionary \
    """, reply_markup=gen_markup_dicts())


# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = bot.send_message(message.chat.id, f"""\
    Hi, <i>{message.from_user.first_name}</i>, I am SanskritBot.
    \n\nI can transliterate to or from DEVANAGARI \
    \n\ntranslate Sanskrit -> English (MW, APTE, WIL) \
    \n\ntranslate Sanskrit -> German (PW, PWG) \
    \n\ntranslate Buddhist Hybrid Sanskrit -> English (BHS) \
    \n\nfind synonyms in AMARAKOSHA 
    \n\nPlease use menu /menu \
    \n\nFor choosing dictionary call /dicts, by default we use MW \
    \n\nFor help use /help command \
    """, reply_markup=gen_main_menu())


# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    msg = bot.send_message(message.chat.id, f"""\
    \n\nI can transliterate to or from DEVANAGARI \
    \n\ntranslate Sanskrit -> English (MW, APTE, WIL) \
    \n\ntranslate Sanskrit -> German (PW, PWG) \
    \n\ntranslate Buddhist Hybrid Sanskrit -> English (BHS) \
    \n\nfind synonyms in AMARAKOSHA 
    \n\nPlease use menu /menu \
    \n\nFor choosing dictionary call /dicts, by default we use MW 
    \n\nDictionaries data from https://sanskrit-lexicon.uni-koeln.de/ \
    \n\nAmarakosha data from https://ashtadhyayi.com/ \
    \n\nQuestions and suggestions @ekolesnikova \
""", reply_markup=gen_main_menu())


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        chat_id = call.message.chat.id
        if chat_id not in selectedAction:
            selectedAction[chat_id] = Settings(TRANSLATE)
        if call.data in [TRANSLIT, TRANSLATE, SYNONYMS]:
            selectedAction[chat_id].action = call.data
            if call.data == SYNONYMS:
                selectedAction[chat_id].sdict = AMARA
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=InlineKeyboardMarkup())
            text = f"{call.data} selected. Send your word" if call.data in [TRANSLIT, SYNONYMS] else f"{call.data} selected. Send your word or choose the dictionary" 
            bot.send_message(call.from_user.id, text)

        elif call.data in DICTS:
            selectedAction[chat_id].sdict = call.data
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=InlineKeyboardMarkup())
            bot.send_message(call.from_user.id, f"{call.data} selected. Send your text")

        else:
            if call.message.text == SUGGEST_ANSWER:
                call.message.text = call.data
                get_answer(call.message)
            else:
                bot.send_message(call.from_user.id, "🤷")

    except:
        bot.send_message(call.from_user.id, 'something went wrong try again later')


@bot.edited_message_handler(func=lambda message: True)
def handle_edited_message(message):
    get_answer(message)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    get_answer(message)


bot.polling(none_stop=True, interval=0)
