import datetime
import sys
import logging

# Настройка логирования
formatter = '[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)'
logging.basicConfig(
    # filename=f'bot-from-{datetime.datetime.now().date()}.log',
    # filemode='w',
    format=formatter,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout) 
    ]
)
logger = logging.getLogger(__name__)