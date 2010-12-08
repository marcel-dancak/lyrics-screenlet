#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

import urllib
import urllib2
import re

partial_result_regex = re.compile('partial: (\d+)\s')
		
class LrcdbEngine:
	
	continueDownloading = True
	
	def __init__(self, resultCallback):
		self.resultCallback = resultCallback
	
	def stop(self):
		self.continueDownloading = False
		
	def find(self, songInfo):
		self.continueDownloading = True
		
		if not songInfo.has_key('title') or not songInfo.has_key('artist'):
			return
		
		title  = songInfo['title' ]
		artist = songInfo['artist']
	
		if songInfo.has_key('album'):
			album = songInfo['album']
		else:
			album = ''
	
		params = {'artist':str(unicode(artist).encode('utf8')),'title':str(unicode(title).encode('utf8')),'album':album,'query':'plugin','type':'plugin','submit':'submit'}
		try:
			file = urllib2.urlopen('http://www.lrcdb.org/search.php',urllib.urlencode(params))
			response = file.read()
			#print "lrcdb response:"
			#print response
			file.close()
			
			for response in response.rsplit('\n'):
				if self.continueDownloading == True and not response.startswith('no match'):
					if response.startswith('exact: '):
						lrcId = response[7:]
					else:
						match = partial_result_regex.match(response)
						if match:
							lrcId = match.group(1)
						else: continue
	
					print lrcId
					url = 'http://www.lrcdb.org/lyric.php?lid=%s&astext=yes' %lrcId
					lyrFile = urllib2.urlopen(url)
					lyrics = lyrFile.read()
					lyrFile.close()
					#print lyrics
					# brrr, windows separators
					if self.continueDownloading == True:
						self.resultCallback(lyrics.replace('\r\n', '\n'))
		except Exception, e:
			print e

