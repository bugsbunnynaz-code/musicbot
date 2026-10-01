import os
import threading
import requests
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
    return jsonify([])

  try:
    # Використовуємо публічний та надійний Invidious/Cobalt/YouTube API для миттєвого пошуку без блокувань
    search_url = f"https://vid.puffyan.us/api/v1/search?q={requests.utils.quote(query)}&type=video"
    response = requests.get(search_url, timeout=5)
    
    if response.status_code != 200:
      return jsonify([])

    results = response.json()
    tracks = []

    for item in results[:15]:
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

  ydl_opts = {
      'format': 'bestaudio/best',
      'noplaylist': True,
      'quiet': True,
      'no_warnings': True,
      'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      audio_url = info.get('url')

      if not audio_url:
        formats = info.get('formats', [])
        for f in formats:
          if f.get('acodec') != 'none' and f.get('url'):
            audio_url = f.get('url')
            break

      return jsonify({'audio_url': audio_url})
  except Exception as e:
    print(f'Помилка отримання потоку: {e}')
    return jsonify({'error': str(e)}), 500


def run_bot():
  bot.infinity_polling()


if __name__ == '__main__':
  bot_thread = threading.Thread(target=run_bot)
  bot_thread.daemon = True
  bot_thread.start()
  app.run(host='0.0.0.0', port=5000)