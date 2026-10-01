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
    # Використовуємо прямий пошук по музичній базі з повними треками
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    # Робимо запит до пошукового каталогу дзеркал z3.fm / muzofon
    search_url = f'https://muzofond.pro/search/{requests.utils.quote(query)}'
    res = requests.get(search_url, headers=headers, timeout=6)

    tracks = []
    if res.status_code == 200:
      from html.parser import HTMLParser

      # Простий і надійний парсер без сторонніх бібліотек, щоб витягнути треки і посилання
      class MusicParser(HTMLParser):

        def __init__(self):
          super().__init__()
          self.in_item = False
          self.current_title = ""
          self.current_artist = ""
          self.current_url = ""
          self.tracks = []
          self.capture_text = None

        def handle_starttag(self, tag, attrs):
          attrs_dict = dict(attrs)
          # Шукаємо блоки треків та прямі посилання на mp3 або сторінки завантаження
          if tag == 'div' and 'item' in attrs_dict.get('class', ''):
            self.in_item = True
            self.current_title = ""
            self.current_artist = ""
            self.current_url = ""
          if self.in_item:
            if tag == 'a':
              href = attrs_dict.get('href', '')
              if '.mp3' in href or 'download' in href:
                self.current_url = href
            if tag == 'span' or tag == 'div':
              cls = attrs_dict.get('class', '')
              if 'title' in cls or 'name' in cls:
                self.capture_text = 'title'
              elif 'artist' in cls or 'author' in cls:
                self.capture_text = 'artist'

        def handle_data(self, data):
          if self.in_item and self.capture_text == 'title':
            self.current_title += data.strip()
          elif self.in_item and self.capture_text == 'artist':
            self.current_artist += data.strip()

        def handle_endtag(self, tag):
          if tag == 'span' or tag == 'div':
            self.capture_text = None
          if tag == 'div' and self.in_item:
            if self.current_title and self.current_url:
              if not self.current_url.startswith('http'):
                self.current_url = f'https://muzofond.pro{self.current_url}'
              self.tracks.append({
                  'title': self.current_title,
                  'author': self.current_artist or 'Виконавець',
                  'url': self.current_url,
              })
            self.in_item = False

      parser = MusicParser()
      parser.feed(res.text)
      tracks = parser.tracks[:15]

    # Запасний варіант, якщо структура верстки змінилася, щоб гравець не був порожнім
    if not tracks:
      fallback_url = f'https://itunes.apple.com/search?term={requests.utils.quote(query)}&media=music&entity=song&limit=15'
      fb_res = requests.get(fallback_url, timeout=5)
      if fb_res.status_code == 200:
        for item in fb_res.json().get('results', []):
          t = item.get('trackName')
          a = item.get('artistName', 'Виконавець')
          u = item.get('previewUrl')
          if t and u:
            tracks.append({'title': t, 'author': a, 'url': u})

    return jsonify(tracks)
  except Exception as e:
    print(f'Помилка пошуку: {e}')
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