#local media assets agent
import os

artExt = ['jpg','jpeg','png','tbn']
posterFiles = ['poster','default','cover','movie']
fanartFiles = ['fanart']

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
    #Log('Local Media Filename: ' + filename)
    path = os.path.dirname(filename)
    Log(path)
    if 'video_ts' == path.lower().split('/')[-1]:
      path = '/'.join(path.split('/')[:-1])
      Log(path)
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    pathFiles = {}
    pathFilesLower = []
    for p in os.listdir(path):
      pathFiles[p.lower()] = p
      pathFilesLower += [p]
    extraFiles = [fileroot, path.split('/')[-1]]

    #look for posters
    for e in artExt:
      for a in posterFiles + extraFiles: # all posterfile names, the filename, the foldername (as a file)
        f = (a + '.' + e).lower()
        Log(f)
        if f in pathFilesLower:
          data = Core.storage.load(os.path.join(path, pathFiles[f]))
          if f not in metadata.posters:
            metadata.posters[f] = Proxy.Media(data)
            Log('local poster added: ' + f)
            
    #look for fanart
    for e in artExt:
      for a in fanartFiles + extraFiles:
        f = (a + '.' + e).lower()
        if f in pathFilesLower:
          data = Core.storage.load(os.path.join(path, pathFiles[f]))
          if f not in metadata.art:
            metadata.art[f] = Proxy.Media(data)
            Log('local fanart added: ' + f)    