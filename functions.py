def bot_send_message(*args, **args2):
    try:
        a = bot.send_message(*args, **args2)
        return a
    except Exception as error:
        print(error)


