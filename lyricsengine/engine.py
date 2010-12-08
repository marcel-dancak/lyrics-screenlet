#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


import threading
import ALSong
import lrcdb
import minilyrics

class ThreadDownloader(threading.Thread):
	def __init__(self, task, finishCallback = None):
		threading.Thread.__init__(self)
		self.task           = task
		self.finishCallback = finishCallback
		
	def setParams(self, *params):
		self.params = params
		
	def run(self):
		self.task(*self.params)
		if self.finishCallback != None:
			self.finishCallback()
		
LYRICS_SOURCES = ['alsong', 'minilyrics', 'lrcdb']


import urllib, urllib2, os
from xml.dom.minidom import parse, parseString

class LyricsScreenletEngine:
	
	continueDownloading = True
	url = 'http://webuser.byethost11.com/'
	
	def __init__(self, resultCallback):
		self.resultCallback = resultCallback
	
	def stop(self):
		self.continueDownloading = False
		
	def find(self, songInfo):
		self.continueDownloading = True
		
		if not songInfo.has_key('title') or not songInfo.has_key('artist'):
			return
		
		if songInfo.has_key('album'):
			album = songInfo['album']
		else:
			album = ''
		query = {
			'title': songInfo['title' ],
			'artist': songInfo['artist'],
			'album': album
		} 
		
		data = urllib.urlencode(query)
		try:
			req = urllib2.Request(self.url+"search.php", data)
			response = urllib2.urlopen(req)
			xml = response.read()
			response.close()
			#print xml
			dom = parseString(xml)
			elements = dom.getElementsByTagName('result')
			for elem in elements:
				#print elem
				print elem.getAttribute('id')
				if self.continueDownloading == True:
					req = urllib2.Request(self.url+"query.php", urllib.urlencode({'id': elem.getAttribute('id')}))
					response = urllib2.urlopen(req)
					lyrics = response.read()
					response.close()
					#print lyrics
					self.resultCallback(lyrics)
		except Exception, e:
			print e
			
class LyricsEngine:
	
	isRunning   = False
	searchQueue = None  # really simple queue
	count = 0
	
	def __init__(self, resultCallback, finishCallback):
		self.resultCallback = resultCallback
		self.finishCallback = finishCallback
		self.lyricsSources = []
		
		#alsongEngine = ALSong.ALSongEngine(self.resultCallback)
		#lrcdbEngine = lrcdb.LrcdbEngine(self.resultCallback)
		#minilyricsEngine = minilyrics.MiniLyricsEngine(self.resultCallback)
		alsongEngine = ALSong.ALSongEngine(self.lyrics)
		lrcdbEngine = lrcdb.LrcdbEngine(self.lyrics)
		minilyricsEngine = minilyrics.MiniLyricsEngine(self.lyrics)
		lyricsSLEngine = LyricsScreenletEngine(self.lyrics)
		
		self.lyricsEngines = {'alsong':alsongEngine,
							'lrcdb':lrcdbEngine,
							'minilyrics':minilyricsEngine,
							'lyricsscreenlet': lyricsSLEngine}
		
	def lyrics(self, lyrics):
		# filter lyrics here if needed
		#print "filer lyrics"
		try:
			import chardet
			encoding = chardet.detect(lyrics)
			print encoding
			#print lyrics.decode(encoding['encoding'], 'ignore')
			self.resultCallback(lyrics.decode(encoding['encoding'], 'ignore'))
		except:
			self.resultCallback(unicode(lyrics, 'utf-8'))
		
	def setLyricsSources(self, sources):
		self.lyricsSources = sources

	def wtf(self, lyrics):
		print "WTF"
		print lyrics
		
	def search(self, songInfo):
		#print "SEARCH FOR %s" % songInfo['title']
		"""
		from lyrics.AstrawebParser import AstrawebParser
		from lyrics.LyricWikiParser import LyricWikiParser
		from lyrics.LeoslyricsParser import LeoslyricsParser
		
		#parser = LeoslyricsParser(songInfo['artist'], songInfo['title'])
		#parser = LyricWikiParser(songInfo['artist'], songInfo['title'])
		parser = AstrawebParser(songInfo['artist'], songInfo['title'])
		parser.search(self.wtf)
		"""
		
		if self.isRunning == True:
			#print "I SHOULD SEARCHING, BUT STILL RUNNING"
			self.searchQueue = songInfo
			return
		
		self.isRunning = True
		self.finished = 0
		for source in self.lyricsSources:
			print "start %s" % source
			engine = self.lyricsEngines[source]
			downloader = ThreadDownloader(engine.find, self.onDownloaderFinish)
			downloader.setParams(songInfo)
			downloader.start()
			
	def stop(self):
		for source in self.lyricsSources:
			engine = self.lyricsEngines[source]
			engine.stop()
	
	def onDownloaderFinish(self):
		self.finished += 1
		#print "finished downloaders: %d" % self.finished
		if self.finished == len(self.lyricsSources):
			if self.searchQueue == None:
				#print "BUT ANOTHER SEARCHING FALLOW"
				self.finishCallback()
			self.isRunning = False
			if self.searchQueue != None:
				#print "&&&&&&&& SEARCH FROM QUEUE &&&&&&&&&&&"
				self.search(self.searchQueue)
				self.searchQueue = None

	def afterUpload(self):
		if self.afterUploadCallback != None:
			self.afterUploadCallback(self.uploadMessage)
		
	def upload(self, songInfo, lyrics, callback = None):
		t = ThreadDownloader(self.asynch_upload, self.afterUpload)
		self.afterUploadCallback = callback
		t.setParams(songInfo, lyrics)
		t.start()
		
	def asynch_upload(self, songInfo, lyrics):
		import httplib, urllib, urllib2
		values = {'artist'    : songInfo['artist'],
		          'title'     : songInfo['title'],
		          'album'     : songInfo['album'],
		          'lyrics'    : lyrics,
		          }
		data = urllib.urlencode(values)
		req = urllib2.Request("http://webuser.byethost11.com/lyrics.php", data)
		try:
			response = urllib2.urlopen(req)
			self.uploadMessage = "Lyrics was successfully uploaded"
		except urllib2.HTTPError, e:
			self.uploadMessage = "Duplicate lyrics or incomplete metadata"
			print e

	def reportMissingLyrics(self, songInfo):		
		if songInfo.has_key('title') and songInfo.has_key('artist') and songInfo.has_key('album'):
			#print os.getlogin()
			import getpass
			print getpass.getuser()
			values = {
				'title': unicode(songInfo['title' ]),
				'artist': unicode(songInfo['artist']),
				'album': unicode(songInfo['album']),
				'user': getpass.getuser()#os.getlogin()
			}
		
			data = urllib.urlencode(values)
			req = urllib2.Request("http://webuser.byethost11.com/missinglyrics.php", data)
			response = urllib2.urlopen(req)
			print response.read()
			response.close()
