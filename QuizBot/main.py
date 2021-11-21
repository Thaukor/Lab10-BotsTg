from os import truncate
from telegram.ext import Updater, CommandHandler, MessageHandler, PollHandler, Filters
from telegram import Poll
import requests, random
import re

qa = [
    ["¿Cuál comando descarga los cambios del repositorio remoto y realiza un merge en el repo. local?", ['Clone', 'Fetch', 'Pull'], 2],
    ["¿Qué comando añade todos los archivos nuevos/modificados y realiza un commit al mismo tiempo?", ['git commit add *', 'git commit -a', 'Ninguno'], 2],
    ["¿Cuál opción permite modificar el último commit?", ['git commit --amend', 'git commit --fixup', 'No es posible'], 0],
    ["¿Qué resultado tiene el siguiente commando? git add * && git commit --amend -m \"Olvidé colocar los archivos jaja\"", 
        [
            'Añade todo, modifica commit antiguo, sobreescribe mensaje',
            'Añade todo, modifica commit antiguo, añade mensaje al antiguo',
            'Añade todo, crea nuevo commit basado en el anterior, combina mensaje del commit antiguo y el nuevo'
        ], 0
    ],
    ["¿En cuál hook es posible modificar el mensaje de un commit?", ['pre-commit', 'post-commit', 'commit-msg'], 2],
    ["¿En cuál de los siguientes hooks es posible abortar un commit?", ['post-commit', 'update', 'pre-commit'], 2],
    ["¿Cuál comando permite forzar un push sin sobreescribir commits de otras personas?", 
        [
            'git push --force-overwrite-self', 'git push --force --no-overwrite', 'git push --force-with-lease'
        ], 2
    ],
    ["¿En qué caso es seguro un conflicto al realizar un merge de dos ramas?", 
        [
            'Siempre que modifiquen el mismo archivo',
            'Cuando la rama contiene commits detrás y adelante de la rama a la cual se realiza el merge'
            'Cuando se modifican las mismas lineas de un archivo'
        ]
    ]
]

# Multiple correct answers
poll_qa = [
    ["¿Cuáles de los siguientes Github Actions puede cerrar un issue?", ['close', 'bugfix', 'resolved'], [0, 2]],
    ["¿Cuál comando añade todos los archivos nuevos/modificados para un commit?", ['git add *', 'git add .', 'git add -A'], [0, 2]],
    ["¿Cómo se puede ignorar una regla de .gitignore?", 
        [
            'Añadiendo un ! frente al archivo/directorio que se quiere incluir en .gitignore',
            'git add -f <archivo>',
            'No es posible sin eliminar la regla de .gitignore' 
        ], [0, 1]
    ],
    ["¿Cómo se puede añadir todos los cambios y archivos de una carpeta?", 
        [
            'git add <carpeta>/',
            'git add --dir <carpeta>',
            'git add <carpeta>/*'
        ], [0, 2]
    ]
]

current_poll_correct = []

total_quiz_qa = 4
total_poll_qa = 2
grade = 1
# A random sample from qa, asked questions will be removed from here.
tq_qa = []
tp_qa = []

is_polling = False

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
    msg = """/start inicia el quiz.
    /help muestra esta pantalla"""
    context.bot.send_message(
        chat_id = get_chat_id(update, context),
        text = msg
    )

def poll_handler(update, context):
    """
    question = update.poll.question
    correct_answer = update.poll.correct_option_id

    options = update.poll.options
    option_1_vote = update.poll.options[0].voter_count
    """

    global grade
    q_type = update.poll.type
    context.bot.send_message(
        chat_id = get_chat_id(update, context),
        text = 'Revisando respuesta...'
    )

    ans = get_answer(update)

    if q_type == 'quiz':
        is_correct = is_quizz_answer_correct(ans, update)
    else:
        is_correct = is_poll_answer_correct(ans, update)
    if is_correct:
        msg = 'Felicidades!'
        grade += 1
    else:
        msg = 'oof'

    context.bot.send_message(
        chat_id = get_chat_id(update, context),
        text = msg
    )

    next_poll(update, context)


def is_poll_answer_correct(ans, update):
    answers = update.poll.options

    for id in current_poll_correct:
        if ans == answers[id].text:
            return True
    
    return False

def is_quizz_answer_correct(ans, update):
    answers = update.poll.options

    if ans == answers[update.poll.correct_option_id].text:
        return True

    return False

def get_answer(update):
    answers = update.poll.options

    ret = ""

    for answer in answers:
        if answer.voter_count == 1:
            ret = answer.text
            break
    
    return ret

def poll_command_handler(update, context):
    global tp_qa
    global tq_qa

    if not is_polling:
        tq_qa = random.sample(qa, 4)
        tp_qa = random.sample(poll_qa, 2)

        next_poll(update, context)
    else:
        context.bot.send_message(
            chat_id = get_chat_id(update, context),
            text = 'Ya hay un Quiz en proceso.'
        )
def next_poll(update, context):
    global total_quiz_qa
    global total_poll_qa
    global grade
    global is_polling

    if total_quiz_qa > 0:
        add_quiz_question(update, context)
        total_quiz_qa -= 1
    elif total_poll_qa > 0:
        add_poll_question(update, context)
        total_poll_qa -= 1
    else:
        # Reset questions, show grade
        total_poll_qa = 2
        total_quiz_qa = 4

        context.bot.send_message(
            chat_id = get_chat_id(update, context),
            text = '¡Terminaste de responder! Tu puntuación final fue de ' + str(grade)
        )

        grade = 1
        is_polling = False
        return False

    is_polling = True
    return True

def add_quiz_question(update, context):
    global tq_qa
    c_id = get_chat_id(update, context)

    _qa = random.choice(tq_qa)
    tq_qa.remove(_qa)

    q = _qa[0]
    a = _qa[1]
    ca = _qa[2]

    msg = context.bot.send_poll(chat_id = c_id, question = q, options=a, type = Poll.QUIZ, correct_option_id=ca)
    context.bot_data.update({msg.poll.id: msg.chat.id})

def add_poll_question(update, context):
    global current_poll_correct
    global tp_qa

    c_id = get_chat_id(update, context)

    _qa = random.choice(tp_qa)
    tp_qa.remove(_qa)

    q = _qa[0]
    a = _qa[1]
    current_poll_correct = _qa[2]

    msg = context.bot.send_poll(chat_id = c_id, question = q, options=a, type = Poll.REGULAR)
    context.bot_data.update({msg.poll.id: msg.chat.id})

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
