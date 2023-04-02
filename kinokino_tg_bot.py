import logging

import requests

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup,\
    ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


URL_KINOKINO = 'http://192.168.0.150:9200/'
URL_USER = 'v1/user/'
URL_START = 'v1/start/'
URL_SEARCH_FILM = 'v1/search_film/'
URL_ADD_MOVIE = 'v1/add_movie_api/'

# START_ROUTES, END_ROUTES = range(2)
# ONE, TWO, THREE, FOUR = range(4)
SEARCH, SEARCHING, SEARCH_SELECT = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    try:
        requests.get(URL_KINOKINO)
    except requests.ConnectionError:
        await update.message.reply_text('Включи сервер, лошара')
    json = {
        'username': f'{user.id}',
        'password': f'{user.id}',
    }
    response = requests.post(f'{URL_KINOKINO}{URL_START}',
                             json=json)
    if response.status_code == 200:
        await update.message.reply_text('🫖')
    if response.status_code == 201:
        await update.message.reply_text('Можно начинать (^˵◕ω◕˵^)')


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f'{user.id}')


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    await update.message.reply_text("Введите название... или если передумали /skip")
    return SEARCHING


async def searching(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    params = {'name': update.message.text}
    searching_result = requests.get(f'{URL_KINOKINO}{URL_SEARCH_FILM}', params).json()
    context.bot_data['search_request'] = searching_result
    result_message = 'Выберите номер фильма, который хотите добавить... или выберите skip, если не хотите добавлять\n'

    reply_keyboard = []
    line = []
    for i in range(1, len(searching_result) + 1):
        line.append(f'{i}')
        if len(line) == 3:
            reply_keyboard.append(line)
            line = []
    reply_keyboard.append(line)
    reply_keyboard.append(['/skip'])

    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    for i, movie in enumerate(searching_result):
        try:
            movie_years = movie['releaseYears']
            if movie_years:
                movie_years = movie_years[0]
                result_message += f"{i + 1}) {movie['name']} ({movie_years['start']}-{movie_years['end']})\n"
        except KeyError:
            result_message += f"{i+1}) {movie['name']} ({movie['year']})\n"

    await update.message.reply_text(result_message, reply_markup=markup)

    return SEARCH_SELECT


async def search_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    user = update.message.from_user

    search_result = context.bot_data['search_request']

    selected = search_result[int(update.message.text) - 1]
    logger.info(selected)
    params = {
        'username': user.id,
        'id': selected['id'],
        'type': selected['type'],
        'name': selected['name'],
        'year': selected['year'],
    }
    try:
        if selected['poster']['previewUrl']:
            params['preview_url'] = selected['poster']['previewUrl']
    except KeyError:
        params['preview_url'] = ''
    try:
        if selected['releaseYears']:
            params['release_years_start'] = selected['releaseYears'][0]['start']
            params['release_years_end'] = selected['releaseYears'][0]['end']
    except KeyError:
        params['release_years_start'] = ''
        params['release_years_end'] = ''

    logger.info(f'AEA1 - {params}')

    response = requests.post(
        f'{URL_KINOKINO}{URL_ADD_MOVIE}',
        params=params,
        timeout=20,
    )

    await update.message.reply_text(f'{response.status_code}',
                                    reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    await update.message.reply_text('😢', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token("5454514886:AAFL06SwdfSCkv_afMBIvT576G-sEE5_cvY").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={

            SEARCHING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, searching),
                CommandHandler('skip', skip)
            ],

            SEARCH_SELECT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_select),
                CommandHandler('skip', skip)
            ],

        },
        fallbacks=[CommandHandler("skip", skip)],
    )

    application.add_handler(conv_handler)

    application.add_handler(CommandHandler('my_id', my_id))

    application.add_handler(CommandHandler('start', start))

    application.run_polling()


if __name__ == "__main__":
    main()

# kinokino_tg_bot.py
