#local media assets agent
import os, string, hashlib, base64, re, plistlib
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.flac import Picture
from mutagen.oggvorbis import OggVorbis

imageExt          = ['jpg', 'png', 'jpeg', 'tbn']
audioExt          = ['mp3']
artExt            = ['jpg','jpeg','png','tbn']
artFiles          = {'posters': ['poster','default','cover','movie','folder'],
                     'art':     ['fanart','art','background']}        
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
  #persist_stored_files = False
  contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.none']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))
    
  def update(self, metadata, media, lang):
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title

    filename = media.items[0].parts[0].file.decode('utf-8')   
    path = os.path.dirname(filename)
    
    # Look for media.
    try: FindMediaForItem(metadata, [path], 'movie', media.items[0].parts[0])
    except: raise #Log('Error finding media for movie %s', media.title)

    # Look for subtitles
    for i in media.items:
      for part in i.parts:
        FindSubtitles(part)
    getMetadataAtoms(part, metadata, type='Movie')

def FindUniqueSubdirs(dirs):
  final_dirs = {}
  for dir in dirs:
    final_dirs[dir] = True
    try: 
      parent = os.path.split(dir)[0]
      final_dirs[parent] = True
      try: final_dirs[os.path.split(parent)[0]] = True
      except: pass
    except: pass
    
  if final_dirs.has_key(''):
    del final_dirs['']
  return final_dirs

class localMediaTV(Agent.TV_Shows):
  name = 'Local Media Assets (TV)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  #persist_stored_files = False
  contributes_to = ['com.plexapp.agents.thetvdb', 'com.plexapp.agents.none']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))
  def update(self, metadata, media, lang):
    # Set title if needed.
    if media and metadata.title is None: metadata.title = media.title

    # Look for media, collect directories.
    dirs = {}
    for s in media.seasons:
      Log('Creating season %s', s)
      metadata.seasons[s].index = int(s)
      for e in media.seasons[s].episodes:
        
        # Make sure metadata exists, and find sidecar media.
        episodeMetadata = metadata.seasons[s].episodes[e]
        episodeMedia = media.seasons[s].episodes[e].items[0]
        dir = os.path.dirname(episodeMedia.parts[0].file.decode('utf-8'))
        dirs[dir] = True
        
        try: FindMediaForItem(episodeMetadata, [dir], 'episode', episodeMedia.parts[0])
        except: raise
        
    # Figure out the directories we should be looking in.
    try: dirs = FindUniqueSubdirs(dirs)
    except: dirs = []
    
    # Look for show images.
    Log("Looking for show media for %s.", metadata.title)
    try: FindMediaForItem(metadata, dirs, 'show')
    except: Log("Error finding show media.")
    
    # Look for season images.
    for s in metadata.seasons:
      Log('Looking for season media for %s season %s.', metadata.title, s)
      try: FindMediaForItem(metadata.seasons[s], dirs, 'season')
      except: Log("Error finding season media for season %s" % s)
        
    # Look for subtitles for each episode.
    for s in media.seasons:
      # If we've got a date based season, ignore it for now, otherwise it'll collide with S/E folders/XML and PMS
      # prefers date-based (why?)
      if int(s) < 1900:
        for e in media.seasons[s].episodes:
          for i in media.seasons[s].episodes[e].items:
            # Look for subtitles.
            for part in i.parts:
              FindSubtitles(part)
              getMetadataAtoms(part, metadata, type='TV', episode=metadata.seasons[s].episodes[e])
      else:
        # Whack it in case we wrote it.
        #del metadata.seasons[s]
        pass

class localMediaArtist(Agent.Artist):
  name = 'Local Media Assets (Artists)'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  #persist_stored_files = False
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
  #persist_stored_files = False
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
                valid_posters.append(posterName)
                if posterName not in metadata.posters:
                  metadata.posters[posterName] = Proxy.Media(data)
                  Log('Local asset image added: ' + f + ', for file: ' + filename)
                else:
                  Log('skipping add for local art')
          # Look for embedded id3 APIC images in mp3 files
          if fext.lower() == '.mp3':
            try: f = ID3(filename)
            except: 
              Log('Bad ID3 tags. Skipping.')
              continue
            #available_at date from TDRC  
            try:
              metadata.originally_available_at = Datetime.ParseDate('01-01-' + f.getall("TDRC")[0].text[0].get_text()).date()
            except:
              pass
            #Genres from TCON
            try:
              genres = f.getall('TCON')
              metadata.genres.clear()
              for g in genres:
                metadata.genres.add(g)
            except: 
              pass            
            for frame in f.getall("APIC"):
              if (frame.mime == 'image/jpeg') or (frame.mime == 'image/jpg'): ext = 'jpg'
              elif frame.mime == 'image/png': ext = 'png'
              elif frame.mime == 'image/gif': ext = 'gif'
              else: ext = ''
              posterName = hashlib.md5(frame.data).hexdigest()
              valid_posters.append(posterName)
              if posterName not in metadata.posters:
                Log('Adding embedded APIC art from mp3 file: ' + filename)
                metadata.posters[posterName] = Proxy.Media(frame.data, ext=ext)
              else:
                Log('skipping already added APIC')
          # Look for coverart atoms in mp4/m4a
          elif fext.lower() in ['.mp4','.m4a','.m4p']:
            try: mp4fileTags = MP4(filename)
            except: 
              Log('Bad mp4 tags. Skipping.')
              continue
            try:
              data = str(mp4fileTags["covr"][0])
              posterName = hashlib.md5(data).hexdigest()
              valid_posters.append(posterName)
              if posterName not in metadata.posters:
                metadata.posters[posterName] = Proxy.Media(data)
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
              valid_posters.append(posterName)
              if posterName not in metadata.posters:
                Log('Adding embedded art from FLAC file: ' + filename)
                metadata.posters[posterName] = Proxy.Media(p.data)
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
                  valid_posters.append(posterName)
                  if posterName not in metadata.posters:
                    Log('Adding embedded art from FLAC file: ' + filename)
                    metadata.posters[posterName] = Proxy.Media(p.data, ext=ext)
                  else:
                    Log('skipping already added ogg art')
            except: pass
    metadata.posters.validate_keys(valid_posters)

def cleanFilename(filename):
  #this will remove any whitespace and punctuation chars and replace them with spaces, strip and return as lowercase
  return string.translate(filename.encode('utf-8'), string.maketrans(string.punctuation + string.whitespace, ' ' * len (string.punctuation + string.whitespace))).strip().lower()

def GetFileRoot(part):
  if part:
    filename = part.file.decode('utf-8')
    path = os.path.dirname(filename)
    if 'video_ts' == SplitPath(path.lower())[-1]:
      path = '/'.join(SplitPath(path)[:-1])
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    return fileroot
  return None

def FindMediaForItem(metadata, paths, type, part = None):
  fileroot = GetFileRoot(part)
  
  # Get files in directories.
  path_files = {}
  total_media_files = 0
  for path in paths:
    for p in os.listdir(path):
      if os.path.isfile(os.path.join(path, p)):
        path_files[p.lower()] = os.path.join(path, p)
      (r, n) = os.path.splitext(p.decode('utf-8'))
      if n.lower()[1:] in video_exts:
        total_media_files += 1
      
  Log('Looking for %s media (%s) in %d paths (fileroot: %s) with %d media files.', type, metadata.title, len(paths), fileroot, total_media_files)
  Log('Paths: %s', str(paths))
    
  # Figure out what regexs to use.
  search_tuples = []
  if type == 'season':
    search_tuples += [['season-?%s[-a-z]?' % metadata.index, metadata.posters, imageExt, False]]
    search_tuples += [['season-?%s-banner[-a-z]?' % metadata.index, metadata.banners, imageExt, False]]
  elif type == 'show':
    search_tuples += [['(show|poster)-?[0-9]?', metadata.posters, imageExt, False]]
    search_tuples += [['banner-?[0-9]?', metadata.banners, imageExt, False]]
    search_tuples += [['(fanart|art|background)-?[0-9]?', metadata.art, imageExt, False]]
    search_tuples += [['theme-?[0-9]?', metadata.themes, audioExt, False]]
  elif type == 'episode':
    search_tuples += [[fileroot + '-?[0-9]?', metadata.thumbs, imageExt, False]]
  elif type == 'movie':
    search_tuples += [['(poster|default|cover|movie|folder|' + fileroot + ')-?[0-9]?', metadata.posters, imageExt, True]]
    search_tuples += [['(fanart|art|background|' + fileroot + '-fanart' + ')-?[0-9]?', metadata.art, imageExt, True]]

  for (pattern, media_list, extensions, limited) in search_tuples:
    valid_things = []
    
    for p in path_files:
      for ext in extensions:
        if re.match('%s.%s' % (pattern, ext), p, re.IGNORECASE):

          # Use a pattern if it's unlimited, or if there's only one media file.
          if (limited and total_media_files == 1) or (not limited) or (p.find(fileroot.lower()) == 0):

            # Read data and hash it.
            data = Core.storage.load(path_files[p])
            media_hash = hashlib.md5(data).hexdigest()
      
            # See if we need to add it.
            valid_things.append(media_hash)
            if media_hash not in media_list:
              media_list[media_hash] = Proxy.Media(data)
              Log('  Local asset added: %s (%s)', path_files[p], media_hash)
          else:
            Log('Skipping file %s because there are %d media files.', p, total_media_files)
              
    Log('Found %d valid things for pattern %s (ext: %s)', len(valid_things), pattern, str(extensions))
    media_list.validate_keys(valid_things)

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
    tags = MP4(filename)
    
    if type == 'Movie':
      item = metadata
    elif type == 'TV':
      item = episode
    
    #Coverart
    try: 
      item.posters['atom_coverart'] = Proxy.Media(str(tags["covr"][0]))
    except: pass
    
    #Title from name atom
    try:
      title = tags["\xa9nam"][0]
      item.title = title
    except: pass
    
    #Summary from long/short decription atom
    try:
      try:
        summary = tags["ldes"][0]
      except:
        summary = tags["desc"][0]
      item.summary = summary
    except: pass

    #Genres from genre atom
    try:
      genres = tags["\xa9gen"][0]
      if len(genres) > 0:
        genList = genres.split('/')
        metadata.genres.clear()
        for g in genList:
          metadata.genres.add(g.strip())
    except: pass 
     
    #Roles from Artist atom
    try: 
      artists = tags["\xa9ART"][0]
      if len(artists) > 0:
        artList = artists.split(',')
        item.roles.clear()
        for a in artList:
          role = item.roles.new()
          role.actor = a.strip()
    except: pass
    
    #Release date from year atom
    try:
      releaseDate = tags["\xa9day"][0]
      releaseDate = releaseDate.split('T')[0]
      parsedDate = Datetime.ParseDate(releaseDate)
      item.originally_available_at = parsedDate.date()
      item.year = parsedDate.year
    except: pass
      
    #Directors from the iTunMOVI-directors atom
    try:
      pl = plistlib.readPlistFromString(str(tags["----:com.apple.iTunes:iTunMOVI"][0]))
      directors = pl["directors"][0]["name"]
      if len(directors) > 0:
        dirList = directors.split("/")
        item.directors.clear()
        for d in dirList:
          item.directors.add(d.strip())
    except: pass
    
    #Writers from the iTunMOVI-screenwriters atom
    try:
      pl = plistlib.readPlistFromString(str(tags["----:com.apple.iTunes:iTunMOVI"][0]))
      writers = pl["screenwriters"][0]["name"]
      if len(directors) > 0:
        wriList = writers.split("/")
        item.writers.clear()
        for w in wriList:
          item.writers.add(w.strip())
    except: pass
    
    #Content rating from iTunEXTC atom
    try:
      rating = tags["----:com.apple.iTunes:iTunEXTC"][0].split('|')[1]
      if len(rating) > 0:
        episode.content_rating = rating
    except: pass
    
    #Studio from copyright atom
    try:
      copyright = tags["cprt"][0]
      if len(copyright) > 0:
        item.studio = copyright
    except: pass
    
    #Collection from album atom
    try:
      album = tags["\xa9alb"][0]
      if len(album) > 0:
        albumList = album.split('/')
        item.collections.clear()
        for a in albumList:
          item.collections.add(a.strip())
    except: pass