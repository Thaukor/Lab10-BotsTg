from telegram.ext import Updater, CommandHandler, MessageHandler, PollHandler, Filters
from telegram import Poll
import requests
import re

qa = [
    ["P1", ['R1', 'R2', 'R3']],
    ["P2", ['R1', 'R2', 'R3']],
    ["P3", ['R1', 'R2', 'R3']],
]

# extract chat_id based on the incoming object
def get_chat_id(update, context):
    chat_id = -1

    if update.message is not None:
        chat_id = update.message.chat.id
    elif update.callback_query is not None:
        chat_id = update.callback_query.message.chat.id
    elif update.poll is not None:
        chat_id = context.bot_data[update.poll.id]

    return chat_id

def help_command_handler(update, context):
    msg = """Type /start to start the quiz. Type /help to display this screen"""
    context.bot.send_message(
        chat_id = get_chat_id(update, context),
        text = msg
    )
    pass

def poll_handler(update, context):

    question = update.poll.question
    correct_answer = update.poll.correct_option_id

    option_1_text = update.poll.options[0].text
    option_1_vote = update.poll.options[0].voter_count

def get_answer(update):
    answers = update.poll.options

    ret = ""

    for answer in answers:
        if answer.voter_count == 1:
            ret = answer.text
            break
    
    return ret

def poll_command_handler(update, context):
    c_id = get_chat_id(update, context)
    q = 'Test answer, correct ans is 1'
    a = ['A1', 'A2', 'A3']

    msg = context.bot.send_poll(chat_id = c_id, question = q, option=a, type = Poll.QUIZ, correct_option_id=0)

def main_handler(update, context):
    pass

def main():
    updater = Updater('2126498441:AAHqMe4CFQyhGX5bLw1LtywLG_LQ1I9pnFw', use_context=True)

    dp = updater.dispatcher

    # command handlers
    dp.add_handler(CommandHandler("help", help_command_handler))
    dp.add_handler(CommandHandler("start", poll_command_handler))
    # message handler
    dp.add_handler(MessageHandler(Filters.text, main_handler))
    # quiz handler
    dp.add_handler(PollHandler(poll_handler, pass_chat_data=True, pass_user_data=True))
    # start
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
