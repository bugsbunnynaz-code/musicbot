import os
import threading
import requests
import telebot
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
    return jsonify([])

  try:
    # Використовуємо публічний екземпляр Invidious API для миттєвого пошуку
    res = requests.get(
        f'https://vid.puffyan.us/api/v1/search?q={requests.utils.quote(query)}&type=video',
        timeout=5,
    )
    if res.status_code != 200:
      return jsonify([])

    items = res.json()
    tracks = []
    for item in items[:15]:
      vid_id = item.get('videoId')
      title = item.get('title')
      author = item.get('author')
      if vid_id and title:
        tracks.append({
            'title': title,
            'author': author or 'YouTube',
            'url': f'https://www.youtube.com/watch?v={vid_id}',
        })
    return jsonify(tracks)
  except Exception as e:
    print(f'Помилка пошуку: {e}')
    return jsonify([])


@app.route('/play', methods=['GET'])
def api_play():
  video_url = request.args.get('url', '')
  if not video_url:
    return jsonify({'error': 'No URL provided'}), 400

  try:
    if 'v=' in video_url:
      vid_id = video_url.split('v=')[1].split('&')[0]
    else:
      vid_id = video_url.split('/')[-1]

    # Запитуємо прямий аудіопотік через надійний публічний інстанс
    res = requests.get(
        f'https://invidious.perennialte.ch/api/v1/videos/{vid_id}', timeout=5
    )
    if res.status_code != 200:
      # Запасний варіант інстансу
      res = requests.get(
          f'https://vid.puffyan.us/api/v1/videos/{vid_id}', timeout=5
      )

    data = res.json()
    adaptive_formats = data.get('adaptiveFormats', [])

    audio_url = None
    for fmt in adaptive_formats:
      if 'audio' in fmt.get('type', ''):
        audio_url = fmt.get('url')
        break

    if audio_url:
      return jsonify({'audio_url': audio_url})
    else:
      return jsonify({'error': 'Audio stream not found'}), 404
  except Exception as e:
    print(f'Помилка отримання потоку: {e}')
    return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
  bot_thread = threading.Thread(
      target=lambda: bot.infinity_polling(none_stop=True)
  )
  bot_thread.daemon = True
  bot_thread.start()

  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)