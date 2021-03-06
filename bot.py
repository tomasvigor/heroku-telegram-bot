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
from datetime import datetime

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

food_category = u'\U0001F35F' + 'Еда' + u'\U0001F35F'
car_category = u'\U0001F3CE' + 'Машина' + u'\U0001F3CE'
party_category = u'\U0001F388' + 'Развлечения' + u'\U0001F388'
other_category = u'\U0001F9E6' + 'Другое' + u'\U0001F9E6'
statistics_category = u'\U0001F4C8' + 'Статистика' + u'\U0001F4C8' 


reply_keyboard = [[ food_category, party_category],
                  [ car_category, other_category],
                  [ statistics_category]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

finans = {food_category, party_category, car_category, other_category}

r = redis.from_url(os.environ.get("REDIS_URL"))


def facts_to_str():
    facts = list()

    for cat in finans:
        cat_value = r.get(md(cat))
        print(md(cat))
        if cat_value is not None:
            facts.append('{} -\t {}'.format(cat, str(int(cat_value))))

    return "\n".join(facts).join(['\n', '\n'])

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def md(key):
    prefix = str(datetime.now().month) + str(datetime.now().year)
    return prefix + '|' + key


def start(bot, update):
    update.message.reply_text(
        "Привет!" + u'\U0001F4A9' + "\n\n" +  "Я роднулин финансовый помощник" + u'\U0001F4B0'  + "\nБуду помогать считать траты. " + u'\U0001F911' +
        "\n\nКуда потратим деньги?" + u'\U0001F43C',
        reply_markup=markup)

    return CHOOSING


def regular_choice(bot, update, user_data):
    text = update.message.text
    user_data['choice'] = text
    update.message.reply_text(
        '{}\nСколько же мы потратили на этот раз?!'.format(text) + u'\U0001F43E')

    return TYPING_REPLY


def custom_choice(bot, update, user_data):
    update.message.reply_text("Итого за этот месяц:\n"
                              "{}".format(facts_to_str()))

    return CHOOSING


def received_information(bot, update, user_data):
    text = update.message.text

    if is_int(text):
        category = user_data['choice']
        print(category)


        old_value = r.get(md(category))
        print("Old value:{0}".format(old_value))

        if old_value is not None:
            new_value = int(old_value) + int(text)
            print("New value:{0}".format(new_value))
            r.set(md(category), new_value)
        else:
            r.set(md(category), 0)

        user_data[category] = text
        del user_data['choice']

        update.message.reply_text("Запомнил!" + u'\U0001F9E0' + "\n\nПоследние роднулины траты:\n"
                              "{}".format(facts_to_str()), reply_markup=markup)
    else:
        category = user_data['choice']
        user_data[category] ='0'
        del user_data['choice']
        update.message.reply_text("Надо денюжки вводить, а не белиберду!" + u'\U0001F62F', reply_markup=markup)
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
            CHOOSING: [RegexHandler('^(' + food_category + '|' + party_category + '|' + car_category + '|' + other_category + ')$',
                                    regular_choice,
                                    pass_user_data=True),
                       RegexHandler('^' + statistics_category  + '$',
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