import gobject
from player import PlayerEvents

REFRESH_INTERVAL = 1000
class GenericPlayer(PlayerEvents):

	timer         = None	
	lastState     = None
	lastSong      = None
	lastTime      = 0
	
	def __init__(self, name, songChange = True, elapsedChange = True, stateChange = True):
		PlayerEvents.__init__(self)
		self.__name__ = name
		self.emitSongChangeEvents    = songChange
		self.emitElapsedChangeEvents = elapsedChange
		self.emitStateChangeEvents   = stateChange
	
	def connect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
		self.timer = gobject.timeout_add(REFRESH_INTERVAL, self.checkForUpdate)
		self.lastSong = self.getCurrentFile()
	
	def disconnect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
		
		
	def checkForUpdate(self):
		#print "refresh"
		try:
			# song change events
			if self.emitSongChangeEvents and self.onSongChanged:
				playing_song = self.getCurrentFile()
				if playing_song != self.lastSong:
					if self.onSongChanged != None:
						self.onSongChanged(playing_song)
				self.lastSong = playing_song
		
			# elapsed events
			if self.emitElapsedChangeEvents and self.onElapsed:				
				elapsed = self.getElapsed()
				if elapsed-self.lastTime < 0 or elapsed-self.lastTime > 2:
					#print str(elapsed) +' '+str(self.lastTime)
					self.onElapsed(elapsed)
				self.lastTime = elapsed	
		
			# play/stop events
			if self.emitStateChangeEvents:
				state = "play" if self.is_playing() else "stop"
				if (state != self.lastState):
					if state == "play" and self.onPlay != None:
						self.onPlay()
					if state == "stop" and self.onStop != None:
						self.onStop()
					self.lastState = state
				
			return True
		#"""
		except Exception, e:
			print e
			return False
		#"""
	
	def is_active(self, dbus_iface):
		pass
		
	def getElapsed(self):
		pass
	
	def getCurrentFile(self):
		pass
		 
	def is_playing(self):
		pass
