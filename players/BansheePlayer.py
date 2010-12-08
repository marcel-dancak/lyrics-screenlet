from screenlets.plugins import Banshee
import utils
from player import PlayerEvents

class BansheePlayer(Banshee.BansheeAPI, PlayerEvents):
	
	def __init__(self, session_bus):
		Banshee.BansheeAPI.__init__(self, session_bus)
		PlayerEvents.__init__(self)
		self.__name__ = "Banshee"
	
	def connect(self):
		Banshee.BansheeAPI.connect(self)
		s1 = self.playerAPI.connect_to_signal("StateChanged", self.stateChanged)
		s2 = self.playerAPI.connect_to_signal("EventChanged", self.eventChanged)
		self.signalReceivers.append(s1)
		self.signalReceivers.append(s2)
		
	
	def stateChanged(self, state):
		if state == 'playing':
			if self.onPlay != None:
				self.onPlay()
		elif state == 'paused':
			if self.onStop != None:
				self.onStop()
		
	def eventChanged(self, event, par2, par3):
		if event != 'statechange':
			if event == 'seek':
				if self.onElapsed != None:
					self.onElapsed(self.getElapsed())
			elif event == 'startofstream':
				if self.onSongChanged != None:
					self.onSongChanged(self.getCurrentFile())

				
	def getElapsed(self):
		elapsed = self.playerAPI.GetPosition()/1000.0
		# GetPosition() sometimes return 0, even if real position is different, so try to eliminate it
		if elapsed == 0:
			return self.playerAPI.GetPosition()/1000.0
		return elapsed
		
	def getCurrentFile(self):
		uri = self.playerAPI.GetCurrentUri()
		return utils.get_local_path_from_uri(uri)
		

