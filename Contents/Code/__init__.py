#local media assets agent
import os, string
from mp4file import atomsearch, mp4file

artExt            = ['jpg','jpeg','png','tbn']
artFiles          = {'posters': ['poster','default','cover','movie','folder'],
                     'art':     ['fanart']}        
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','ssa','aqt','jss','ass','idx']

class localMediaMovie(Agent.Movies):
  name = 'Local Media Assets (Movies)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.none']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))
    
  def update(self, metadata, media, lang):

    filename = media.items[0].parts[0].file.decode('utf-8')
    
    path = os.path.dirname(filename)
    if 'video_ts' == path.lower().split('/')[-1]:
      path = '/'.join(path.split('/')[:-1])
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    pathFiles = {}
    for p in os.listdir(path):
      pathFiles[p.lower()] = p

    # Add the filename as a base, and the dirname as a base for poster lookups
    passFiles = {}
    passFiles['posters'] = artFiles['posters'] + [fileroot, path.split('/')[-1]] 
    passFiles['art'] = artFiles['art'] + [fileroot + '-fanart'] 

    # Look for posters and art
    valid_art = []
    valid_posters = []
    
    for t in ['posters','art']:
      for e in artExt:
        for a in passFiles[t]:
          f = (a + '.' + e).lower()
          if f in pathFiles.keys():
            data = Core.storage.load(os.path.join(path, pathFiles[f]))
            if t == 'posters':
              if f not in metadata.posters:
                metadata.posters[f] = Proxy.Media(data)
                valid_posters.append(f)
                Log('Local asset (type: ' + t + ') added: ' + f)
            elif t == 'art':
              if f not in metadata.art:
                metadata.art[f] = Proxy.Media(data)
                valid_art.append(f)
                Log('Local asset (type: ' + t + ') added: ' + f)
    
    metadata.posters.validate_keys(valid_posters)
    metadata.art.validate_keys(valid_art)
    
    # Look for subtitles
    for i in media.items:
      for part in i.parts:
        FindSubtitles(part)
     
    getMetadataAtoms(part, metadata, type='Movie')

class localMediaTV(Agent.TV_Shows):
  name = 'Local Media Assets (TV)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb', 'com.plexapp.agents.none']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))

  def update(self, metadata, media, lang):
    # Look for subtitles for each episode.
    for s in media.seasons:
      # If we've got a date based season, ignore it for now, otherwise it'll collide with S/E folders/XML and PMS
      # prefers date-based (why?)
      #
      if int(s) < 1900:
        for e in media.seasons[s].episodes:
          for i in media.seasons[s].episodes[e].items:
            for part in i.parts:
              FindSubtitles(part)
              getMetadataAtoms(part, metadata, type='TV', episode=metadata.seasons[s].episodes[e])
      else:
        # Whack it in case we wrote it.
        del metadata.seasons[s]

class localMediaArtist(Agent.Artist):
  name = 'Local Media Assets (Artists)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.lastfm', 'com.plexapp.agents.none']

  def search(self, results, media, lang):
    pass

  def update(self, metadata, media, lang):
    pass

class localMediaAlbum(Agent.Album):
  name = 'Local Media Assets (Albums)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.lastfm', 'com.plexapp.agents.none']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))

  def update(self, metadata, media, lang):
    print metadata

            
def cleanFilename(filename):
  #this will remove any whitespace and punctuation chars and replace them with spaces, strip and return as lowercase
  return string.translate(filename.encode('utf-8'), string.maketrans(string.punctuation + string.whitespace, ' ' * len (string.punctuation + string.whitespace))).strip().lower()

def FindSubtitles(part):
  filename = part.file.decode('utf-8') #full pathname
  basename = os.path.basename(filename) #filename only (no path)
  (fileroot, ext) = os.path.splitext(basename)
  fileroot = cleanFilename(fileroot) 
  ext = ext.lower()
  path = os.path.dirname(filename) #get the path, without filename

  # Get all the files in the path.
  pathFiles = {}
  for p in os.listdir(path):
    pathFiles[p] = p

  # Start with the existing languages.
  lang_sub_map = {}
  for lang in part.subtitles.keys():
    lang_sub_map[lang] = []

  addAll = False
  for f in pathFiles:
    (froot, fext) = os.path.splitext(f)
    froot = cleanFilename(froot)

    if f[0] != '.' and fext[1:].lower() in subtitleExt:
      langCheck = cleanFilename(froot).split(' ')[-1].strip()

      # Remove the language from the filename for comparison purposes.
      frootNoLang = froot[:-(len(langCheck))-1]

      if addAll or ((fileroot == froot) or (fileroot == frootNoLang)):
        Log('Found subtitle file: ' + f + ' language: ' + langCheck)
        lang = Locale.Language.Match(langCheck)
        part.subtitles[lang][f] = Proxy.LocalFile(os.path.join(path, pathFiles[f]))
        
        if not lang_sub_map.has_key(lang):
          lang_sub_map[lang] = []
        lang_sub_map[lang].append(f)
  
  # Now whack subtitles that don't exist anymore.
  for lang in lang_sub_map.keys():
    part.subtitles[lang].validate_keys(lang_sub_map[lang])
  
def getMetadataAtoms(part, metadata, type, episode=None):
  filename = part.file.decode('utf-8')
  file = os.path.basename(filename)
  
  (file, ext) = os.path.splitext(file)
  if ext.lower() in ['.mp4', '.m4v', '.mov']:
    mp4fileTags = mp4file.Mp4File(filename)
    
    try: metadata.posters['atom_coverart'] = Proxy.Media(find_data(mp4fileTags, 'moov/udta/meta/ilst/coverart'))
    except: pass
    try:
      title = find_data(mp4fileTags, 'moov/udta/meta/ilst/title') #Name
      if type == 'Movie': metadata.title = title
      else: episode.title = title
    except:
      pass
      
    try:
      try:
        summary = find_data(mp4fileTags, 'moov/udta/meta/ilst/ldes') #long description
      except:
        summary = find_data(mp4fileTags, 'moov/udta/meta/ilst/desc') #short description
        
      if type == 'Movie': metadata.summary = summary
      else: episode.summary = summary
    except:
      pass

    if type == 'Movie':
      try: 
        genres = find_data(mp4fileTags, 'moov/udta/meta/ilst/genre') #genre
        if len(genres) > 0:
          genList = genres.split(',')
          metadata.genres.clear()
          for g in genList:
            metadata.genres.add(g.strip())
      except: 
        pass
      try: 
        artists = find_data(mp4fileTags, 'moov/udta/meta/ilst/artist') #artist
        if len(artists) > 0:
          artList = artists.split(',')
          metadata.roles.clear()
          for a in artList:
            role = metadata.roles.new()
            role.actor = a.strip()
      except: 
        pass
      try:
        releaseDate = find_data(mp4fileTags, 'moov/udta/meta/ilst/year')
        releaseDate = releaseDate.split('T')[0]
        parsedDate = Datetime.ParseDate(releaseDate)
        
        metadata.year = parsedDate.year
        metadata.originally_available_at = parsedDate.date() #release date
      except: 
        pass
     
def find_data(atom, name):
  child = atomsearch.find_path(atom, name)
  data_atom = child.find('data')
  if data_atom and 'data' in data_atom.attrs:
    return data_atom.attrs['data']