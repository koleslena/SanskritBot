from indic_transliteration import sanscript, detect
from indic_transliteration.sanscript import transliterate

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import requests
import datetime
import os
import logging
from response_parser import parse

APT = "AP90"
WIL = "WIL"
MW = "MW"

TRANSLATE = "translate"
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

class Settings:
    def __init__(self, action):
        self.action = action
        self.sdict = MW
        
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
selectedAction = {}

URL_DICT = "http://127.0.0.1:4000/api/search?term={}&dict={}"

def gen_main_menu():
    markup = ReplyKeyboardMarkup(True, False)
    # markup.row_width = 2
    markup.add(KeyboardButton("/actions"),
               KeyboardButton("/dicts"))
    return markup


def gen_markup_actions():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("TRANSLITERATE", callback_data=TRANSLIT),
               InlineKeyboardButton("TRANSLATE", callback_data=TRANSLATE))
    return markup


def gen_markup_dicts():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("MW", callback_data=MW),
               #InlineKeyboardButton("WILSON", callback_data=WIL),
               #InlineKeyboardButton("APTE", callback_data=APT),
               )
    return markup

def clean_text(text):
    return text.strip().lstrip().rstrip().replace(',', '').replace(';', '').replace('.', '') if text else ""

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
    except Exception as e:
        logger.error(e)
        return 'Ooopss..'

def get_translate(message):
    try:
        term = clean_text(message.text)
        if detect.detect(term) == sanscript.IAST:
            term = transliterate(term, sanscript.IAST, sanscript.SLP1)
        elif detect.detect(term) == sanscript.DEVANAGARI:
            term = transliterate(term, sanscript.DEVANAGARI, sanscript.SLP1)
        elif detect.detect(term) == sanscript.HK:
            term = transliterate(term, sanscript.HK, sanscript.SLP1)
        chat_id = message.chat.id
        sdict = selectedAction[chat_id].sdict if selectedAction[chat_id].sdict else MW
        url = URL_DICT.format(term, sdict)
        resp = requests.get(url)
        return parse(resp.json()) if resp.text else "🤷"
    except Exception as e:
        logger.error(e)
        return ['Ooopss..😢']

def cut_chunk(str):
    ancore = len(str)
    for i in range(len(str) - 1, -1, -1):
        if str[i] == '<' and str[i + 1] != '/':
            ancore = i
            break
    return str[:ancore], ancore

def cut_answer(answer):
    answer_size = len(answer)
    
    if answer_size > message_size:
        lst = []
        chunks = 2
        chunk_size = message_size
        for i in range(2, 10):
            chunks = i
            chunk_size = answer_size // i
            if answer_size // i < message_size:
                break
        ancore = 0
        for i in range(chunks + 1):
            if ancore+chunk_size < answer_size:
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
        elif selectedAction[chat_id].action == TRANSLATE:
            lst = get_translate(message)
            res_answer = '\n'.join(lst)
            if len(res_answer) < message_size:
                bot.send_message(message.chat.id, res_answer)
            else:
                for answer in lst:
                    for part_answer in cut_answer(answer):
                        bot.send_message(message.chat.id, part_answer)
        else:
            bot.send_message(message.chat.id, "Please choose the action /actions")
    except Exception as e:
        logger.error(e)
        bot.send_message(message.chat.id, "something went wrong try again later")
        return 'Ooopss..😢'


# Handle '/actions'
@bot.message_handler(commands=['actions'])
def handle_actions(message):
    msg = bot.send_message(message.chat.id, f"""\
    Please choose the action \
    """, reply_markup=gen_markup_actions())


# Handle '/dicts'
@bot.message_handler(commands=['dicts'])
def handle_dicts(message):
    msg = bot.send_message(message.chat.id, f"""\
    Please choose the dictionary \
    """, reply_markup=gen_markup_dicts())


# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = bot.send_message(message.chat.id, f"""\
    Hi, <i>{message.from_user.first_name}</i>, I am SanskritBot.
    \n\nI can transliterate to or from DEVANAGARI and translate Sanskrit -> English (MW). \
    \n\nPlease choose the action /actions \
    \n\nFor choosing dictionary call /dicts, by default we use MW \
    \n\nFor help use /help command \
    """, reply_markup=gen_main_menu())


# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    msg = bot.send_message(message.chat.id, f"""\
    \n\nI can transliterate to or from DEVANAGARI and translate Sanskrit -> English (MW) \
    \n\nPlease choose the action /actions \
    \n\nFor choosing dictionary call /dicts, by default we use MW \
    \n\nDictionaries data from https://sanskrit-lexicon.uni-koeln.de/ \
""", reply_markup=gen_main_menu())


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        chat_id = call.message.chat.id
        if call.data == TRANSLIT or call.data == TRANSLATE:
            if chat_id in selectedAction:
                selectedAction[chat_id].action = call.data
            else:
                selectedAction[chat_id] = Settings(call.data)
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=InlineKeyboardMarkup())
            text = "Send your text" if call.data == TRANSLIT else "Send your text or choose the dictionary" 
            bot.send_message(call.from_user.id, text)

        elif call.data == MW or call.data == WIL or call.data == APT:
            selectedAction[chat_id].sdict = call.data
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=InlineKeyboardMarkup())
            bot.send_message(call.from_user.id, "Send your text")

    except:
        bot.send_message(call.from_user.id, 'something went wrong try again later')


@bot.edited_message_handler(func=lambda message: True)
def handle_edited_message(message):
    get_answer(message)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    get_answer(message)


bot.polling(none_stop=True, interval=0)
