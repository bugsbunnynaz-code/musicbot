
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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://z3.fm/',
    }

    search_url = f'https://z3.fm/mp3/search?keywords={requests.utils.quote(query)}'
    res = requests.get(search_url, headers=headers, timeout=6)

    tracks = []
    if res.status_code == 200:
      from html.parser import HTMLParser

      class Z3Parser(HTMLParser):
        def __init__(self):
          super().__init__()
          self.in_song = False
          self.current_title = ""
          self.current_artist = ""
          self.current_url = ""
          self.tracks = []
          self.capture = None

        def handle_starttag(self, tag, attrs):
          attrs_dict = dict(attrs)
          if tag == 'div' and 'song' in attrs_dict.get('class', ''):
            self.in_song = True
            self.current_title = ""
            self.current_artist = ""
            self.current_url = ""
          
          if self.in_song:
            if tag == 'a' and 'download' in attrs_dict.get('class', ''):
              self.current_url = attrs_dict.get('href', '')
            elif tag == 'span':
              cls = attrs_dict.get('class', '')
              if 'name' in cls or 'song-name' in cls:
                self.capture = 'title'
              elif 'artist' in cls or 'author' in cls:
                self.capture = 'artist'

        def handle_data(self, data):
          if self.in_song:
            if self.capture == 'title':
              self.current_title += data.strip()
            elif self.capture == 'artist':
              self.current_artist += data.strip()

        def handle_endtag(self, tag):
          if tag == 'span':
            self.capture = None
          if tag == 'div' and self.in_song:
            if self.current_title and self.current_url:
              if not self.current_url.startswith('http'):
                self.current_url = f'https://z3.fm{self.current_url}'
              self.tracks.append({
                  'title': self.current_title,
                  'author': self.current_artist or 'Виконавець',  # Виправлено тут
                  'url': self.current_url,
              })
            self.in_song = False

      parser = Z3Parser()
      parser.feed(res.text)
      tracks = parser.tracks[:15]

    return jsonify(tracks)
  except Exception as e:
    print(f'Помилка пошуку z3: {e}')
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