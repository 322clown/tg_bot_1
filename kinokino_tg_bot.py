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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
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
# START_ROUTES, END_ROUTES = range(2)
# ONE, TWO, THREE, FOUR = range(4)


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     user = update.message.from_user
#     logger.info("User %s started the conversation.", user.first_name)
#     keyboard = [
#         [
#             InlineKeyboardButton("1", callback_data=str(ONE)),
#             InlineKeyboardButton("2", callback_data=str(TWO)),
#         ]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text("Start handler, Choose a route", reply_markup=reply_markup)
#     return START_ROUTES


# async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     query = update.callback_query
#     await query.answer()
#     keyboard = [
#         [
#             InlineKeyboardButton("1", callback_data=str(ONE)),
#             InlineKeyboardButton("2", callback_data=str(TWO)),
#         ]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text(text="Start handler, Choose a route", reply_markup=reply_markup)
#     return START_ROUTES
#
#
# async def one(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     query = update.callback_query
#     await query.answer()
#     keyboard = [
#         [
#             InlineKeyboardButton("3", callback_data=str(THREE)),
#             InlineKeyboardButton("4", callback_data=str(FOUR)),
#         ]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text(
#         text="First CallbackQueryHandler, Choose a route", reply_markup=reply_markup
#     )
#     return START_ROUTES
#
#
# async def two(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     query = update.callback_query
#     await query.answer()
#     keyboard = [
#         [
#             InlineKeyboardButton("1", callback_data=str(ONE)),
#             InlineKeyboardButton("3", callback_data=str(THREE)),
#         ]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text(
#         text="Second CallbackQueryHandler, Choose a route", reply_markup=reply_markup
#     )
#     return START_ROUTES
#
#
# async def three(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     query = update.callback_query
#     await query.answer()
#     keyboard = [
#         [
#             InlineKeyboardButton("Yes, let's do it again!", callback_data=str(ONE)),
#             InlineKeyboardButton("Nah, I've had enough ...", callback_data=str(TWO)),
#         ]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text(
#         text="Third CallbackQueryHandler. Do want to start over?", reply_markup=reply_markup
#     )
#     return END_ROUTES
#
#
# async def four(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     query = update.callback_query
#     await query.answer()
#     keyboard = [
#         [
#             InlineKeyboardButton("2", callback_data=str(TWO)),
#             InlineKeyboardButton("3", callback_data=str(THREE)),
#         ]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text(
#         text="Fourth CallbackQueryHandler, Choose a route", reply_markup=reply_markup
#     )
#     return START_ROUTES
#
#
# async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     query = update.callback_query
#     await query.answer()
#     await query.edit_message_text(text="See you next time!")
#     return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    try:
        requests.get(URL_KINOKINO)
    except requests.ConnectionError:
        await update.message.reply_text('Включи бота, лошара')
    json = {
        'username': f'{user.id}',
        'password': f'{user.id}',
    }
    response = requests.post(f'{URL_KINOKINO}{URL_START}',
                             json=json)
    if response.status_code == 418:
        await update.message.reply_text('🫖')
    if response.status_code == 201:
        await update.message.reply_text('Можно начинать (^˵◕ω◕˵^)')


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f'{user.id}')


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    pass


def main() -> None:
    application = Application.builder().token("5454514886:AAFL06SwdfSCkv_afMBIvT576G-sEE5_cvY").build()

    # conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler("start", start)],
    #     states={
    #         START_ROUTES: [
    #             CallbackQueryHandler(one, pattern="^" + str(ONE) + "$"),
    #             CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
    #             CallbackQueryHandler(three, pattern="^" + str(THREE) + "$"),
    #             CallbackQueryHandler(four, pattern="^" + str(FOUR) + "$"),
    #         ],
    #         END_ROUTES: [
    #             CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
    #             CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
    #         ],
    #     },
    #     fallbacks=[CommandHandler("start", start)],
    # )
    #
    # application.add_handler(conv_handler)

    application.add_handler(CommandHandler('my_id', my_id))

    application.add_handler(CommandHandler('my_profile', my_profile))

    application.add_handler(CommandHandler('start', start))

    application.run_polling()


if __name__ == "__main__":
    main()
