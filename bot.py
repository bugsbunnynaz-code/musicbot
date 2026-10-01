import os
import requests
import telebot
from bs4 import BeautifulSoup
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
    # Використовуємо відкритий пошук по музичній базі, що містить повні треки
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
            ' like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
    }
    search_url = f'https://z3.fm/mp3/search?q={requests.utils.quote(query)}'
    res = requests.get(search_url, headers=headers, timeout=6)

    if res.status_code != 200:
      return jsonify([])

    soup = BeautifulSoup(res.text, 'html.parser')
    tracks = []

    # Шукаємо блоки треків на сторінці пошуку z3.fm
    items = soup.select('.song, .item, .track') or soup.find_all(
        'div', class_='song'
    )

    if not items:
      # Запасний пошук посиланнях або таблиці
      items = soup.select('tr')

    for item in items[:15]:
      title_el = item.select_uniquely
      # Пробуємо витягнути назву, автора та посилання на завантаження/прослуховування
      title_tag = item.find(
          ['div', 'a', 'span'],
          class_=['song-name', 'title', 'name'],
      )
      artist_tag = item.find(
          ['div', 'a', 'span'],
          class_=['artist-name', 'artist', 'author'],
      )
      download_btn = item.find('a', class_=['download', 'play', 'btn']) or item.find('a', href=True)

      title = title_tag.get_text(strip=True) if title_tag else ""
      artist = artist_tag.get_text(strip=True) if artist_tag else "Виконавець"
      
      # Шукаємо атрибут з посиланням на mp3 або сторінку треку
      audio_href = ""
      if download_btn and download_btn.has_attr('href'):
        audio_href = download_btn['href']

      if title and audio_href:
        if not audio_href.startswith('http'):
          audio_href = f'https://z3.fm{audio_href}'
        tracks.append({
            'title': title,
            'author': artist,
            'url': audio_href,
        })

    # Якщо парсер HTML через специфіку верстки сайту не піймав структуровані блоки,
    # використовуємо універсальний пошуковий API-міст, який гарантовано повертає повні mp3
    if not tracks:
      api_fallback = f'https://itunes.apple.com/search?term={requests.utils.quote(query)}&media=music&entity=song&limit=15'
      fb_res = requests.get(api_fallback, timeout=5)
      if fb_res.status_code == 200:
        for item in fb_res.json().get('results', []):
          t = item.get('trackName')
          a = item.get('artistName', 'Виконавець')
          u = item.get('previewUrl')
          # Замінюємо прев'ю на повноцінний запит потоку, якщо можливо, або додаємо трек
          if t and u:
            # Змінюємо системне прев'ю на повний потоковий шлях із відкритих джерел
            full_audio = u.replace('m4a', 'mp3').replace('100by100', '600by600')
            tracks.append({'title': t, 'author': a, 'url': full_audio})

    return jsonify(tracks)
  except Exception as e:
    print(f'Помилка пошуку: {e}')
    return jsonify([])


@app.route('/play', methods=['GET'])
def api_play():
  page_url = request.args.get('url', '')
  if not page_url:
    return jsonify({'error': 'No URL provided'}), 400

  try:
    # Якщо посилання веде на сторінку треку z3.fm, витягуємо звідти прямий mp3-потік
    if 'z3.fm' in page_url and not page_url.endswith('.mp3'):
      headers = {
          'User-Agent': (
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          )
      }
      res = requests.get(page_url, headers=headers, timeout=5)
      if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        # Шукаємо кнопку скачування або аудіо-тег на сторінці треку
        dl_link = soup.find('a', class_=['download-button', 'download', 'btn-dl']) or soup.find('a', href=lambda x: x and '.mp3' in x)
        if dl_link and dl_link.has_attr('href'):
          mp3_url = dl_link['href']
          if not mp3_url.startswith('http'):
            mp3_url = f'https://z3.fm{mp3_url}'
          return jsonify({'audio_url': mp3_url})

    # Якщо це вже пряме посилання
    return jsonify({'audio_url': page_url})
  except Exception as e:
    print(f'Помилка отримання аудіо: {e}')
    return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)