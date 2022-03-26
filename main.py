from indic_transliteration import sanscript, detect
from indic_transliteration.sanscript import transliterate

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import urllib.request
import datetime
import os
import logging
from DictParser import DictParser
from markdown_util import parse_answer

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
URL_MV = "https://sanskrit-lexicon.uni-koeln.de/scans/MWScan/2020/web/webtc/getword.php?%s"


def gen_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("TRANSLITERATE", callback_data="translit"),
               InlineKeyboardButton("TRANSLATE", callback_data="translate"))
    return markup


def get_translit(s):
    try:
        if detect.detect(s) == sanscript.DEVANAGARI:
            return transliterate(s, sanscript.DEVANAGARI, sanscript.ITRANS)
        elif detect.detect(s) == sanscript.ITRANS:
            return transliterate(s, sanscript.ITRANS, sanscript.DEVANAGARI)
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
        translit = 'hk'
        if detect.detect(s) == sanscript.DEVANAGARI:
            translit = 'deva'
        params = urllib.parse.urlencode({'key': s, 'filter': 'roman', 'accent': 'no', 'transLit': translit})
        url = URL_MV % params
        ans = urllib.request.urlopen(url).read().decode("utf-8")
        return parse_answer(get_lines(ans), url)
    except Exception as e:
        logger.error(e)
        return 'Ooopss..'


def get_answer(message):
    try:
        if selectedAction['action'] == "translit":
            bot.send_message(message.chat.id, get_translit(message.text))
        elif selectedAction['action'] == "translate":
            bot.send_message(message.chat.id, get_translate(message.text))
    except Exception as e:
        logger.error(e)
        bot.send_message(message.chat.id, "Please choose an action")
        return 'Ooopss..'


# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = bot.send_message(message.chat.id, f"""\
    Hi, <i>{message.from_user.first_name}</i>, I am SanskritBot.
    I can transliterate to/from DEVANAGARI \
    and translate Sanskrit -> English (MV).
    Choose the action \
    """, reply_markup=gen_markup())


# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    msg = bot.send_message(message.chat.id, f"""\
    I can transliterate to/from DEVANAGARI \
    and translate Sanskrit -> English (MV) \
    Choose the action ? \
""", reply_markup=gen_markup())


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        if call.data == "translit":
            selectedAction['action'] = 'translit'
            bot.send_message(call.from_user.id, "Send your text")

        elif call.data == "translate":
            selectedAction['action'] = 'translate'
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
