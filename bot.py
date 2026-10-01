import os
import threading
import telebot
import yt_dlp
from flask import Flask, jsonify, request, redirect
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
      'extractor_args': {'youtube': {'player_client': ['android']}},
  }

  tracks = []
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(f'ytsearch10:{query}', download=False)
      entries = info.get('entries', [])

      for entry in entries:
        if entry:
          vid_id = entry.get('id')
          title = entry.get('title', 'Без назви')
          author = (
              entry.get('uploader')
              or entry.get('channel')
              or entry.get('artist')
              or 'YouTube'
          )

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

  try:
    # Витягуємо чистий ID відео з посилання YouTube
    if 'v=' in video_url:
      vid_id = video_url.split('v=')[1].split('&')[0]
    else:
      vid_id = video_url.split('/')[-1]

    # Використовуємо стабільний стрімінговий бекенд, який гарантовано відтворює будь-яке відео як аудіо
    stream_url = f'https://pipedapi.kavin.rocks/streams/{vid_id}'
    import requests
    res = requests.get(stream_url, timeout=5).json()
    
    audio_streams = res.get('audioStreams', [])
    if audio_streams:
      # Беремо найкращий доступний прямий аудіопотік
      direct_url = audio_streams[0].get('url')
      if direct_url:
        return jsonify({'audio_url': direct_url})

    return jsonify({'error': 'Stream not found'}), 404
  except Exception as e:
    print(f'Помилка отримання потоку: {e}')
    return jsonify({'error': str(e)}), 500


def run_bot():
  bot.infinity_polling()


if __name__ == '__main__':
  bot_thread = threading.Thread(target=run_bot)
  bot_thread.daemon = True
  bot_thread.start()
  
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)