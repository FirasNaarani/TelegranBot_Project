import flask
from flask import request
from dotenv import load_dotenv
import os

from loguru import logger
from bot import ObjectDetectionBot, Bot

app = flask.Flask(__name__)

# Provide the path to the .env file
load_dotenv('/run/secrets/my_secret')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_APP_URL = os.getenv('TELEGRAM_APP_URL')


@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    logger.info(f'Incoming REQ: {req}')
    bot.handle_message(req['message'])
    return 'Ok'


if __name__ == "__main__":
    bot = Bot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)

    app.run(host='0.0.0.0', port=8443)
