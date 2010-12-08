#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


import hashlib
import httplib
import os
from xml.dom.minidom import parse, parseString

def mp3CheckSum(filename):
		##################################
		##### find first audio frame #####
		##################################
		# Plan A: parse mp3 header a compute id3v2.x tag size, maybe behind it will be first audio frame
		# read mp3 header
		if not filename.endswith(".mp3"):
			print "Can't compute check sum for non mp3 files"
			
		try:
			if filename.startswith("file://"):
				filename = filename[7:]
			fp = open(filename, 'r')
			id3 = fp.read(3)
			ver = fp.read(2)
			flags = fp.read(1)
			size = fp.read(4)

			tagsize = 0
			if id3 == "ID3":
				tagsize = 10		
				for i in range(4):
					tagsize = tagsize + ord(size[3-i])*pow(128, i)

				#print id3
				#print 'version: id3v2.'+str(ord(ver[0])) + '.'+str(ord(ver[1]))
				#print 'flags: '+str(ord(flags))
				#print tagsize

			fp.seek(tagsize)
			# check if there is first audio frame, if not, Plan B: find it byte by byte
			while True:
				if ord(fp.read(1)) == 0xFF and ord(fp.read(1)) & 0xE0 == 0xE0: break
			tagsize = fp.tell()-2
			#print tagsize

			fp.seek(tagsize)
			# to make request to server to download lyrics, checksum from this part of the mp3 file is needed 
			md = hashlib.md5()
			md.update(fp.read(163840))
			fp.close()
			return md.hexdigest()
		except Exception, e:
			print "ChekSum function error: %s" % e


def process(xmlData):
	#print "processing lyrics ..."
	additionalInfo = ''
	from xml.dom.minidom import parse, parseString

	#xmlData = xmlData.encode("utf-8")
	
	dom = parseString(xmlData)
	lyricsElements = dom.getElementsByTagName('strLyric')
	lyricsList = []
	for elem in lyricsElements:
		textNode = elem.childNodes[0]
		if textNode.nodeType == elem.TEXT_NODE:
			lyrics = str(textNode.nodeValue)
			#lyrics = lyrics.replace('&lt;br&gt;', os.linesep)
			lyrics = lyrics.replace('<br>', os.linesep)
			lyricsList.append(lyrics)
		
	#lyricsData = self.parseXML(xmlData, 'strLyric')
	#lyricsData = lyricsData.replace('<strLyric>', '<strLyric>'+os.linesep)
	#lyricsData = lyricsData.replace('&lt;br&gt;', os.linesep)
	return lyricsList
	
install_path = os.path.dirname(os.path.abspath(__file__)) + os.sep
servers = [
			{
				'Host': 'lyrics.alsong.net',
				#'IP': '204.232.253.233',#'67.192.185.143',
				'URL': 'http://lyrics.alsong.net/alsongwebservice/service1.asmx',
				'headers' : {'Content-Type':'text/xml; charset=utf-8', 'Host':'lyrics.alsong.net'},
				'request_file' : "%squery.xml" % install_path
			},
			{
				'Host': 'lyrics.alsong.co.kr',
				#'IP': , '218.153.8.105',
				'URL': 'http://lyrics.alsong.co.kr/alsongwebservice/service1.asmx',
				'headers' : {'Content-Type':'application/soap+xml; charset=utf-8', 'Host':'lyrics.alsong.co.kr'},
				'request_file' : "%squery2.xml" % install_path
			}
			
	]


class ALSongEngine:

	checkSum = None
	continueDownloading = True
	
	def __init__(self, callback = None):
		self.resultCallback = callback
		self.install_path = os.path.dirname(os.path.abspath(__file__)) + os.sep
		self.server = servers[1]
	
	def stop(self):
		self.continueDownloading = False
		
	def find(self, songInfo):
		#print "search on ALSong"
		self.continueDownloading = True
		if not songInfo.has_key('title') or not songInfo.has_key('artist'):
			return
		
		title  = songInfo['title']
		artist = songInfo['artist']
		request = open(self.server['request_file']).read()
		request = request.replace('title' , title)
		request = request.replace('artist', artist)

		self.server = servers[0]
		self.lyricsCount = 0
		self.download(request)
		print "ALSong Server1 Lyrics Count: %d" % self.lyricsCount
		
		if self.lyricsCount == 0:
			self.server = servers[1]
			self.lyricsCount = 0
			self.download(request)
			print "ALSong Server2 Lyrics Count: %d" % self.lyricsCount
	
	def download(self, request):
		if os.environ.has_key('http_proxy'):
			proxy = os.environ['http_proxy']
			proxy_ip = proxy[7:]
			if proxy_ip.endswith("/"):			
				proxy_ip = proxy_ip[:-1]
				
			print "Using proxy: %s" % proxy
			print proxy_ip
				
		else:
			proxy = None
		#print "PROXY"
		#print proxy
		block_size = 1024
		try:
			headers = self.server['headers']#{'Content-Type':'text/xml; charset=utf-8', 'Host':'lyrics.alsong.net'}
			if proxy != None:				
				h = httplib.HTTPConnection(proxy_ip)
				h.request ('POST', self.server['URL'], request, headers)
			else:
				# lyrics.alsong.net server
				h = httplib.HTTPConnection(self.server['Host'])
				h.request ('POST', '/alsongwebservice/service1.asmx', request, headers)
				
			#h.set_debuglevel(1)
			response = h.getresponse()
			#print response.read()
			data = ""
			progress = 0
			while self.continueDownloading == True:
				block = response.read(block_size)
				data = data + block
				data = self.processChunk(data)
				if len(block) == 0:
					print "end of response"
					break
		        
		except Exception, e:
			print e		
		
	def processChunk(self, data):
		elem_start = data.find("<strLyric>")
		if elem_start != -1:
			#print data
			elem_start += 10 # skip <strLyric> tag
			elem_end = data.find("</strLyric>", elem_start)
			if elem_end != -1:
				lyrics = data[elem_start : elem_end]
				
				if self.continueDownloading == True:
					lyrics = lyrics.replace('&lt;br&gt;', os.linesep)
					#print lyrics
					self.resultCallback(lyrics)
					self.lyricsCount += 1
					
				data = data[elem_end :]
				
				# try to eat more elements recursively
				data = self.processChunk(data)
		return data
		
			    
	def findByCheckSum(self, filename):
		checkSum = mp3CheckSum(filename)
		#print "checksm %s" % checkSum
		if checkSum == None:
			return None
		print checkSum
		####################################
		##### download lyrics from net #####
		####################################
		request = open(self.install_path+"request2.xml").read()
		request = request.replace('checkSum', checkSum)
		xmlData = None
		try:
			headers = {'Content-Type':'text/xml; charset=utf-8', 'Host':'lyrics.alsong.net'}
			#headers = {'Content-Type':'application/soap+xml; charset=utf-8', 'Host':'lyrics.alsong.co.kr'}
			if os.environ.has_key('http_proxy'):
				proxy = os.environ['http_proxy']
				proxy_ip = proxy[7:]
				print "Using proxy: %s" % proxy
				if proxy_ip.endswith("/"):			
					proxy_ip = proxy_ip[:-1]
				print proxy_ip
				h = httplib.HTTPConnection(proxy_ip)
				h.request ('POST', 'http://lyrics.alsong.net/alsongwebservice/service1.asmx', request, headers)
			else:
				#h = httplib.HTTPConnection("218.153.8.105")
				#print "%%%%%%%%%%%%%%%%%%%%%%"
				h = httplib.HTTPConnection("lyrics.alsong.net")
				h.request ('POST', '/alsongwebservice/service1.asmx', request, headers)
				
			#h.set_debuglevel(1)
			xmlData = h.getresponse().read()
			#print xmlData
				
		except Exception, e:
			print "Can't connect to server! " + str(e)
			
		if xmlData != None and xmlData.find("<strLyric>") != -1:
			lyricsList = process(xmlData)
			if len(lyricsList) > 0:
				return lyricsList[0]
		
	
	def response2(self, request):
		try:
			# lyrics.alsong.co.kr server
			h = httplib.HTTPConnection("218.153.8.105")
			#h.set_debuglevel(1)
			headers = {'Content-Type':'application/soap+xml; charset=utf-8', 'Host':'lyrics.alsong.co.kr'}
			h.request ('POST', '/alsongwebservice/service1.asmx', request, headers)
			return h.getresponse().read()
		except Exception, e:
			print e
		
	def response1(self, request):
		try:
			# lyrics.alsong.net server
			h = httplib.HTTPConnection("67.192.185.143")
			#h.set_debuglevel(1)
			headers = {'Content-Type':'text/xml; charset=utf-8', 'Host':'lyrics.alsong.net'}
			h.request ('POST', '/alsongwebservice/service1.asmx', request, headers)
			return h.getresponse().read()
		except Exception, e:
			print e
		
	def parse(self, xmlData, tagName):
		dom = parseString(xmlData)
		dom.getElementsByTagName(tagName)
		
	def parseXML(self, xmlData, tag):
		sTag = '<'+tag+'>'
		eTag = '</'+tag+'>'
		start = xmlData.find(sTag)
		end = xmlData.find(eTag)
		if start != -1 and end > start:
			return xmlData[start+len(sTag) : end]
		return None
		
