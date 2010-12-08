from screenlets.plugins import Exaile
import gobject
import re
from player import PlayerEvents

elapsed_regex = re.compile('(.)+\[(?P<min>\d(\d)?):(?P<sec>\d\d)\]') # (bla bla [d(d)?:dd])
REFRESH_INTERVAL = 1000

class ExailePlayer(Exaile.ExaileAPI, PlayerEvents):

	timer          = None	
	lastStatus     = None
	lastSong       = None
	lastTime	   = 0
	
	def __init__(self, session_bus):
		Exaile.ExaileAPI.__init__(self, session_bus)
		PlayerEvents.__init__(self)
		self.__name__ = "Exaile"
	
	def connect(self):
		Exaile.ExaileAPI.connect(self)
		if self.timer != None:
			gobject.source_remove(self.timer)
		self.timer = gobject.timeout_add(REFRESH_INTERVAL, self.checkForUpdate)
		self.lastSong = self.getCurrentFile()
	
	def disconnect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
		
		
	def checkForUpdate(self):
		try:
			status = self.playerAPI.status()
			# song change events
			if self.onSongChanged:
				playing_song = self.getCurrentFile()
				if playing_song != self.lastSong:
					if self.onSongChanged != None:
						self.onSongChanged(playing_song)
				self.lastSong = playing_song
		
			# elapsed events
			if self.onElapsed:				
				elapsed = self.getElapsed()
				if elapsed-self.lastTime not in range (0,3):
					#print str(elapsed) +' '+str(self.lastTime)
					self.onElapsed(elapsed)
				self.lastTime = elapsed	
		
			# play/stop events
			if self.lastStatus and status != self.lastStatus:
				if status == 'playing' and self.onPlay != None:
					self.onPlay()
				if self.lastStatus == 'playing' and (status == 'paused' or status == 'stopped') and self.onStop != None:
					self.onStop()
				
			self.lastStatus = status
			return True
		#"""
		except Exception, e:
			print e
			return False
		#"""
	
	def getElapsed(self):
		query = self.playerAPI.query()
		match = elapsed_regex.match(query)
		if match: 
			return 60*int(match.group('min'))+int(match.group('sec'))
		return 0
	
	def getCurrentFile(self):
		filename = self.playerAPI.get_track_attr('loc')
		if filename != '':
			return filename
		 
	# Exaile.ExaileAPI method is_playing() doing something different
	def is_playing(self):
		return self.playerAPI.status() == 'playing'
