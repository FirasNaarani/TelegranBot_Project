import requests
import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile


class Bot:

    def __init__(self, token, telegram_chat_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{telegram_chat_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

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

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
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
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ObjectDetectionBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            pass
            # TODO download the user photo (utilize download_user_photo)
            # TODO upload the photo to S3
            # TODO send a request to the `yolo5` service for prediction
            # TODO send results to the Telegram end-user

import boto3

class ObjectDetectionBot(Bot):
    def __init__(self, token, telegram_chat_url, bucket_name):
        super().__init__(token, telegram_chat_url)
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name

    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            # Download the user photo
            local_img_path = self.download_user_photo(msg)

            # Upload the photo to S3
            s3_img_path = f"{msg['chat']['id']}/{os.path.basename(local_img_path)}"
            self.s3_client.upload_file(local_img_path, self.bucket_name, s3_img_path)

            # Send a request to the `yolo5` service for prediction
            # This part depends on how your `yolo5` service is set up.
            # Assuming it's a REST API that takes an image URL and returns a prediction.
            yolo5_service_url = "http://your-yolo5-service-url/predict"
            image_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_img_path}"
            response = requests.post(yolo5_service_url, json={"image_url": image_url})
            prediction = response.json()

            # Send results to the Telegram end-user
            self.send_text(msg['chat']['id'], f"Prediction: {prediction}")
