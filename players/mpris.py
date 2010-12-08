import dbus
import gobject
import utils

from player import PlayerEvents

DELAY = 1000

class MprisApiPlayer(PlayerEvents):

	timer          = None
	lastStatus     = None
	lastTime	   = 0
	
	session_bus    = None
	dbus_ns        = None
	dbus_iface     = None
	
	def __init__(self, session_bus, dbus_ns):
		PlayerEvents.__init__(self)
		self.session_bus    = session_bus
		self.dbus_ns = dbus_ns
		
		self.session_bus = dbus.SessionBus()
		self.dbus_object = self.session_bus.get_object ('org.freedesktop.DBus', '/org/freedesktop/DBus')
		self.dbus_iface = dbus.Interface(self.dbus_object, 'org.freedesktop.DBus')
		
	def _is_active(self):
		return self.dbus_ns in self.dbus_iface.ListNames()
		
	def is_active(self, dbus_iface):
		return self.dbus_ns in dbus_iface.ListNames()
		
	def connect(self):
		print "connect"
		player_proxy_obj    = self.session_bus.get_object(self.dbus_ns, "/Player")
		tracklist_proxy_obj = self.session_bus.get_object(self.dbus_ns, "/TrackList")
		self.playerAPI      = dbus.Interface(player_proxy_obj,    "org.freedesktop.MediaPlayer")
		self.tracklistAPI   = dbus.Interface(tracklist_proxy_obj, "org.freedesktop.MediaPlayer")
		print "signals"
		#self.playerAPI.connect_to_signal("CapsChange", self.onCapabilitiesChange)
		s1 = self.playerAPI.connect_to_signal("StatusChange", self.onStatusChange)
		s2 = self.playerAPI.connect_to_signal("TrackChange", self.onTrackChange)
		self.signalReceivers.append(s1)
		self.signalReceivers.append(s2)
		
		if self.timer != None:
			gobject.source_remove(self.timer)
		self.timer = gobject.timeout_add(DELAY, self.checkForUpdate)
		
	
	def disconnect(self):
		PlayerEvents.disconnect(self)
		if self.timer != None:
			gobject.source_remove(self.timer)
		
	def is_playing(self):
		print "is_playing"
		try:
			status = self.playerAPI.GetStatus()
			if isinstance(status, int):  # again, audacious breaking mpris API
				return status == 0
			return status[0] == 0
		except:
			return True
	
	def onTrackChange(self, metadata):
		path = self.getCurrentFromMetadata(metadata)
		self.onSongChanged(path)
	
	#def onCapabilitiesChange(self, arg):
	#	print "capabilitiesChange: %s" % arg
	
	def onStatusChange(self, status):
		if status == self.lastStatus:
			return
		self.lastStatus = status
		
		if isinstance(status, int):
			state = status
		elif isinstance(status, dbus.Struct):
			state = status[0]
		else:
			print "Another player breaking mpris API ?"
			
		if state == 0 and self.onPlay != None:
			self.onPlay()
		if (state == 1 or state == 2) and self.onStop != None:
			self.onStop()
		
	
	def getElapsed(self):
		print "get elapsed"
		try:
			return self.playerAPI.PositionGet()/1000.0
		except Exception, e:
			print "Can't get elapsed time information from MPRIS API: %s" % e
			return 0.0

	def getCurrentFromMetadata(self, metadata):
		try:
			metadata = self.playerAPI.GetMetadata()
		except:
			print "Error getting player metadata"
			return None
		if metadata.has_key('location'):
			uri = metadata['location']
		elif metadata.has_key('URI'):
			uri = metadata['URI'] # audacious want be unique
		else:
			print "Can't get current song info from MPRIS API"
			return
		return utils.get_local_path_from_uri(uri)
		
	def getCurrentFile(self):
		return self.getCurrentFromMetadata(self.playerAPI.GetMetadata())
		
		
	def checkForUpdate(self):
		if not self._is_active():
			return False
		try:
			if self.onElapsed:
				elapsed = self.getElapsed()
				if elapsed-self.lastTime > 2 or elapsed-self.lastTime < 0:
					self.onElapsed(elapsed)
				self.lastTime = elapsed	
		except: # if player was disconnected or so
			return False
		return True

	def get_title(self):
		metadata = self.playerAPI.GetMetadata()
		if metadata.has_key('title'):
			return metadata['title']
		return ""

	def get_artist(self):
		metadata = self.playerAPI.GetMetadata()
		if metadata.has_key('artist'):
			return metadata['artist']
		return ""

	def get_album(self):
		metadata = self.playerAPI.GetMetadata()
		if metadata.has_key('album'):
			return metadata['album']
		return ""
