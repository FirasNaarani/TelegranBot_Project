import os
import boto3
import requests
import telebot
import time
from loguru import logger
from telebot.types import InputFile
from botocore.exceptions import ClientError

URL = os.environ['YOLO_URL']
IMAGES_BUCKET = os.environ['BUCKET_NAME']

class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(
            URL=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(
            f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(
            chat_id, text, reply_to_message_id=quoted_msg_id)

    @staticmethod
    def is_current_msg_photo(msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(
            msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'],
                       f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(
                msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ObjectDetectionBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            # TODO download the user photo (utilize download_user_photo)
            file_path = self.download_user_photo(msg)
            print(file_path)
            # TODO upload the photo to S3
            client = boto3.client('s3')
            try:
                client.upload_file(file_path, IMAGES_BUCKET,
                                    f"bot/received/{os.path.basename(file_path)}")
                print("uploaded")
            except ClientError as e:
                logger.info(e)
                return False
            # TODO send a request to the `yolo5` service for prediction localhost:8081/predict?imgName=nfb
            response = requests.post(
                f"{URL}/predict?imgName=bot/received/{os.path.basename(file_path)}")
            # TODO send results to the Telegram end-user
            if response.ok:
                data = response.json()
                utility = Util(data)
                processed_data = utility.objects_counter()
                self.send_text(msg['chat']['id'], f"{processed_data}")


class Util:
    def __init__(self, json_data):
        self.json_data = json_data

    def objects_counter(self):
        total_items = len(self.json_data['labels'])
        print(f"There are {total_items} items in the JSON")
        class_count = {}
        for item in self.json_data['labels']:
            class_name = item["class"]
            if class_name in class_count:
                class_count[class_name] += 1
            else:
                class_count[class_name] = 1
        if len(class_count) == 0:
            return "Zero objects Detected :("
        else:
            result = '.:: Detected Objects ::.\n'
            for key, val in class_count.items():
                result += f"\t{key}\t-->\t{val}\n"
            return result