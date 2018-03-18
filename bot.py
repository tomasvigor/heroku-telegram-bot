# -*- coding: utf-8 -*-

import os
import redis
import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from time import sleep
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [['Еда', 'Развлечения'],
                  ['Машина', 'Другое'],
                  ['Статистика']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

finans = {'Еда' : 0, 'Развлечения' : 0, 'Машина' : 0, 'Другое' : 0}

r = redis.from_url(os.environ.get("REDIS_URL"))
print(r)


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


def start(bot, update):
    update.message.reply_text(
        "Привет! Я роднулин финансовый помощник. Буду помогать считать траты. "
        "Куда потратим деньги?",
        reply_markup=markup)

    return CHOOSING


def regular_choice(bot, update, user_data):
    text = update.message.text
    user_data['choice'] = text
    update.message.reply_text(
        '{}|Сколько же мы потратили на этот раз?!'.format(text.lower()))

    return TYPING_REPLY


def custom_choice(bot, update, user_data):
    update.message.reply_text("Итого за все время:"
                              "{}".format(facts_to_str(finans)))

    return CHOOSING


def received_information(bot, update, user_data):
    text = update.message.text

    if is_int(text):
        category = user_data['choice']

        old_value = r.get(category)
        print("Old value:{0}".format(old_value))

        if old_value is not None:
            new_value = old_value + int(text)
            print("New value:{0}".format(new_value))
            r.set(category, new_value)
        else:
            r.set(category, 0)

        finans[category] += int(text)
        user_data[category] = text
        del user_data['choice']

        update.message.reply_text("Клаас! Последние роднулины траты:"
                              "{}".format(facts_to_str(user_data)), reply_markup=markup)
    else:
        category = user_data['choice']
        user_data[category] ='0'
        del user_data['choice']
        update.message.reply_text("Надо денюжки вводить, а не белиберду!", reply_markup=markup)
    return CHOOSING


def done(bot, update, user_data):
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text("I learned these facts about you:"
                              "{}"
                              "Until next time!".format(facts_to_str(user_data)))

    user_data.clear()
    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(os.environ['TELEGRAM_TOKEN'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [RegexHandler('^(Еда|Развлечения|Машина|Другое)$',
                                    regular_choice,
                                    pass_user_data=True),
                       RegexHandler('^Статистика$',
                                    custom_choice,
									pass_user_data=True),
                       ],

            TYPING_CHOICE: [MessageHandler(Filters.text,
                                           regular_choice,
                                           pass_user_data=True),
                            ],

            TYPING_REPLY: [MessageHandler(Filters.text,
                                          received_information,
                                          pass_user_data=True),
                           ],
        },

        fallbacks=[RegexHandler('^Готово$', done, pass_user_data=True)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling(poll_interval = 3.0,timeout=20)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()