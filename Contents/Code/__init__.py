#local media assets agent
import os

artExt            = ['jpg','jpeg','png','tbn']
artFiles          = {'posters': ['poster','default','cover','movie','folder'],
                     'art':     ['fanart']}
            
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','txt','ssa','aqt','jss','ass','idx']
opensubtitleLanguages = ['Albanian','Arabic','Armenian','Bosnian','Bulgarian','Catalan','Chinese','Croatian','Czech','Danish','Dutch',
                     'English','Esperanto','Estonian','Farsi','Finnish','French','Galician','Georgian','German','Greek','Hebrew','Hindi',
                     'Hungarian','Icelandic','Indonesian','Italian','Japanese','Kazakh','Korean','Latvian','Lithuanian','Luxembourgish',
                     'Macedonian','Malay','Norwegian','Occitan','Polish','Portuguese','Portuguese-BR','Romanian','Russian','Serbian','Slovak',
                     'Slovenian','Spanish','Swedish','Syriac','Thai','Turkish','Ukrainian','Urdu','Vietnamese','Unknown']

class localMediaMovie(Agent.Movies):
  name = 'Local Media Assets (Movies)'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
        id    = 'null',
        score = 100    ))
    
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

    passFiles = {}
    passFiles['posters'] = artFiles['posters'] + [fileroot, path.split('/')[-1]] #add the filename as a base, and the dirname as a base for poster lookups
    passFiles['art'] = artFiles['art'] + [fileroot + '-fanart'] 

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
    
    #look for subtitles
    for i in media.items:
      for p in i.parts:
        filename = p.file.decode('utf-8').lower()
        basename = os.path.basename(filename)
        (fileroot, ext) = os.path.splitext(basename)
        for f in pathFiles:
          (froot, fext) = os.path.splitext(f)
          if fext[1:] in subtitleExt: 
            for lang in opensubtitleLanguages: 
              if froot[-(len(lang)):] == lang.lower(): #does it have a language designator in the filename? 
                froot = froot[:-(len(lang))-1] #remove the language from the filename for comparison purposes
                break
            if fileroot == froot:
              #sample: media.items[0].parts[0].subtitles[Locale.Language.English][subtitle_name] = Proxy.LocalFile(file_path)
              #if you can't figure out the language, use Locale.Language.Unknown
              Log('found subtitle file: ' + f + ' language: ' + lang)
              p.subtitles[Locale.Language.Unknown][f] = Proxy.LocalFile(os.path.join(path, pathFiles[f]))
                
class localMediaTV(Agent.TV_Shows):
  name = 'Local Media Assets (TV)'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb']
  
  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
        id    = 'null',
        score = 100    ))
    
  def update(self, metadata, media, lang):

    for s in media.seasons:
      for e in media.seasons[s].episodes:
        filename = media.seasons[s].episodes[e].items[0].parts[0].file.decode('utf-8')
        Log(filename)
    
    path = os.path.dirname(filename)
    if 'video_ts' == path.lower().split('/')[-1]:
      path = '/'.join(path.split('/')[:-1])
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    pathFiles = {}
    for p in os.listdir(path):
      pathFiles[p.lower()] = p

    passFiles = {}
    passFiles['posters'] = artFiles['posters'] + [fileroot, path.split('/')[-1]] #add the filename as a base, and the dirname as a base for poster lookups
    passFiles['art'] = artFiles['art'] + [fileroot + '-fanart'] 

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
    
    #look for subtitles
    for s in media.seasons:
      for e in media.seasons[s].episodes:
        for i in media.seasons[s].episodes[e].items:
          for p in i.parts:
            filename = p.file.decode('utf-8').lower()
            basename = os.path.basename(filename)
            (fileroot, ext) = os.path.splitext(basename)
            for f in pathFiles:
              (froot, fext) = os.path.splitext(f)
              if fext[1:] in subtitleExt:
                for lang in opensubtitleLanguages: 
                  if froot[-(len(lang)):] == lang.lower(): #does it have a language designator in the filename? 
                    froot = froot[:-(len(lang))-1] #remove the language from the filename for comparison purposes
                    break
                if fileroot == froot:
                  #sample: media.items[0].parts[0].subtitles[Locale.Language.English][subtitle_name] = Proxy.LocalFile(file_path)
                  #if you can't figure out the language, use Locale.Language.Unknown
                  Log('found subtitle file: ' + f + ' language: ' + lang)
                  p.subtitles[Locale.Language.Unknown][f] = Proxy.LocalFile(os.path.join(path, pathFiles[f]))