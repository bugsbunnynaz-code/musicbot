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
    # Використовуємо офіційне відкрите API Deezer для пошуку музики
    res = requests.get(
        f'https://api.deezer.com/search?q={requests.utils.quote(query)}',
        timeout=5,
    )
    if res.status_code != 200:
      return jsonify([])

    data = res.json().get('data', [])
    tracks = []
    for item in data[:15]:
      title = item.get('title')
      artist = item.get('artist', {}).get('name', 'Невідомий виконавець')
      preview_url = item.get('preview')  # Пряме посилання на трек

      if title and preview_url:
        tracks.append({
            'title': title,
            'author': artist,
            'url': preview_url,
        })
    return jsonify(tracks)
  except Exception as e:
    print(f'Помилка пошуку Deezer: {e}')
    return jsonify([])


@app.route('/play', methods=['GET'])
def api_play():
  # Оскільки Deezer одразу віддає готове посилання на аудіо при пошуку, просто повертаємо його
  audio_url = request.args.get('url', '')
  if not audio_url:
    return jsonify({'error': 'No URL provided'}), 400

  return jsonify({'audio_url': audio_url})


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)