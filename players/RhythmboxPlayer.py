import screenlets
#import gnomevfs
import utils
from screenlets.plugins import Rhythmbox
from player import PlayerEvents

class RhythmboxPlayer(Rhythmbox.RhythmboxAPI, PlayerEvents):
	
	lastTime        = None
	radioMode       = False
	
	def __init__(self, session_bus):
		Rhythmbox.RhythmboxAPI.__init__(self, session_bus)
		PlayerEvents.__init__(self)
	
	def connect(self):
		Rhythmbox.RhythmboxAPI.connect(self)
		s1 = self.playerAPI.connect_to_signal("playingChanged", self.playingChangedSignal)
		s2 = self.playerAPI.connect_to_signal("playingUriChanged", self.songChangedSignal)
		s3 = self.playerAPI.connect_to_signal("elapsedChanged", self.elapsedSignal)
		
		# add to signalReceivers, to be automaticaly removed on disconnection
		self.signalReceivers.append(s1)
		self.signalReceivers.append(s2)
		self.signalReceivers.append(s3)
		
		
	def playingChangedSignal(self, flag):
		if flag and self.onPlay != None:
			self.onPlay()
		if not flag and self.onStop != None:
			self.onStop()
		
	def songChangedSignal(self, uri):
		print "RHYTHMBOX SONG CHANGED"
		if uri.startswith("http") and self.getElapsed() > 10:
			self.switch_to_radio_mode()
		if uri:
			self.onSongChanged(utils.get_local_path_from_uri(uri))
			self.lastTime = None

		
	def elapsedSignal(self, elapsed):
		# filter rhythmbox elapsed signal during normal playing
		#print str(elapsed) +' '+ str(self.lastTime)
		if self.lastTime == None or (elapsed - self.lastTime) not in range(-1,2):
			#print "last: %s now: %s diff: %s" % (elapsed, self.lastTime, (elapsed - self.lastTime))
			print "Rhythmbox API seek: %s" % elapsed
			self.onElapsed(elapsed)
		self.lastTime = elapsed
	
	def getElapsed(self):
		try:
			return self.playerAPI.getElapsed()
		except:
			return 0

	def getCurrentFile(self):
		uri = self.playerAPI.getPlayingUri()
		if uri.startswith("http"):
			self.switch_to_radio_mode()
			print "use title: %s" % self.get_title()
			return self.get_title()
		return utils.get_local_path_from_uri(uri)
		
	def switch_to_radio_mode(self):
		print "SHOULD SWITCH TO RADIO MODE"
		"""
		if not self.radioMode:
			self.radioMode = True
			self.emitSongChangeEvents = True
			PlayerEvents.connect(self)
		"""
			
