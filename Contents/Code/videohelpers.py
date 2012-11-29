import os
import helpers

from mutagen.mp4 import MP4

class VideoHelper(object):
  def __init__(self, filename):
    self.filename = filename

def VideoHelpers(filename):
  filename = helpers.unicodize(filename)
  file = os.path.basename(filename)
  (file, ext) = os.path.splitext(file)

  for cls in [ MP4VideoHelper ]:
    if cls.is_helper_for(ext):
      return cls(filename)
  return None

#####################################################################################################################

class MP4VideoHelper(VideoHelper):
  @classmethod
  def is_helper_for(cls, file_extension):
    return file_extension.lower() in ['.mp4', '.m4v', '.mov']

  def process_metadata(self, metadata, episode = None):

    if episode == None:
      item = metadata
    else:
      item = episode

    Log('Reading MP4 tags')
    try: tags = MP4(self.filename)
    except: 
      Log('An error occurred while attempting to parse the MP4 file')

    # Coverart
    try: 
      picture = Proxy.Media(str(tags["covr"][0]))

      # If we're dealing with an actual episode, it uses thumbs rather than posters.
      if episode != None:
        item.thumbs['atom_coverart'] = picture
      else:
        item.posters['atom_coverart'] = picture
    except: raise

    # Title
    try:
      title = tags["\xa9nam"][0]
      item.title = title
    except: pass

    # Summary (long or short)
    try:
      try:
        summary = tags["ldes"][0]
      except:
        summary = tags["desc"][0]
      item.summary = summary
    except: pass

    # Genres
    try:
      genres = tags["\xa9gen"][0]
      if len(genres) > 0:
        genre_list = genres.split('/')
        metadata.genres.clear()
        for genre in genre_list:
          metadata.genres.add(genre.strip())
    except: pass

    # Roles
    try: 
      artists = tags["\xa9ART"][0]
      if len(artists) > 0:
        artist_list = artists.split(',')
        item.roles.clear()
        for artist in artist_list:
          role = item.roles.new()
          role.actor = artist.strip()
    except: pass

    # Release Date & Year
    try:
      releaseDate = tags["\xa9day"][0]
      releaseDate = releaseDate.split('T')[0]
      parsedDate = Datetime.ParseDate(releaseDate)
      item.originally_available_at = parsedDate.date()
      item.year = parsedDate.year
    except: pass

    # Directors
    try:
      pl = plistlib.readPlistFromString(str(tags["----:com.apple.iTunes:iTunMOVI"][0]))
      directors = pl["directors"][0]["name"]
      if len(directors) > 0:
        director_list = directors.split("/")
        item.directors.clear()
        for director in director_list:
          item.directors.add(director.strip())
    except: pass

    # Writers
    try:
      pl = plistlib.readPlistFromString(str(tags["----:com.apple.iTunes:iTunMOVI"][0]))
      writers = pl["screenwriters"][0]["name"]
      if len(directors) > 0:
        writer_list = writers.split("/")
        item.writers.clear()
        for writer in writer_list:
          item.writers.add(writer.strip())
    except: pass

    # Content Rating
    try:
      rating = tags["----:com.apple.iTunes:iTunEXTC"][0].split('|')[1]
      if len(rating) > 0:
        episode.content_rating = rating
    except: pass

    # Studio
    try:
      copyright = tags["cprt"][0]
      if len(copyright) > 0:
        item.studio = copyright
    except: pass

    # Collection
    try:
      albums = tags["\xa9alb"][0]
      if len(albums) > 0:
        album_list = albums.split('/')
        item.collections.clear()
        for album in album_list:
          item.collections.add(album.strip())
    except: pass