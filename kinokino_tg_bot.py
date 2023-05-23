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
URL_PROFILE_STAT = 'v1/profile_statistics/'
URL_MOVIES = 'v1/user_movies/'
URL_INFO_MOVIES = 'v1/movie_info/'


SEARCHING = range(1)
MOVIES = range(1)


PLANNED_TO_WATCH = 'Запланировано'
WATCHING = 'Смотрю'
COMPLETED = 'Просмотрено'


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


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите название... или если передумали /skip")
    return SEARCHING


async def searching(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_text = update.message.text
    params = {'name': search_text}
    searching_result = requests.get(f'{URL_KINOKINO}{URL_SEARCH_FILM}', params).json()
    result_message = 'Выберит фильм, который хотите добавить...\n'

    reply_keyboard = []

    for i, movie in enumerate(searching_result):
        try:
            movie_years = movie['releaseYears']
            if movie_years:
                movie_years = movie_years[0]
                reply_keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"{movie['name']} ({movie_years['start']}-{movie_years['end']})",
                            callback_data=f'search__{search_text}__{i}'
                        )
                    ]
                )
        except KeyError:
            reply_keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{movie['name']} ({movie['year']})",
                        callback_data=f'search__{search_text}__{i}'
                    )
                ]
            )
    markup = InlineKeyboardMarkup(reply_keyboard)

    await update.message.reply_text(result_message, reply_markup=markup)

    return ConversationHandler.END


async def searching_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    searching_text = query.data
    if searching_text.startswith('search__'):
        searching_text_split = searching_text.split('__')
        found_name = searching_text_split[1]
        found_id = searching_text_split[2]
        params = {
            'number': found_id,
            'name': found_name,
            'username': query.from_user.id,
        }
        response = requests.post(
            url=f"{URL_KINOKINO}{URL_ADD_MOVIE}",
            params=params
        )
        await query.answer()
        if response.status_code == 200:
            await query.message.reply_text(f"Есть в списках")
        if response.status_code == 201:
            await query.message.reply_text(f"Добавлено")


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    await update.message.reply_text('😢', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    response = requests.post(
        url=f"{URL_KINOKINO}{URL_PROFILE_STAT}",
        params={'username': user.id}
    )
    if response.status_code == 200:
        response_json = response.json()
        result_message = f"Статистика.\n" \
                         f"Всего: {response_json['all_count']}\n" \
                         f"Запланировано: {response_json['planned_count']}\n" \
                         f"Смотрю: {response_json['watching_count']}\n" \
                         f"Просмотрено: {response_json['completed_count']}\n"
        await update.message.reply_text(result_message)
    else:
        await update.message.reply_text('error')


async def my_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user

    keyboard = [
        [
            InlineKeyboardButton('Все', callback_data="all__"),
            InlineKeyboardButton('Запланировано', callback_data="planned__"),
            InlineKeyboardButton('Смотрю', callback_data="watching__"),
            InlineKeyboardButton('Просмотрено', callback_data="completed__"),
            InlineKeyboardButton('Избранное', callback_data="favorite__"),
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите:',
                                    reply_markup=markup)

    return MOVIES


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return MOVIES


def util_movie(response: dict):
    result_message = ''
    for i, film_info in enumerate(response['films']):
        film_name = film_info['name']
        film_year = film_info['year']
        film_year_start = film_info['year_start']
        film_year_end = film_info['year_end']
        if film_year_start:
            result_message += f'{i+1}){film_name} ({film_year_start}-{film_year_end})\n'
        else:
            result_message += f'{i+1}){film_name} ({film_year})\n'
    return result_message


async def planned_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton('Все', callback_data="all__"),
            InlineKeyboardButton('Смотрю', callback_data="watching__"),
            InlineKeyboardButton('Просмотрено', callback_data="completed__"),
            InlineKeyboardButton('Избранное', callback_data="favorite__"),
        ]
    ]
    response = requests.post(
        url=f"{URL_KINOKINO}{URL_MOVIES}",
        params={
            'username': query.from_user.id,
            'field_name': PLANNED_TO_WATCH,
        },
    ).json()
    result_message = util_movie(response)
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'В планах:\n{result_message}', reply_markup=markup)
    return MOVIES


async def watching_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton('Все', callback_data="all__"),
            InlineKeyboardButton('Запланировано', callback_data="planned__"),
            InlineKeyboardButton('Просмотрено', callback_data="completed__"),
            InlineKeyboardButton('Избранное', callback_data="favorite__"),
        ]
    ]
    response = requests.post(
        url=f"{URL_KINOKINO}{URL_MOVIES}",
        params={
            'username': query.from_user.id,
            'field_name': WATCHING,
        },
    ).json()
    result_message = util_movie(response)
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'Смотрю:\n{result_message}', reply_markup=markup)
    return MOVIES


async def completed_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton('Все', callback_data="all__"),
            InlineKeyboardButton('Запланировано', callback_data="planned__"),
            InlineKeyboardButton('Смотрю', callback_data="watching__"),
            InlineKeyboardButton('Избранное', callback_data="favorite__"),
        ]
    ]
    response = requests.post(
        url=f"{URL_KINOKINO}{URL_MOVIES}",
        params={
            'username': query.from_user.id,
            'field_name': COMPLETED,
        },
    ).json()
    result_message = util_movie(response)
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'Просмотренные:\n{result_message}', reply_markup=markup)
    return MOVIES


async def all_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    keyboard = []
    buttons = [
            InlineKeyboardButton('Запланировано', callback_data="planned__"),
            InlineKeyboardButton('Смотрю', callback_data="watching__"),
            InlineKeyboardButton('Просмотрено', callback_data="completed__"),
            InlineKeyboardButton('Избранное', callback_data="favorite__"),
        ]
    response = requests.post(
        url=f"{URL_KINOKINO}{URL_MOVIES}",
        params={
            'username': query.from_user.id,
            'field_name': 'None',
        },
    ).json()
    for i, movie in enumerate(response['films']):
        callback_data = f"info__{movie['id']}"
        keyboard.append([InlineKeyboardButton(f"{i}) {movie['name']}", callback_data=callback_data)])
    keyboard.append(buttons)
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'Все:\n', reply_markup=markup)
    return MOVIES


async def favorite_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    keyboard = []
    buttons = [
            InlineKeyboardButton('Все', callback_data="all__"),
            InlineKeyboardButton('Запланировано', callback_data="planned__"),
            InlineKeyboardButton('Смотрю', callback_data="watching__"),
            InlineKeyboardButton('Просмотрено', callback_data="completed__"),
        ]
    response = requests.post(
        url=f"{URL_KINOKINO}{URL_MOVIES}",
        params={
            'username': query.from_user.id,
            'field_name': 'favorite',
        },
    ).json()
    for i, movie in enumerate(response['films']):
        callback_data = f"info__{movie['id']}"
        keyboard.append([InlineKeyboardButton(f"{i}) {movie['name']}", callback_data=callback_data)])
    keyboard.append(buttons)
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'Избранное:\n', reply_markup=markup)
    return MOVIES


async def movie_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    data_split = query.data.split('__')
    movie_id = data_split[1]
    response = requests.post(
        url=f"{URL_KINOKINO}{URL_INFO_MOVIES}",
        params={
            'username': f'{query.from_user.id}',
            'movie_id': f'{movie_id}',
        },
    ).json()
    buttons = [
        InlineKeyboardButton('Все', callback_data="all__"),
        InlineKeyboardButton('Запланировано', callback_data="planned__"),
        InlineKeyboardButton('Смотрю', callback_data="watching__"),
        InlineKeyboardButton('Просмотрено', callback_data="completed__"),
    ]
    keyboard = [buttons]
    if response['favorite']:
        keyboard.append([InlineKeyboardButton('Удалить из избранного', callback_data=f"add__rem__{movie_id}")])
    else:
        keyboard.append([InlineKeyboardButton('Добавить в избранное', callback_data=f"add__add__{movie_id}")])
    markup = InlineKeyboardMarkup(keyboard)
    result_message = f"Название: {response['name']}\n" \
                     f"Год: {response['year']}\n" \
                     f"Сезонов: {response['seasons_count']}\n" \
                     f"Серий: {response['episodes_count']}\n" \
                     f"Превью: {response['preview_url']}\n"
    await query.answer()
    await query.edit_message_text(result_message, reply_markup=markup)
    return MOVIES


async def add_to_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    data_split = query.data.split('__')
    movie_id = data_split[1]
    response = requests.post(
        url=f"{URL_KINOKINO}{URL_INFO_MOVIES}",
        params={
            'username': f'{query.from_user.id}',
            'movie_id': f'{movie_id}',
        },
    ).json()
    buttons = [
        InlineKeyboardButton('Все', callback_data="all__"),
        InlineKeyboardButton('Запланировано', callback_data="planned__"),
        InlineKeyboardButton('Смотрю', callback_data="watching__"),
        InlineKeyboardButton('Просмотрено', callback_data="completed__"),
    ]
    keyboard = [buttons]
    if response['favorite']:
        keyboard.append([InlineKeyboardButton('Удалить из избранного', callback_data=f"add__rem__{movie_id}")])
    else:
        keyboard.append([InlineKeyboardButton('Добавить в избранное', callback_data=f"add__add__{movie_id}")])
    markup = InlineKeyboardMarkup(keyboard)
    result_message = f"Название: {response['name']}\n" \
                     f"Год: {response['year']}\n" \
                     f"Сезонов: {response['seasons_count']}\n" \
                     f"Серий: {response['episodes_count']}\n" \
                     f"Превью: {response['preview_url']}\n"
    await query.answer()
    await query.edit_message_text(result_message, reply_markup=markup)
    return MOVIES


def main() -> None:
    application = Application.builder().token("5454514886:AAFL06SwdfSCkv_afMBIvT576G-sEE5_cvY").build()

    search_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={

            SEARCHING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, searching),
                CommandHandler('skip', skip),
            ],

        },
        fallbacks=[CommandHandler("skip", skip)],
    )

    movies_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("my_movies", my_movies)],
        states={

            MOVIES: [
                CallbackQueryHandler(all_movies, pattern="^all__$"),
                CallbackQueryHandler(planned_movies, pattern="^planned__$"),
                CallbackQueryHandler(watching_movies, pattern="^watching__$"),
                CallbackQueryHandler(completed_movies, pattern="^completed__$"),
                CallbackQueryHandler(favorite_movies, pattern="^favorite__$"),
                CallbackQueryHandler(movie_info, pattern="^info__"),
                CallbackQueryHandler(add_to_favorite, pattern="^add__"),

            ],

        },
        fallbacks=[
            CommandHandler("my_movies", my_movies),
        ],

    )

    application.add_handler(search_conv_handler)

    application.add_handler(movies_conv_handler)

    application.add_handler(CallbackQueryHandler(searching_select))

    application.add_handler(CommandHandler('start', start))

    application.add_handler(CommandHandler('statistics', statistics))

    application.run_polling()


if __name__ == "__main__":
    main()

# python kinokino_tg_bot.py
