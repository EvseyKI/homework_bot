import os
from dotenv import load_dotenv
import logging
from exception import SendMessageFailed, ConnectionError, EmptyResponse
import requests

load_dotenv()

logger = logging.getLogger(__name__)

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
    """Проверяет доступность переменных окружения"""
    list_tokens = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    return all(list_tokens)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Новое сообщение в чате: {message}')
    except Exception as error:
        raise SendMessageFailed(f'Не удалось отправить сообщение: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса"""
    params = {'from_date': timestamp}
    api_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params,
    }
    try:
        logger.info('Запрос к API')
        response = requests.get(**api_params)
    except Exception as error:
        raise ConnectionError(f'Ошибка запроса: {error}')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации"""
    if not isinstance(response, dict):
        message = (
            f'Данные пришли не в dict, а в {type(response)}'
        )
        raise TypeError(message)
    if not isinstance(response.get('homeworks'), list):
        received_data = response.get('homeworks')
        message = (
            f'Данные пришли не в list, а в {type(received_data)}'
        )
        raise TypeError(message)
    if 'homeworks' not in response:
        message = ('Ответ не содержит домашних работ.')
        raise EmptyResponse(message)


def parse_status(homework):
    """извлекает из информации о конкретной 
        домашней работе статус этой работы"""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    return (
        f'Изменился статус проверки работы "{homework_name}". {verdict}'
        .format(homework_name=homework_name, verdict=HOMEWORK_VERDICTS[status])
    )


def main():
    """Основная логика работы бота."""

    ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
