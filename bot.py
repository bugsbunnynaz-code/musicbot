import os
import requests
import telebot
from flask import Flask, jsonify, request
from flask_cors import CORS

TOKEN = "8810770465:AAH7ywIfeivDOuVsQzMSf2Xuru7C24Mn6KM"
WEB_APP_URL = "https://music-box-player.vercel.app/"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)


@app.route('/search', methods=['GET'])
def api_search():
  query = request.args.get('q', '')
  if not query:
    return jsonify([])

  try:
    # Використовуємо стабільний відкритий екземпляр Invidious для миттєвого пошуку будь-яких виконавців
    res = requests.get(
        f'https://invidious.perennialte.ch/api/v1/search?q={requests.utils.quote(query)}&type=video',
        timeout=5,
    )
    if res.status_code != 200:
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
            'author': author or 'Виконавець',
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

    # Отримуємо пряме посилання на повний аудіопотік через відкритий шлюз Piped API
    res = requests.get(
        f'https://pipedapi.kavin.rocks/streams/{vid_id}', timeout=5
    )
    if res.status_code == 200:
      data = res.json()
      audio_streams = data.get('audioStreams', [])
      if audio_streams:
        # Вибираємо найкращу якість звуку
        audio_url = audio_streams[0].get('url')
        if audio_url:
          return jsonify({'audio_url': audio_url})

    # Запасний варіант через Invidious потоки
    res = requests.get(
        f'https://invidious.perennialte.ch/api/v1/videos/{vid_id}', timeout=5
    )
    if res.status_code == 200:
      data = res.json()
      adaptive_formats = data.get('adaptiveFormats', [])
      for fmt in adaptive_formats:
        if 'audio' in fmt.get('type', ''):
          return jsonify({'audio_url': fmt.get('url')})

    return jsonify({'error': 'Audio stream not found'}), 404
  except Exception as e:
    print(f'Помилка отримання потоку: {e}')
    return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)