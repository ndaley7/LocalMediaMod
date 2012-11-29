import config
import helpers

def findSubtitles(part):

  path_list = [ helpers.unicodize(part.file) ]

  # Chceck for a global subtitle location
  global_subtitle_folder = os.path.join(Core.app_support_path, 'Subtitles')
  if os.path.exists(global_subtitle_folder):
    path_list.append(os.path.join(global_subtitle_folder, os.path.basename(path_list[0])))

  lang_sub_map = {}
  for filename in path_list:
      
    basename = os.path.basename(filename)
    (fileroot, ext) = os.path.splitext(basename)
    fileroot = helpers.cleanFilename(fileroot)
    ext = ext.lower()
    
    # get the path, without filename
    path = os.path.dirname(filename)
    
    totalVidFiles = 0
    # Get all the files in the path.
    pathFiles = {}
    for p in os.listdir(path):
      (r, n) = os.path.splitext(helpers.unicodize(p))
      pathFiles[p] = helpers.cleanFilename(r) + n.lower()
      # Also, check to see if we have only one video filetype in this dir
      if n.lower()[1:] in config.VIDEO_EXTS:
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
      format = None
      (froot, fext) = pathFiles[f].split('.')
      
      # If we are looking in the global subtitle folder, we only accept filenames which match.
      if filename.count(global_subtitle_folder) and froot != helpers.cleanFilename(fileroot): 
        continue

      if f[0] != '.' and fext in config.SUBTITLE_EXTS:

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
                languages[lang].append(Proxy.LocalFile(os.path.join(path, f), index=str(langID), format="vobsub"))
                langID+=1
              
                if not lang_sub_map.has_key(lang):
                  lang_sub_map[lang] = []
                lang_sub_map[lang].append(f)
              
              for lang,subs in languages.items():
                part.subtitles[lang][f] = subs
        else:
          
          # Remove the language from the filename for comparison purposes.
          langCheck = helpers.cleanFilename(froot).split(' ')[-1].strip()
          frootNoLang = froot[:-(len(langCheck))-1].strip()
          
          if addAll or ((fileroot == froot) or (fileroot == frootNoLang)):
            if fext == 'txt' or fext == 'sub': #check to make sure this is a sub file
              try:
                txtLines = [l.strip() for l in Core.storage.load(os.path.join(path,f)).splitlines(True)]
                if re.match('^\{[0-9]+\}\{[0-9]*\}', txtLines[1]):
                  format = 'microdvd'
                elif re.match('^[0-9]{1,2}:[0-9]{2}:[0-9]{2}[:=,]', txtLines[1]):
                  format = 'txt'
                elif '[SUBTITLE]' in txtLines:
                  format = 'subviewer'
                else:
                  continue
              except:
                continue
            
            if codec is None and fext in ('ass', 'ssa', 'smi', 'srt', 'psb'):
              codec = fext.replace('ass', 'ssa')
              
            if format is None:
              format = codec
                
            Log('Found subtitle file: ' + f + ' language: ' + langCheck + ' codec: ' + str(codec))
            lang = Locale.Language.Match(langCheck)
            part.subtitles[lang][f] = Proxy.LocalFile(os.path.join(path, f), codec=codec, format=format)
            if not lang_sub_map.has_key(lang):
              lang_sub_map[lang] = []
            lang_sub_map[lang].append(f)
            
  # Now whack subtitles that don't exist anymore.
  for lang in lang_sub_map.keys():
    part.subtitles[lang].validate_keys(lang_sub_map[lang])