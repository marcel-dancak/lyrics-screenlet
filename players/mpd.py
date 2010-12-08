from screenlets.plugins import mpdclient2
import os
import re
import gobject
from player import PlayerEvents

def parseValue(param, line):
	regex = '([\s#])*%s(\s)*"(?P<value>(.)*)"' % param
	r = re.compile(regex)
	m = r.match(line)
	if m:
		return m.group('value')

DELAY = 1000

class mpd(PlayerEvents):

	__name__       = "MPD"#"Music Player Daemon"
	timer          = None

	lastStatus     = None
	lastSong       = None
	lastTime	   = 0
	
	music_dir      = None
	port           = 6600
	host           = "localhost"
	password       = ""
	configuration_found = False
	
	def __init__(self, session_bus): # session_bus not used, fust for API
		self.parseMpdConfig()
		#print self.music_dir
		#print self.port	
		
	def is_active(self, dbus_iface):
		if self.configuration_found:
			try:
				mpdclient2.connect(host = self.host, port = self.port, password = self.password)
				return True
			except Exception, e:
				pass
				#print "Cannot connect to MPD: %s" % str(e) # too much mess when ...
		return False
	
	def connect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
		self.timer = gobject.timeout_add(DELAY, self.checkForUpdate)
		self.lastSong = self.getCurrentFile()
		
	def disconnect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
	
	def parseMpdConfig(self):
		mpd_config_file = os.environ['HOME']+os.sep+".mpdconf"
		if not os.path.exists(mpd_config_file):
			print "MPD configuration file %s doesn't exist, /etc/mpd.conf will be used" % mpd_config_file
			mpd_config_file = "/etc/mpd.conf"
			if not os.path.exists(mpd_config_file):
				print "MPD configuration file %s doesn't exist, MPD support will be disabled" % mpd_config_file
				return
				
		
		try:
			mpd_config = open(mpd_config_file, 'r')
			
			for line in mpd_config:
				line = line.rstrip()
				if not line.startswith("#"):
			
					if line.find("music_directory") != -1:
						self.music_dir = parseValue("music_directory", line)
						if not self.music_dir.endswith(os.sep):
							self.music_dir += os.sep
						self.configuration_found = True # valid configuration found
						
					elif line.find("host") != -1:
						self.host = parseValue("host", line)
				
					elif line.find("password") != -1:
						self.password = parseValue("password", line)
					
					elif line.find("port") != -1:
						port = parseValue("port", line)
						if port != None:
							self.port = int(port)
		except Exception, e:
			print "Can't read/parse MPD configuration file: %s. %s" % (os.environ['HOME']+os.sep+".mpdconf", e)
			
	def getCurrentFile(self):
		try:
			song = mpdclient2.connect(host = self.host, port = self.port, password = self.password).currentsong().file
			return self.music_dir+song
		except Exception, e:
			print e
	
	def get_title(self):
		try:
			return mpdclient2.connect(host = self.host, port = self.port, password = self.password).currentsong().title
		except Exception, e:
			print e
	
	def get_artist(self):
		try:
			return mpdclient2.connect(host = self.host, port = self.port, password = self.password).currentsong().artist
		except Exception, e:
			print e

	def get_album(self):
		try:
			return mpdclient2.connect(host = self.host, port = self.port, password = self.password).currentsong().album
		except Exception, e:
			print e
						
	def getElapsed(self):
		try:
			time = mpdclient2.connect(host = self.host, port = self.port, password = self.password).status().time
			elapsed = float(time.replace(":", "."))
			return elapsed
		except Exception, e:
			return 0.0
			
	def is_playing(self):
		try:
			return mpdclient2.connect(host = self.host, port = self.port, password = self.password).status().state == "play"
		except Exception, e:
			print e
			
			
	def checkForUpdate(self):
		try:
			# song change events
			if self.onSongChanged:
				playing_song = self.getCurrentFile()
				if playing_song != self.lastSong:
					if self.onSongChanged != None:
						#print 'generate onSongChange'
						self.onSongChanged(playing_song)
				self.lastSong = playing_song
			
			# elapsed events
			if self.onElapsed:
				elapsed = self.getElapsed()
				if elapsed-self.lastTime > 2 or elapsed-self.lastTime < 0:
					self.onElapsed(elapsed)
				self.lastTime = elapsed
				
			# play/stop events
			status = mpdclient2.connect(host = self.host, port = self.port, password = self.password).status().state
			if self.lastStatus != None and status != self.lastStatus:
				if status == 'play' and self.onPlay != None:
					self.onPlay()
				if self.lastStatus == 'play' and (status == 'pause' or status == 'stop') and self.onStop != None:
					self.onStop()
				
			self.lastStatus = status
			return True

		except Exception, e:
			print e
			return False
		
		
