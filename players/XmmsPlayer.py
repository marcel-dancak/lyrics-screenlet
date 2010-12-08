try:
	import xmms
	xmms_support = True
except:
	xmms_support = False
	print "pyxmms package not installed, Xmms player support will be disabled"
	
import gobject
from player import PlayerEvents

REFRESH_INTERVAL = 1000
class XmmsPlayer(PlayerEvents):

	__name__   = "xmms"
	timer      = None
	
	lastStatus = None
	lastSong   = None
	lastTime   = 0
	
	active      = False
	isPlaying   = False
	currentFile = None
	title       = None
	isFrozen    = False
	
	def __init__(self, session_bus = None):
		pass
	
	def freeze(self):
		self.isFrozen = True
		self.disconnect()
		
	def defreeze(self):
		self.isFrozen = False
		if xmms_support == True:
			self.connect()
		
	def is_active(self, dbus_iface = None):
		#print xmms_support
		if not self.isFrozen:
			self.active = xmms_support and xmms.is_running()
			
		return self.active
		
	def connect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
		self.timer = gobject.timeout_add(REFRESH_INTERVAL, self.refreshCallback)
		self.lastSong = self.getCurrentFile()
	
	def disconnect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
			
	def getCurrentFile(self):
		if not self.isFrozen:
			playlistPosition = xmms.get_playlist_pos()
			self.currentFile = xmms.get_playlist_file(playlistPosition)
			return self.currentFile
		 
	def get_title(self):
		if not self.isFrozen:
			playlistPosition = xmms.get_playlist_pos()
			title = xmms.get_playlist_title(playlistPosition)
			metaData = title.split(" - ")
			self.title = metaData[1]
		return self.title
		
	def get_artist(self):
		if not self.isFrozen:
			playlistPosition = xmms.get_playlist_pos()
			title = xmms.get_playlist_title(playlistPosition)
			metaData = title.split(" - ")
			self.artist = metaData[0]
		return self.artist
		
	def get_album(self):
		return None

	def getElapsed(self):
		return xmms.get_output_time()/1000.0
		
	def is_playing(self):
		if not self.isFrozen:
			self.isPlaying = xmms.is_paused() == 0 and xmms.is_playing() == 1 #must be this combination
		return self.isPlaying
	
	def get_state(self):
		if xmms.is_playing() == 1:
			if xmms.is_paused() == 1:
				return 'pause'
			else:
				return 'play'
		else:
			return 'stop'
		
	def refreshCallback(self):
		try:
			#return True
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
			
			#print xmms.is_playing()
			#print xmms.is_paused()
			#print self.get_state()
			if self.is_playing(): status = 'play'
			else: status = 'pause'
			
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
#print dir(xmms)
#print xmms.get_info()
#print xmms.control.playlist(0,0)

