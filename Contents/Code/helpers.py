import unicodedata

# A platform independent way to split paths which might come in with different separators.
def splitPath(str):
  if str.find('\\') != -1:
    return str.split('\\')
  else: 
    return str.split('/')

def unicodize(s):
  filename = s
  try: 
    filename = unicodedata.normalize('NFC', unicode(s.decode('utf-8')))
  except: 
    Log('Failed to unicodize: ' + filename)
    pass
  return filename

def cleanFilename(filename):
  #this will remove any whitespace and punctuation chars and replace them with spaces, strip and return as lowercase
  return string.translate(filename.encode('utf-8'), string.maketrans(string.punctuation + string.whitespace, ' ' * len (string.punctuation + string.whitespace))).strip().lower()