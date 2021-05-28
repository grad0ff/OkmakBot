import telebot

bot = telebot.TeleBot("1825854132:AAFn3pRQ7yhRemHc5cSsG_e3MohAyC9lQyA")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Салам-пополам! Кузе вара?")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.polling()
