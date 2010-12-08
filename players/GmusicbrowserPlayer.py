import dbus
from player import PlayerEvents

class GmusicbrowserPlayer(PlayerEvents):
	__name__ = "gmusicbrowser"
	
	def __init__(self, session_bus):
		PlayerEvents.__init__(self, songChange = False, elapsedChange = True, stateChange = True)
		self.session_bus = session_bus
	
	def is_active(self, dbus_iface):
		return "org.gmusicbrowser" in dbus_iface.ListNames()
		
	def connect(self):
		proxy = self.session_bus.get_object("org.gmusicbrowser", "/org/gmusicbrowser")
		self.playerAPI = dbus.Interface(proxy, "org.gmusicbrowser")
		self.playerAPI.connect_to_signal("SongChanged", self.onSongChangedSignal)
		PlayerEvents.connect(self)
	
	def disconnect(self):
		PlayerEvents.disconnect(self)

	def onSongChangedSignal(self, song):
		#print "SONG CHANGE %s" % song
		if self.onSongChanged:
			self.onSongChanged(self.getCurrentFile())
		
	def get_title(self):
		return self.playerAPI.CurrentSong()['title']

	def get_artist(self):
		return self.playerAPI.CurrentSong()['artist']

	def get_album(self):
		return self.playerAPI.CurrentSong()['album']
				
	def getElapsed(self):
		return self.playerAPI.GetPosition()
	
	def getCurrentFile(self):
		print "FILE"
		#print self.playerAPI.CurrentSong()
		#print self.playerAPI.GetLibrary()
		#print self.playerAPI.Get(["0"], 'length')
		return "http"
		 
	def is_playing(self):
		return self.playerAPI.Playing() == 1
