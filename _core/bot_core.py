from Core_.events import handle_message, handle_callbacks


def setup(dp):

    dp.message.register(handle_message)
    dp.callback_query.register(handle_callbacks)
