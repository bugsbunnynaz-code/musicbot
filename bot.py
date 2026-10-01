@app.route('/search', methods=['GET'])
def api_search():
  query = request.args.get('q', '')
  if not query:
    return jsonify([])

  ydl_opts = {
      'format': 'bestaudio/best',
      'noplaylist': True,
      'default_search': 'ytsearch10',
      'extract_flat': True,
      'skip_download': True,
  }

  tracks = []
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(query, download=False)
      entries = info.get('entries', [])
      if not entries and 'title' in info:
        entries = [info]

      for entry in entries:
        if entry:
          vid_id = entry.get('id') or entry.get('url')
          title = entry.get('title', 'Без назви')
          author = entry.get('uploader') or entry.get('channel') or 'YouTube'
          
          if vid_id:
            # Якщо це просто ID, формуємо посилання
            if not str(vid_id).startswith('http'):
              watch_url = f'https://www.youtube.com/watch?v={vid_id}'
            else:
              watch_url = vid_id

            tracks.append({
                'title': title,
                'author': author,
                'url': watch_url,
            })
  except Exception as e:
    print(f'Помилка пошуку: {e}')
    return jsonify([])

  return jsonify(tracks)