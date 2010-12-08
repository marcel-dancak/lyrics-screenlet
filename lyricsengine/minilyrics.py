#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


import urllib2
import hashlib
from xml.dom.minidom import parse, parseString


class MiniLyricsEngine:
	continueDownloading = True
	
	def __init__(self, callback):
		self.resultCallback = callback
		
	def stop(self):
		self.continueDownloading = False
		
	def find(self, songInfo):
		self.continueDownloading = True
		if not songInfo.has_key('title') or not songInfo.has_key('artist'):
			return
		
		title  = songInfo['title' ]
		artist = songInfo['artist']
		
		xml ="<?xml version=\"1.0\" encoding='utf-8'?>\r\n"
		xml+="<search filetype=\"lyrics\" artist=\"%s\" title=\"%s\" " % (artist.encode('utf-8'), title.encode('utf-8'))
		xml+="ClientCharEncoding=\"utf-8\"/>\r\n"
		md5hash=hashlib.md5(xml+"Mlv1clt4.0").digest()
		request="\x02\x00\x04\x00\x00\x00%s%s" % (md5hash, xml)
		del md5hash,xml
	
		url="http://www.viewlyrics.com:1212/searchlyrics.htm"
		#print request
		req=urllib2.Request(url,request)
		req.add_header("User-Agent", "MiniLyrics")
		print "minilyrics"
		self.lyricsCount = 0
		try:
			response = urllib2.urlopen(url, request)
			xml = response.read()
			response.close()

			dom = parseString(xml)

			elements = dom.getElementsByTagName('fileinfo')
			
			for element in elements:
				if self.continueDownloading == False:
					break
				
				artistAttribute = element.getAttribute('artist').lower()
				#print "%s in: %s" % (artist, artistAttribute)
				#print element.getAttribute('link')
				#print artistAttribute.lower().find(artist.lower())
				if artistAttribute.lower().find(artist.lower()) != -1:
					url = element.getAttribute('link')
					#print url
					response = urllib2.urlopen(url)
					lyrics = response.read()#.encode('utf-8')
					#print "URL: %s" % url
					#print lyrics
					if self.continueDownloading == True:
						self.resultCallback(lyrics)
						self.lyricsCount += 1
					response.close()
		except Exception, e:
			print e
		print "Minilyrics Lyrics Count: %d" % self.lyricsCount
