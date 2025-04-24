# run_webhook.py
import os
from flask import Flask, request
import telebot

# беремо токен і URL із змінних оточення
BOT_TOKEN  = os.environ['BOT_TOKEN']
BASE_URL   = os.environ['BASE_URL']  # наприклад: https://my-app.up.railway.app
WEBHOOK_URL = f"{BASE_URL}/{BOT_TOKEN}"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# підключаємо стандартний код бота з lookup_bot_multi, але без polling()
# наприклад:
import lookup_bot_multi  # має просто реєструвати хендлери, не робити bot.polling()

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update   = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

if __name__ == '__main__':
    # при старті чистимо старий вебхук і ставимо новий
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    # запускаємо Flask на порті, який дає Railway
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')))
