import os, unicodedata
import config
import helpers
import subtitlehelpers

#####################################################################################################################

def findAssests(metadata, paths, type, part = None):
  root_file = getRootFile(helpers.unicodize(part.file)) if part else None

  # We start by building a dictionary of files to their absolute paths. We also need to know
  # the number of media files that are actually present, in case the found local media asset 
  # is limited to a single instance per media file.
  path_files = {}
  total_media_files = 0
  for path in paths:
    path = helpers.unicodize(path)
    for file_path in os.listdir(path):

      # When using os.listdir with a unicode path, it will always return a string using the
      # NFD form. However, we internally are using the form NFC and therefore need to convert
      # it to allow correct regex / comparisons to be performed.
      if os.path.isfile(os.path.join(path, helpers.unicodize(file_path))):
        path_files[file_path.lower()] = os.path.join(path, file_path)

      # If we've found an actual media file (not a trailer), we should record it.
      (root, ext) = os.path.splitext(file_path)
      if ext.lower()[1:] in config.VIDEO_EXTS and root.lower().endswith('-trailer') == False:
        total_media_files += 1

  Log('Looking for %s media (%s) in %d paths (root file: %s) with %d media files.', type, metadata.title, len(paths), root_file, total_media_files)
  Log('Paths: %s', ", ".join([ helpers.unicodize(p) for p in paths ]))

  # Figure out what regexs to use.
  search_tuples = []
  if type == 'season':
    search_tuples += [['season(-|0|\s)?%s[-a-z]?(-poster)?' % metadata.index, metadata.posters, config.IMAGE_EXTS, False]]
    search_tuples += [['season(-|0|\s)?%s-banner[-a-z]?' % metadata.index, metadata.banners, config.IMAGE_EXTS, False]]
    if int(metadata.index) == 0: # Season zero, also look for Frodo-compliant 'specials' artwork.
      search_tuples += [['season-specials-poster', metadata.posters, config.IMAGE_EXTS, False]]
      search_tuples += [['season-specials-banner', metadata.banners, config.IMAGE_EXTS, False]]
  elif type == 'show':
    search_tuples += [['(show|poster|folder)-?[0-9]?', metadata.posters, config.IMAGE_EXTS, False]]
    search_tuples += [['banner-?[0-9]?', metadata.banners, config.IMAGE_EXTS, False]]
    search_tuples += [['(fanart|art|background|backdrop)-?[0-9]?', metadata.art, config.IMAGE_EXTS, False]]
    search_tuples += [['theme-?[0-9]?', metadata.themes, config.AUDIO_EXTS, False]]
  elif type == 'episode':
    search_tuples += [[re.escape(root_file) + '(-|-thumb)?[0-9]?', metadata.thumbs, config.IMAGE_EXTS, False]]
  elif type == 'movie':
    search_tuples += [['(poster|default|cover|movie|folder|' + re.escape(root_file) + ')-?[0-9]?', metadata.posters, config.IMAGE_EXTS, True]]
    search_tuples += [['(fanart|art|background|backdrop|' + re.escape(root_file) + '-fanart' + ')-?[0-9]?', metadata.art, config.IMAGE_EXTS, True]]

  for (pattern, media_list, extensions, limited) in search_tuples:
    valid_keys = []
    
    sort_index = 1
    file_path_keys = sorted(path_files.keys(), key = lambda x: os.path.splitext(x)[0])
    for file_path in file_path_keys:
      for ext in extensions:
        if re.match('%s.%s' % (pattern, ext), file_path, re.IGNORECASE):

          # Use a pattern if it's unlimited, or if there's only one media file.
          if (limited and total_media_files == 1) or (not limited) or (file_path.find(root_file.lower()) == 0):

            # Read data and hash it.
            data = Core.storage.load(path_files[file_path])
            media_hash = hashlib.md5(data).hexdigest()
      
            # See if we need to add it.
            valid_keys.append(media_hash)
            if media_hash not in media_list:
              media_list[media_hash] = Proxy.Media(data, sort_order = sort_index)
              sort_index = sort_index + 1
              Log('  Local asset added: %s (%s)', path_files[file_path], media_hash)
          else:
            Log('Skipping file %s because there are %d media files.', file_path, total_media_files)
              
    Log('Found %d valid things for pattern %s (ext: %s)', len(valid_keys), pattern, str(extensions))
    media_list.validate_keys(valid_keys)

def getRootFile(filename):
  path = os.path.dirname(filename)
  if 'video_ts' == helpers.splitPath(path.lower())[-1]:
    path = '/'.join(helpers.splitPath(path)[:-1])
  basename = os.path.basename(filename)
  (root_file, ext) = os.path.splitext(basename)
  return root_file

#####################################################################################################################

def findSubtitles(part):

  lang_sub_map = {}
  part_filename = helpers.unicodize(part.file)
  part_basename = os.path.splitext(os.path.basename(part_filename))[0]
  paths = [ os.path.dirname(part_filename) ]

  # Check for a global subtitle location
  global_subtitle_folder = os.path.join(Core.app_support_path, 'Subtitles')
  if os.path.exists(global_subtitle_folder):
    paths.append(global_subtitle_folder)

  # We start by building a dictionary of files to their absolute paths. We also need to know
  # the number of media files that are actually present, in case the found local media asset 
  # is limited to a single instance per media file.
  file_paths = {}
  total_media_files = 0
  for path in paths:
    path = helpers.unicodize(path)
    for file_path_listing in os.listdir(path):

      # When using os.listdir with a unicode path, it will always return a string using the
      # NFD form. However, we internally are using the form NFC and therefore need to convert
      # it to allow correct regex / comparisons to be performed.
      if os.path.isfile(os.path.join(path, helpers.unicodize(file_path_listing))):
        file_paths[file_path_listing.lower()] = os.path.join(path, file_path_listing)

      # If we've found an actual media file, we should record it.
      (root, ext) = os.path.splitext(file_path_listing)
      if ext.lower()[1:] in config.VIDEO_EXTS:
        total_media_files += 1

  Log('Looking for subtitle media in %d paths with %d media files.', len(paths), total_media_files)
  Log('Paths: %s', ", ".join([ helpers.unicodize(p) for p in paths ]))

  for file_path in file_paths.values():

    local_basename = helpers.unicodize(os.path.splitext(os.path.basename(file_path))[0])
    local_basename2 = local_basename.rsplit('.', 1)[0]
    filename_matches_part = local_basename == part_basename or local_basename2 == part_basename

    # If the file is located within the global subtitle folder and it's name doesn't match exactly
    # then we should simply ignore it.
    if file_path.count(global_subtitle_folder) and not filename_matches_part:
      continue

    # If we have more than one media file within the folder and located filename doesn't match 
    # exactly then we should simply ignore it
    if total_media_files > 1 and not filename_matches_part:
      continue

    subtitle_helper = subtitlehelpers.SubtitleHelpers(file_path)
    if subtitle_helper != None:
      local_lang_map = subtitle_helper.process_subtitles(part)
      for new_language, subtitles in local_lang_map.items():

        # Add the possible new language along with the located subtitles so that we can validate them
        # at the end...
        if not lang_sub_map.has_key(new_language):
          lang_sub_map[new_language] = []
        lang_sub_map[new_language] = lang_sub_map[new_language] + subtitles

  # Now whack subtitles that don't exist anymore.
  for language in lang_sub_map.keys():
    part.subtitles[language].validate_keys(lang_sub_map[language])
    
  # Now whack the languages that don't exist anymore.
  for language in list(set(part.subtitles.keys()) - set(lang_sub_map.keys())):
    part.subtitles[language].validate_keys({})
