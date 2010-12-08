from screenlets.plugins import Quodlibet
import dbus
from player import PlayerEvents

class QuodlibetPlayer(Quodlibet.QuodlibetAPI, PlayerEvents):

	onSongChangeFn = None
	onPlayFn       = None
	onStopFn       = None
	onElapsedFn    = None

	def __init__(self, session_bus):
		Quodlibet.QuodlibetAPI.__init__(self, session_bus)
		PlayerEvents.__init__(self)
		self.signalReceivers = []

	def connect(self):
		Quodlibet.QuodlibetAPI.connect(self)
		try:
			proxy_obj1 = self.session_bus.get_object(self.ns, '/org/LyricsScreenlet')
			self.pluginAPI = dbus.Interface(proxy_obj1, "org.LyricsScreenlet")
			s1 = self.pluginAPI.connect_to_signal("onSongChange", self.onSongChangedSignal)
			s2 = self.playerAPI.connect_to_signal("Unpaused", self.onPlaySignal)
			s3 = self.playerAPI.connect_to_signal("Paused", self.onStopSignal)
			s4 = self.pluginAPI.connect_to_signal("onSeek", self.onSeekSignal)
			self.signalReceivers.append(s1)
			self.signalReceivers.append(s2)
			self.signalReceivers.append(s3)
			self.signalReceivers.append(s4)
		except Exception, e:
			print e
	
	def disconnect(self):
		for s in self.signalReceivers:
			s.remove()
		self.signalReceivers = []
		
	def onPlaySignal(self):
		if self.onPlay != None:
			self.onPlay()

	def onStopSignal(self):
		if self.onStop != None:
			self.onStop()
	
	def onSongChangedSignal(self, song):
		if self.onSongChanged != None:
			self.onSongChanged(song)
						
	def onSeekSignal(self, elapsed):
		if self.onElapsed != None:
			self.onElapsed(elapsed)
		
		
	def getCurrentFile(self):
		if self.pluginAPI != None:
			uri = self.pluginAPI.currentSong()
			#print "Quodlibet Currentfile %s" % uri
			return uri
		
	def getElapsed(self):
		return self.playerAPI.GetPosition()/1000.0
		
	def is_playing(self):
		#print "is_playing: %s" % self.playerAPI.IsPlaying()
		if self.playerAPI.IsPlaying() == 0:
			return False
		else:
			return True
