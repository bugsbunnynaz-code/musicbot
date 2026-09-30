import os
import threading
import telebot
import yt_dlp
from flask import Flask, jsonify, request
from flask_cors import CORS

TOKEN = "8810770465:AAH7ywIfeivDOuVsQzMSf2Xuru7C24Mn6KM"
WEB_APP_URL = "https://music-box-player.vercel.app/"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)


@bot.message_handler(commands=['start'])
def send_welcome(message):
  markup = telebot.types.InlineKeyboardMarkup()
  web_app = telebot.types.WebAppInfo(url=WEB_APP_URL)
  markup.add(
      telebot.types.InlineKeyboardButton(text="🎧 Відкрити плеєр", web_app=web_app)
  )

  bot.send_message(
      message.chat.id,
      "Привіт! 🎵 Це твій повноцінний музичний бот.\n\n"
      "Натисни кнопку нижче, щоб відкрити плеєр і слухати повні треки!",
      reply_markup=markup,
  )


@app.route('/search', methods=['GET'])
def api_search():
  query = request.args.get('q', '')
  if not query:
    return jsonify({'tracks': []})

  ydl_opts = {
      'format': 'bestaudio/best',
      'noplaylist': True,
      'default_search': 'ytsearch5',
  }

  tracks = []
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(query, download=False)
      entries = info.get('entries', [info])

      for entry in entries:
        if entry:
          tracks.append({
              'title': entry.get('title', 'Без назви'),
              'artist': entry.get('uploader', 'YouTube'),
              'url': entry.get('url'),  # Пряме посилання на повний аудіопотік
          })
  except Exception as e:
    print(f'Помилка пошуку: {e}')

  return jsonify({'tracks': tracks})


# Запуск бота у фоновому потоці всередині хмари
def run_bot():
  bot.infinity_polling()


if __name__ == '__main__':
  bot_thread = threading.Thread(target=run_bot)
  bot_thread.daemon = True
  bot_thread.start()
  # Для локального запуск (якщо захочеш перевірити на ПК)
  app.run(host='0.0.0.0', port=5000)