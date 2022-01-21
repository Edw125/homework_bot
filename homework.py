import logging
import telegram
import time
import requests
import os

from dotenv import load_dotenv
from exceptions import TokenError
from logging.handlers import RotatingFileHandler
from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler = RotatingFileHandler('homework.log', maxBytes=50000000, backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info('Бот отправил сообщение: '
                f'{message}')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == HTTPStatus.OK:
        logger.info(f'Запрос получен. Статус ответа: {response.status_code}')
        return response.json()
    else:
        message = ('Сбой в работе программы: '
                   f'Эндпоинт {ENDPOINT} недоступен. '
                   f'Код ответа API: {response.status_code}')
        logger.error(message)
        # send_message(bot, message)
        raise response.raise_for_status()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) == dict:
        homeworks = response.get('homeworks')
        if type(homeworks) == list:
            return homeworks
        else:
            error = f'Тип данных {type(homeworks).__name__} не список'
            logger.error(error)
            # send_message(bot, error)
            raise TypeError(error)
    else:
        error = f'Тип данных {type(response).__name__} не словарь'
        logger.error(error)
        # send_message(bot, error)
        raise TypeError(error)


def parse_status(homework):
    """Получает статус конкретной домашней работы."""
    homework_name = homework.get('homework_name')
    if homework_name:
        homework_status = homework.get('status')
        if homework_status in HOMEWORK_STATUSES.keys():
            verdict = HOMEWORK_STATUSES.get(homework_status)
            message = ('Изменился статус проверки работы '
                       f'"{homework_name}". {verdict}')
            return message
        else:
            error = 'Недокументированный статус домашней работы'
            logger.error(error)
            raise KeyError(error)
    else:
        error = 'Статус домашней работы отсутствует'
        logger.error(error)
        raise KeyError(error)

        # error = StatusError()
        # logger.error(error)
        # send_message(bot, error)
        # raise error


def check_tokens():
    """Проверяет доступность переменных окружения."""
    token_list = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in token_list:
        if not token:
            return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())
        container = ''
        while True:
            try:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)
                if homeworks:
                    message = parse_status(homeworks[0])
                    current_timestamp = response.get('current_date')
                    if container != message:
                        send_message(bot, message)
                    else:
                        logger.debug('Статус домашней работы не изменился')
                else:
                    message = 'Домашняя работа не найдена'
                    if container != message:
                        send_message(bot, message)
                    else:
                        logger.debug('Статус домашней работы не изменился')
                time.sleep(RETRY_TIME)
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                time.sleep(RETRY_TIME)
            else:
                container = message
    else:
        error = TokenError(env=os.environ)
        logger.critical(error)
        raise error

        # error = ('Отсутствует обязательная переменная окружения. '
        #          'Программа принудительно остановлена.')
        # logger.critical(error)
        # raise NameError(error)


if __name__ == '__main__':
    main()
