from screenlets.plugins import Amarok
import gobject
import commands
from player import PlayerEvents

DELAY = 1000
class AmarokDcopPlayer(PlayerEvents):
	__name__       = "Amarok (dcop)"
	
	timer          = None
	lastStatus     = None
	lastSong       = None
	lastTime	   = 0
	
	def __init__(self, session_bus):
		pass
	
	def is_active(self, dbus_iface):
		if commands.getoutput("ps -A | grep amarokapp") != '':
			return commands.getoutput("dcop").find("amarok") != -1
		else:
			return False
		
	def connect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
		self.timer = gobject.timeout_add(DELAY, self.checkForUpdate)
		self.lastSong = self.getCurrentFile()
	
	def disconnect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
	
	
	def checkForUpdate(self):
		try:
			if self.is_playing():
				status = 'playing'
			else:
				status = 'paused'
			
			#print "old: %s new: %s" % (self.lastStatus, status)
			
			# song change events
			if self.onSongChanged:
				playing_song = self.getCurrentFile()
				if playing_song != self.lastSong:
					if self.onSongChanged != None:
						self.onSongChanged(playing_song)
				self.lastSong = playing_song
		
			# elapsed events
			if self.onElapsed:
				elapsed = float(self.getElapsed())
				#print 'diff: %s' % (elapsed-self.lastTime)
				if elapsed-self.lastTime > 2 or elapsed-self.lastTime < 0:
					#print 'fire elapsed'
					self.onElapsed(elapsed)
				self.lastTime = elapsed

			# play/stop events
			if self.lastStatus and status != self.lastStatus:
				print 'status changed: %s' % status
				if status == 'playing' and self.onPlay != None:
					self.onPlay()
				if self.lastStatus == 'playing' and (status == 'paused' or status == 'stopped') and self.onStop != None:
					self.onStop()
				
			self.lastStatus = status
			return True

		except Exception, e:
			print "Amarok player checking loop: %s" % e
			return False
	
	def is_playing(self):
		if commands.getoutput('dcop amarok player isPlaying') == 'true':
			return True;
		else:
			return False
			
	def getElapsed(self):
		output = commands.getoutput("dcop amarok player trackCurrentTimeMs")
		if output != 'call failed':
			elapsed = int(output)/1000.0
		else: elapsed = 0.0
		return elapsed
	
	def getCurrentFile(self):
		filename = commands.getoutput("dcop amarok player path")
		if filename != '' and filename != 'call failed':
			return filename
	
	def get_title(self):
		title = commands.getoutput("dcop amarok player title")
		if title != '' and title != 'call failed':
			return title
			
	def get_artist(self):
		artist = commands.getoutput("dcop amarok player artist")
		if artist != '' and artist != 'call failed':
			return artist
			
	def get_album(self):
		album = commands.getoutput("dcop amarok player album")
		if album != '' and album != 'call failed':
			return album
	
