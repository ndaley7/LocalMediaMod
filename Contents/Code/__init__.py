#local media assets agent
import os, string, hashlib, base64, re
from mp4file import atomsearch, mp4file
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.flac import Picture
from mutagen.oggvorbis import OggVorbis

artExt            = ['jpg','jpeg','png','tbn']
artFiles          = {'posters': ['poster','default','cover','movie','folder'],
                     'art':     ['fanart']}        
subtitleExt       = ['utf','utf8','utf-8','srt','smi','rt','ssa','aqt','jss','ass','idx','sub','txt', 'psb']
video_exts        = ['3gp', 'asf', 'asx', 'avc', 'avi', 'avs', 'bin', 'bivx', 'bup', 'divx', 'dv', 'dvr-ms', 'evo', 'fli', 'flv', 'ifo', 'img', 
                     'iso', 'm2t', 'm2ts', 'm2v', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'mts', 'nrg', 'nsv', 'nuv', 'ogm', 'ogv', 
                     'pva', 'qt', 'rm', 'rmvb', 'sdp', 'svq3', 'strm', 'ts', 'ty', 'vdr', 'viv', 'vob', 'vp3', 'wmv', 'wpl', 'xsp', 'xvid']
              
# A platform independent way to split paths which might come in with different separators.
def SplitPath(str):
  if str.find('\\') != -1:
    return str.split('\\')
  else: 
    return str.split('/')

class localMediaMovie(Agent.Movies):
  name = 'Local Media Assets (Movies)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.none']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))
    
  def update(self, metadata, media, lang):
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title
    
    filename = media.items[0].parts[0].file.decode('utf-8')   
    path = os.path.dirname(filename)
    if 'video_ts' == SplitPath(path.lower())[-1]:
      path = '/'.join(SplitPath(path)[:-1])
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    pathFiles = {}
    for p in os.listdir(path):
      pathFiles[p.lower()] = p
    # Add the filename as a base, and the dirname as a base for poster lookups
    passFiles = {}
    passFiles['posters'] = artFiles['posters'] + [fileroot, SplitPath(path)[-1]] 
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
                Log('Local asset (type: ' + t + ') added: ' + f)
              valid_posters.append(f)
            elif t == 'art':
              if f not in metadata.art:
                metadata.art[f] = Proxy.Media(data)
                Log('Local asset (type: ' + t + ') added: ' + f)
              valid_art.append(f)
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
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title
    
    # Look for subtitles for each episode.
    for s in media.seasons:
      # If we've got a date based season, ignore it for now, otherwise it'll collide with S/E folders/XML and PMS
      # prefers date-based (why?)
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
  contributes_to = ['com.plexapp.agents.discogs', 'com.plexapp.agents.lastfm', 'com.plexapp.agents.none']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', name=media.artist, score = 100))   
  def update(self, metadata, media, lang):
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title
    pass 

class localMediaAlbum(Agent.Album):
  name = 'Local Media Assets (Albums)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.discogs', 'com.plexapp.agents.lastfm', 'com.plexapp.agents.none']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))

  def update(self, metadata, media, lang):
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title
      
    valid_posters = []
    for t in media.tracks:
      for i in media.tracks[t].items:
        for p in i.parts:
          filename = p.file.decode('utf-8')
          path = os.path.dirname(filename)
          (fileroot, fext) = os.path.splitext(filename)
          pathFiles = {}
          for pth in os.listdir(path):
            pathFiles[pth.lower()] = pth
          # Add the filename as a base, and the dirname as a base for poster lookups
          passFiles = {}
          passFiles['posters'] = artFiles['posters'] + [fileroot, SplitPath(path)[-1]]
          # Look for posters
          for e in artExt:
            for a in passFiles['posters']:
              f = (a + '.' + e).lower()
              if f in pathFiles.keys():
                data = Core.storage.load(os.path.join(path, pathFiles[f]))
                posterName = hashlib.md5(data).hexdigest()
                if posterName not in metadata.posters:
                  metadata.posters[posterName] = Proxy.Media(data)
                  valid_posters.append(posterName)
                  Log('Local asset image added: ' + f + ', for file: ' + filename)
                else:
                  Log('skipping add for local art')
          # Look for embedded id3 APIC images in mp3 files
          if fext.lower() == '.mp3':
            try: f = ID3(filename)
            except: 
              Log('Bad ID3 tags. Skipping.')
              continue
            for frame in f.getall("APIC"):
              if (frame.mime == 'image/jpeg') or (frame.mime == 'image/jpg'): ext = 'jpg'
              elif frame.mime == 'image/png': ext = 'png'
              elif frame.mime == 'image/gif': ext = 'gif'
              else: ext = ''
              posterName = hashlib.md5(frame.data).hexdigest()
              if posterName not in metadata.posters:
                Log('Adding embedded APIC art from mp3 file: ' + filename)
                metadata.posters[posterName] = Proxy.Media(frame.data, ext=ext)
                valid_posters.append(posterName)
              else:
                Log('skipping already added APIC')
          # Look for coverart atoms in mp4/m4a
          elif fext.lower() in ['.mp4','.m4a','.m4p']:
            try: mp4fileTags = mp4file.Mp4File(filename)
            except: 
              Log('Bad mp4 tags. Skipping.')
              continue
            try:
              data = find_data(mp4fileTags, 'moov/udta/meta/ilst/coverart')
              posterName = hashlib.md5(data).hexdigest()
              if posterName not in metadata.posters:
                metadata.posters[posterName] = Proxy.Media(data)
                valid_posters.append(posterName)
                Log('Adding embedded coverart from m4a/mp4 file: ' + filename)
            except: pass
          # Look for coverart atoms in flac files
          elif fext.lower() == '.flac':
            try: f = FLAC(filename)
            except: 
              Log('Bad FLAC tags. Skipping.')
              continue
            for p in f.pictures:
              posterName = hashlib.md5(p.data).hexdigest()
              if posterName not in metadata.posters:
                Log('Adding embedded art from FLAC file: ' + filename)
                metadata.posters[posterName] = Proxy.Media(p.data)
                valid_posters.append(posterName)
              else:
                Log('skipping already added FLAC art')
          # Look for coverart atoms in ogg files
          elif fext.lower() == '.ogg':
            try:
              f = OggVorbis(filename)
              if f.has_key('metadata_block_picture'):
                for pic in f['metadata_block_picture']:
                  p = Picture(base64.standard_b64decode(pic))
                  if (p.mime == 'image/jpeg') or (p.mime == 'image/jpg'): ext = 'jpg'
                  elif p.mime == 'image/png': ext = 'png'
                  elif p.mime == 'image/gif': ext = 'gif'
                  else: ext = ''
                  posterName = hashlib.md5(p.data).hexdigest()
                  if posterName not in metadata.posters:
                    Log('Adding embedded art from FLAC file: ' + filename)
                    metadata.posters[posterName] = Proxy.Media(p.data, ext=ext)
                    valid_posters.append(posterName)
                  else:
                    Log('skipping already added ogg art')
            except: pass
    metadata.posters.validate_keys(valid_posters)

def cleanFilename(filename):
  #this will remove any whitespace and punctuation chars and replace them with spaces, strip and return as lowercase
  return string.translate(filename.encode('utf-8'), string.maketrans(string.punctuation + string.whitespace, ' ' * len (string.punctuation + string.whitespace))).strip().lower()

def FindSubtitles(part):
  globalSubtitleFolder = os.path.join(Core.app_support_path, 'Subtitles')
  pathsToCheck = [part.file.decode('utf-8')] # full pathname
  
  # filename only (no path)
  if os.path.exists(globalSubtitleFolder):
    pathsToCheck.append(os.path.join(globalSubtitleFolder, os.path.basename(pathsToCheck[0])))
  lang_sub_map = {}
  
  for filename in pathsToCheck:
    
    # See if we're in the global folder.
    if filename.count(globalSubtitleFolder) > 0: 
      globalFolder = True
    else: 
      globalFolder = False
      
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    fileroot = cleanFilename(fileroot)
    ext = ext.lower()
    
    # get the path, without filename
    path = os.path.dirname(filename)
    
    totalVidFiles = 0
    # Get all the files in the path.
    pathFiles = {}
    for p in os.listdir(path):
      (r, n) = os.path.splitext(p.decode('utf-8'))
      pathFiles[p] = cleanFilename(r) + n.lower()
      # Also, check to see if we have only one video filetype in this dir
      if n.lower()[1:] in video_exts:
        totalVidFiles += 1
    
    # If we have only one video file in the dir, then we will addAll the subs we find    
    if totalVidFiles == 1:
      addAll = True
    else:
      addAll = False  
      
    # Start with the existing languages.
    for lang in part.subtitles.keys():
      lang_sub_map[lang] = []
    
    for f in pathFiles.keys():
      if pathFiles[f].find('.') == -1:
        continue
        
      codec = None  
      (froot, fext) = pathFiles[f].split('.')
      
      # we are looking in the global subtitle folder, so the filenames need to match
      if globalFolder and froot != cleanFilename(fileroot): 
        continue

      if f[0] != '.' and fext in subtitleExt:

        # Is this an IDX file and we have a matching SUB file.
        if fext == 'idx' and (froot + '.sub') in pathFiles.values():

          # If it matches or we're adding everything.
          if addAll or fileroot == froot:
          
            idx = Core.storage.load(os.path.join(path,f))
            if idx.count('VobSub index file') > 0: #confirm this is a vobsub file
              langID = 0
              idxSplit = idx.split('\nid: ')
            
              languages = {}
              for i in idxSplit[1:]: #find all the languages indexed
                lang = i[:2]
                if not languages.has_key(lang):
                  languages[lang] = []
            
                Log('Found .idx subtitle file: ' + f + ' language: ' + lang + ' stream index: ' + str(langID))
                languages[lang].append(Proxy.LocalFile(os.path.join(path, f), index=str(langID)))
                langID+=1
              
                if not lang_sub_map.has_key(lang):
                  lang_sub_map[lang] = []
                lang_sub_map[lang].append(f)
              
              for lang,subs in languages.items():
                part.subtitles[lang][f] = subs
        else:
          
          # Remove the language from the filename for comparison purposes.
          langCheck = cleanFilename(froot).split(' ')[-1].strip()
          frootNoLang = froot[:-(len(langCheck))-1].strip()
          
          if addAll or ((fileroot == froot) or (fileroot == frootNoLang)):
            if fext == 'txt' or fext == 'sub': #check to make sure this is a sub file
              try:
                txtLines = [l.strip() for l in Core.storage.load(os.path.join(path,f)).splitlines(True)]
                if re.match('^\{[0-9]+\}\{[0-9]*\}', txtLines[1]):
                  pass #codec = 'microdvd'
                elif re.match('^[0-9]{1,2}:[0-9]{2}:[0-9]{2}[:=,]', txtLines[1]):
                  pass #codec = 'txt'
                elif '[SUBTITLE]' in txtLines:
                  pass #codec = 'subviewer'
                else:
                  continue
              except:
                continue
            
            if codec is None and fext in ('ass', 'ssa', 'smi', 'srt', 'psb'):
              codec = fext.replace('ass', 'ssa')
                
            Log('Found subtitle file: ' + f + ' language: ' + langCheck + ' codec: ' + str(codec))
            lang = Locale.Language.Match(langCheck)
            part.subtitles[lang][f] = Proxy.LocalFile(os.path.join(path, f), codec=codec)
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