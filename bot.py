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
    return jsonify([])

  ydl_opts = {
      'format': 'bestaudio/best',
      'noplaylist': True,
      'extract_flat': True,
      'skip_download': True,
      'quiet': True,
  }

  tracks = []
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(f'ytsearch15:{query}', download=False)
      entries = info.get('entries', [])

      for entry in entries:
        if entry:
          vid_id = entry.get('id')
          title = entry.get('title', 'Без назви')
          author = entry.get('uploader') or entry.get('channel') or 'YouTube'

          if vid_id:
            tracks.append({
                'title': title,
                'author': author,
                'url': f'https://www.youtube.com/watch?v={vid_id}',
            })
  except Exception as e:
    print(f'Помилка пошуку: {e}')
    return jsonify([])

  return jsonify(tracks)


@app.route('/play', methods=['GET'])
def api_play():
  video_url = request.args.get('url', '')
  if not video_url:
    return jsonify({'error': 'No URL provided'}), 400

  # Використовуємо надійні параметри для обходу захисту YouTube на хмарі
  ydl_opts = {
      'format': 'bestaudio',
      'noplaylist': True,
      'quiet': True,
      'no_warnings': True,
      'extractor_args': {'youtube': {'player_client': ['android']}},
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      audio_url = info.get('url')

      if not audio_url:
        formats = info.get('formats', [])
        for f in formats:
          if f.get('url'):
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