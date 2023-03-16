import json
import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

from exception import EmptyResponse, HTTPRequestError, SendMessageFailed

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=50000000,
    backupCount=2
)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    list_tokens = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    return all(list_tokens)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Новое сообщение в чате: {message}')
    except telegram.TelegramError:
        logger.error('Не удалось отправить сообщение об ошибке!')
    except Exception as error:
        raise SendMessageFailed(f'Не удалось отправить сообщение: {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    api_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params,
    }
    try:
        logger.info('Запрос к API')
        response = requests.get(**api_params)
        if response.status_code != HTTPStatus.OK:
            raise HTTPRequestError(response)
        return response.json()
    except requests.RequestException as e:
        logger.info(e)
    except json.decoder.JSONDecodeError:
        logger.info('Проблема с функцией json')


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not response:
        message = 'В ответ получен пустой словарь!'
        raise EmptyResponse(message)
    if not isinstance(response, dict):
        message = f'Данные пришли не в dict, а в {type(response)}'
        raise TypeError(message)
    if 'homeworks' not in response:
        message = 'Ответ не содержит домашних работ.'
        raise EmptyResponse(message)
    if not isinstance(response.get('homeworks'), list):
        received_data = response.get('homeworks')
        message = f'Данные пришли не в list, а в {type(received_data)}'
        raise TypeError(message)
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает статус работы."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if not homework_name:
        message = 'У работы отсутствует name'
        raise KeyError(message)
    if status not in HOMEWORK_VERDICTS:
        message = 'Статус работы неизвестен, либо отсутствует'
        raise EmptyResponse(message)
    return (
        'Изменился статус проверки работы "{homework_name}". {verdict}'
        .format(homework_name=homework_name, verdict=HOMEWORK_VERDICTS[status])
    )


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens():
        message = 'Не все токены доступны'
        logger.critical(message)
        sys.exite(message)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logger.debug('Нет проверенной домашней работы')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
