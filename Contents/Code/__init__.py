#local media assets agent
import os, string

artExt            = ['jpg','jpeg','png','tbn']
artFiles          = {'posters': ['poster','default','cover','movie','folder'],
                     'art':     ['fanart']}
            
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','txt','ssa','aqt','jss','ass','idx']

def FindSubtitles(part):
  filename = part.file.decode('utf-8')
  basename = os.path.basename(filename.lower())
  (fileroot, ext) = os.path.splitext(basename)
  path = os.path.dirname(filename)
  
  # Get all the files in the path.
  pathFiles = {}
  for p in os.listdir(path):
    pathFiles[p.lower()] = p
  
  for f in pathFiles:
    (froot, fext) = os.path.splitext(f)
    if fext[1:] in subtitleExt:
      langCheck =  string.translate(froot.encode('utf-8'), string.maketrans(string.punctuation + string.whitespace, ' ' * len (string.punctuation + string.whitespace))).split(' ')[-1].strip()
      
      # Remove the language from the filename for comparison purposes.
      frootNoLang = froot[:-(len(langCheck))-1] 
      
      if (fileroot == froot) or (fileroot == frootNoLang):
        Log('found subtitle file: ' + f + ' language test: ' + langCheck)
        part.subtitles[Locale.Language.Match(langCheck)][f] = Proxy.LocalFile(os.path.join(path, pathFiles[f]))

class localMediaMovie(Agent.Movies):
  name = 'Local Media Assets (Movies)'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))
    
  def update(self, metadata, media, lang):

    filename = media.items[0].parts[0].file.decode('utf-8')
    Log(filename)
    
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
            elif t == 'art':
              if f not in metadata.art:
                metadata.art[f] = Proxy.Media(data)
                Log('Local asset (type: ' + t + ') added: ' + f)
    
    # Look for subtitles
    for i in media.items:
      for part in i.parts:
        FindSubtitles(part)
                
class localMediaTV(Agent.TV_Shows):
  name = 'Local Media Assets (TV)'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(id = 'null', score = 100))
    
  def update(self, metadata, media, lang):
    
    # Look for subtitles for each episode.
    for s in media.seasons:
      for e in media.seasons[s].episodes:
        for i in media.seasons[s].episodes[e].items:
          for part in i.parts:
            FindSubtitles(part)
