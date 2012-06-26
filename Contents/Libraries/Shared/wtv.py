import re, os
import datetime

class WTV_Metadata:
  def __init__(self, filename):
    self.filename = filename
    f = open(filename,'rb')
    metaHeader = f.read(80000)
    metaHeader = metaHeader[metaHeader.find('\x57\x00\x4D\x00\x2F\x00'):]
    # Search for printable ASCII characters encoded as UTF-16LE.
    tags = metaHeader.split('\x5A\xFE\xD7\x6D\xC8\x1D\x8F\x4A\x99\x22\xFA\xB1\x1C\x38\x14\x53')
    pat = re.compile(ur'(?:[\x20-\x7E][\x00]){2,}')
    self.tagDict = {}
    for z in tags:
      z = [w.decode('utf-16le').encode('utf-8') for w in pat.findall(z)]
      if len(z)==1:
        self.tagDict[z[0]] = ''
      elif len(z)==2:
        self.tagDict[z[0]] = z[1]
      else:
        continue
        
  def getTitle(self):
    return self.tagDict['Title']
  
  def getEpisodeTitle(self):
    return self.tagDict['WM/SubTitle']
    
  def getOriginalBroadcastDateTime(self):
    origDate = self.tagDict['WM/MediaOriginalBroadcastDateTime']
    if origDate[:4] == '0001':
      # let's use the create date instead of the metadata supplied date
      mod_time = os.path.getmtime(self.filename)
      origDate = datetime.date.fromtimestamp(mod_time)
    else:
      origDate = datetime.datetime.strptime(origDate.replace('T',' ').replace('Z',''), '%Y-%m-%d %H:%M:%S').date()
    return origDate
      
  def getOriginalReleaseTime(self):
    return int(self.tagDict['WM/OriginalReleaseTime'])
    
  def getGenres(self):
    return self.tagDict['WM/Genre'].split(';')
  
  def getStationName(self):
    return self.tagDict['WM/MediaStationName']
  
  def getDescription(self):
    return self.tagDict['WM/SubTitleDescription']
  
  def getContentRating(self):
    return self.tagDict['WM/ParentalRating']