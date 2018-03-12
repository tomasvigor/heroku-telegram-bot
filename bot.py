# -*- coding: utf-8 -*-

import os
import requests
import time

token = os.environ['TELEGRAM_TOKEN']


def get_updates_json():  
    response = requests.get("https://api.telegram.org/bot{0}/getUpdates".format(token))
    return response.json()
print(get_updates_json())

while True:
    print(get_updates_json())
    time.sleep(3)



#some_api_token = os.environ['SOME_API_TOKEN']
#             ...

# If you use redis, install this add-on https://elements.heroku.com/addons/heroku-redis
#r = redis.from_url(os.environ.get("REDIS_URL"))

#       Your bot code below
# bot = telebot.TeleBot(token)
# some_api = some_api_lib.connect(some_api_token)
#              ...
