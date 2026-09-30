@app.route('/search', methods=['GET'])
def api_search():
  query = request.args.get('q', '')
  if not query:
    return jsonify([])

  ydl_opts = {
      'format': 'bestaudio/best',
      'noplaylist': True,
      'default_search': 'ytsearch10',
      'extract_flat': True,  # Швидкий пошук без завантаження зайвого
  }

  tracks = []
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(query, download=False)
      entries = info.get('entries', [info])

      for entry in entries:
        if entry:
          vid_id = entry.get('id')
          tracks.append({
              'title': entry.get('title', 'Без назви'),
              'author': entry.get('uploader', 'YouTube'),
              'url': (
                  f'https://www.youtube.com/watch?v={vid_id}'
                  if vid_id
                  else entry.get('url')
              ),
          })
  except Exception as e:
    print(f'Помилка пошуку: {e}')

  return jsonify(tracks)


@app.route('/play', methods=['GET'])
def api_play():
  video_url = request.args.get('url', '')
  if not video_url:
    return jsonify({'error': 'No URL provided'}), 400

  ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True}

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      audio_url = info.get('url')  # Пряме посилання на аудіопотік
      return jsonify({'audio_url': audio_url})
  except Exception as e:
    print(f'Помилка отримання потоку: {e}')
    return jsonify({'error': str(e)}), 500