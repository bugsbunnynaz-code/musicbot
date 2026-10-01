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
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      audio_url = info.get('url')
      if not audio_url:
        # Шукаємо у форматах, якщо прямий url відсутній
        formats = info.get('formats', [])
        for f in formats:
          if f.get('acodec') != 'none' and f.get('url'):
            audio_url = f.get('url')
            break

      return jsonify({'audio_url': audio_url})
  except Exception as e:
    print(f'Помилка отримання потоку: {e}')
    return jsonify({'error': str(e)}), 500