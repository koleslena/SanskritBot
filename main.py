from indic_transliteration import sanscript, detect
from indic_transliteration.sanscript import transliterate

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import urllib.request
import datetime
import os
import logging
from DictParser import DictParser
from markdown_util import parse_answer

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

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
selectedAction = {}
URL_DICT = "https://sanskrit-lexicon.uni-koeln.de/scans/{}Scan/2020/web/webtc/getword.php?%s"


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
               InlineKeyboardButton("WILSON", callback_data=WIL),
               InlineKeyboardButton("APTE", callback_data=APT),
               )
    return markup


def get_translit(s):
    try:
        if detect.detect(s) == sanscript.DEVANAGARI:
            return transliterate(s, sanscript.DEVANAGARI, sanscript.IAST)
        elif detect.detect(s) == sanscript.IAST:
            return transliterate(s, sanscript.IAST, sanscript.DEVANAGARI)
        elif detect.detect(s) == sanscript.ITRANS:
            return transliterate(s, sanscript.DEVANAGARI, sanscript.HK)
        elif detect.detect(s) == sanscript.HK:
            return transliterate(s, sanscript.HK, sanscript.DEVANAGARI)
    except Exception as e:
        logger.error(e)
        return 'Ooopss..'


def get_lines(answer):
    parser = DictParser()
    parser.feed(answer)
    lines = parser.get_cleaned_answer()
    return lines


def get_translate(s):
    try:
        translit_ = 'hk'
        if detect.detect(s) == sanscript.DEVANAGARI:
            translit_ = 'deva'
        params = urllib.parse.urlencode({'key': s, 'filter': 'roman', 'accent': 'no', 'transLit': translit_})
        dict_ = MW
        if selectedAction.get('dict'):
            dict_ = selectedAction['dict']
        url = URL_DICT.format(dict_) % params
        ans = urllib.request.urlopen(url).read().decode("utf-8")
        return parse_answer(get_lines(ans), url)
    except Exception as e:
        logger.error(e)
        return 'Ooopss..'


def get_answer(message):
    try:
        if selectedAction['action'] == TRANSLIT:
            bot.send_message(message.chat.id, get_translit(message.text))
        elif selectedAction['action'] == TRANSLATE:
            bot.send_message(message.chat.id, get_translate(message.text))
    except Exception as e:
        logger.error(e)
        bot.send_message(message.chat.id, "Please choose the action")
        return 'Ooopss..'


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
    I can transliterate to/from DEVANAGARI \
    and translate Sanskrit -> English (MW).
    Please choose the action \
    """, reply_markup=gen_main_menu())


# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    msg = bot.send_message(message.chat.id, f"""\
    I can transliterate to/from DEVANAGARI \
    and translate Sanskrit -> English (MW) \
    Please choose the action  \
""", reply_markup=gen_main_menu())


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        if call.data == TRANSLIT:
            selectedAction['action'] = TRANSLIT
            bot.send_message(call.from_user.id, "Send your text")

        elif call.data == TRANSLATE:
            selectedAction['action'] = TRANSLATE
            bot.send_message(call.from_user.id, "Send your text or choose the dictionary")

        elif call.data == MW:
            selectedAction['dict'] = MW
            bot.send_message(call.from_user.id, "Send your text")

        elif call.data == WIL:
            selectedAction['dict'] = WIL
            bot.send_message(call.from_user.id, "Send your text")

        elif call.data == APT:
            selectedAction['dict'] = APT
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
