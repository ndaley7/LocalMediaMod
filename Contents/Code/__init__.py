#local media assets agent
import os

artExt =   ['jpg','jpeg','png','tbn']
allFiles = {'posters': ['poster','default','cover','movie'],
            'art':     ['fanart']}

class localmedia(Agent.Movies):
  name = 'Local Media Assets'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
        id    = 'null',
        score = 100    ))
    
  def update(self, metadata, media, lang):
    filename = media.items[0].parts[0].file
    path = os.path.dirname(filename)
    if 'video_ts' == path.lower().split('/')[-1]:
      path = '/'.join(path.split('/')[:-1])
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    pathFiles = {}
    pathFilesLower = []
    for p in os.listdir(path):
      pathFiles[p.lower()] = p
      pathFilesLower += [p]
    allFiles['posters'] = allFiles['posters'] + [fileroot, path.split('/')[-1]] #add the filename as a base, and the dirname as a base for poster lookups
    allFiles['art'] = allFiles['art'] + [fileroot + '-fanart']
    
    #look for posters and art
    for t in ['posters','art']:
      for e in artExt:
        for a in allFiles[t]:
          f = (a + '.' + e).lower()
          if f in pathFilesLower:
            data = Core.storage.load(os.path.join(path, pathFiles[f]))
            if t == 'posters':
              if f not in metadata.posters: metadata.posters[f] = Proxy.Media(data)
            elif t == 'art':
              if f not in metadata.art: metadata.art[f] = Proxy.Media(data)
            Log('local asset (type: ' + t + ') added: ' + f)
