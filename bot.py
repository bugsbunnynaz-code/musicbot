import os
import telebot
import yt_dlp
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

  ydl_opts = {
      'format': 'bestaudio/best',
      'noplaylist': True,
      'extract_flat': True,
      'skip_download': True,
      'quiet': True,
      'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
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
    print(f'Помилка пошуку yt-dlp: {e}')
    return jsonify([])

  return jsonify(tracks)


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
      'extractor_args': {'youtube': {'player_client': ['android']}},
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      audio_url = info.get('url')

      if not audio_url:
        formats = info.get('formats', [])
        for f in formats:
          if f.get('url') and f.get('acodec') != 'none':
            audio_url = f.get('url')
            break

      if audio_url:
        return jsonify({'audio_url': audio_url})
      else:
        return jsonify({'error': 'Audio stream not found'}), 404
  except Exception as e:
    print(f'Помилка отримання потоку: {e}')
    return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)