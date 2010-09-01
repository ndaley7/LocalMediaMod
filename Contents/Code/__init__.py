#local media assets agent
import os

artExt =   ['jpg','jpeg','png','tbn']
allFiles = {'posters': ['poster','default','cover','movie','folder'],
            'art':     ['fanart']}

class localmedia(Agent.Movies):
  name = 'Local Media Assets'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.thetvdb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
        id    = 'null',
        score = 100    ))
    
  def update(self, metadata, media, lang):
    passFiles = {}
    filename = media.items[0].parts[0].file
    path = os.path.dirname(filename)
    if 'video_ts' == path.lower().split('/')[-1]:
      path = '/'.join(path.split('/')[:-1])
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    pathFiles = {}
    for p in os.listdir(path):
      pathFiles[p.lower()] = p

    passFiles['posters'] = allFiles['posters'] + [fileroot, path.split('/')[-1]] #add the filename as a base, and the dirname as a base for poster lookups
    passFiles['art'] = allFiles['art'] + [fileroot + '-fanart'] 

    #look for posters and art
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