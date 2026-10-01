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
    # Використовуємо відкрите API Jamendo для повних треків (без 30-секундних обмежень)
    url = f"https://api.jamendo.com/v3.0/tracks/?client_id=59395f9d&format=json&limit=15&search={requests.utils.quote(query)}"
    res = requests.get(url, timeout=5)
    
    if res.status_code != 200:
      return jsonify([])

    data = res.json().get('results', [])
    tracks = []
    for item in data:
      title = item.get('name')
      artist = item.get('artist_name', 'Невідомий виконавець')
      audio_url = item.get('audio')  # Повний трек

      if title and audio_url:
        tracks.append({
            'title': title,
            'author': artist,
            'url': audio_url,
        })
    return jsonify(tracks)
  except Exception as e:
    print(f'Помилка пошуку Jamendo: {e}')
    return jsonify([])


@app.route('/play', methods=['GET'])
def api_play():
  audio_url = request.args.get('url', '')
  if not audio_url:
    return jsonify({'error': 'No URL provided'}), 400

  return jsonify({'audio_url': audio_url})


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)