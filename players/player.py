#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


# must be before ListenPlayer import !

EVENTS_REFRESH_INTERVAL = 1000
class PlayerEvents:

	onSongChanged      = None
	onElapsed          = None
	onPlay             = None
	onStop             = None

	timer         = None	
	lastState     = None
	lastSong      = None
	lastTime      = 0
	
	def __init__(self, songChange = False, elapsedChange = False, stateChange = False):
		self.emitSongChangeEvents    = songChange
		self.emitElapsedChangeEvents = elapsedChange
		self.emitStateChangeEvents   = stateChange
		self.signalReceivers = []
		
	def connect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
		if self.emitSongChangeEvents or	self.emitElapsedChangeEvents or emitStateChangeEvents:
			self.timer = gobject.timeout_add(EVENTS_REFRESH_INTERVAL, self.checkForUpdate)
		self.lastSong = self.getCurrentFile()
		
	def registerOnSongChange(self, callback):
		self.onSongChanged = callback
			
	def registerOnElapsedChanged(self, callback):
		self.onElapsed = callback
			
	def registerOnPlay(self, callback):
		self.onPlay = callback
	
	def registerOnStop(self, callback):
		self.onStop = callback

	def disconnect(self):
		onSongChanged = None
		onElapsed     = None
		onPlay        = None
		onStop        = None
		
		if self.timer != None:
			gobject.source_remove(self.timer)
			
		for s in self.signalReceivers:
			s.remove()
		self.signalReceivers = []

		
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
		
import dbus
import gobject
import RhythmboxPlayer, ExailePlayer, ExailePlayer03, BansheePlayer, QuodlibetPlayer, AmarokDcopPlayer, ListenPlayer, GmusicbrowserPlayer #, mpd, XmmsPlayer
import mpris

PLAYER_LIST = ['RhythmboxPlayer', 'ExailePlayer', 'ExailePlayer03', 'BansheePlayer', 'QuodlibetPlayer', 'AmarokDcopPlayer', 'ListenPlayer', 'GmusicbrowserPlayer']#'XmmsPlayer', 'mpd']
REFRESH_INTERVAL = 2000

class Player(PlayerEvents):

	player_list        = None
	activePlayers      = None
	player             = None
	
	playerConnected    = None
	playerDisconnected = None
	is_connected       = False
	activePlayerListChangeCallback = None
	
	def __init__(self):
		PlayerEvents.__init__(self)
		self.player_list   = []
		self.activePlayers = []
		self.activePlayerListChangeCallback = []
		# D-Bus
		self.session_bus = dbus.SessionBus()
		self.dbus_object = self.session_bus.get_object ('org.freedesktop.DBus', '/org/freedesktop/DBus')
		self.dbus_iface = dbus.Interface(self.dbus_object, 'org.freedesktop.DBus')
		self.init_player_list()
		self.check_players_timer = gobject.timeout_add(REFRESH_INTERVAL, self.check_players)
		self.mprisPlayers = {}
		
	def getActivePlayers(self):
		return self.activePlayers
		
	def init_player_list(self):
		for player in PLAYER_LIST:
			try:
				#module = __import__("players."+player, fromlist=["players"])
				#self.player_list.append(eval('module.'+player+'(self.session_bus)'))
				self.player_list.append(eval('%s.%s(self.session_bus)' % (player, player)))
			except Exception, e:
				print "Could not load "+player+" API: " + str(e)
					
	def check_players(self):
	
		activePlayers = []

		for d in self.dbus_iface.ListNames():
			if d.startswith("org.mpris."):
				playerName = d[10:]
				if self.mprisPlayers.has_key(playerName):
					player = self.mprisPlayers[playerName]
				else:
					player = mpris.MprisApiPlayer(self.session_bus, d)
					player.__name__ = playerName
					self.mprisPlayers[playerName] = player
					self.player_list.append(player)
					print "NEW MPRIS PLAYER %s " % player
		
		for player in self.player_list:
			if player.is_active(self.dbus_iface):
				activePlayers.append(player)
		
		if len(activePlayers) == len(self.activePlayers):
			for p in activePlayers:
				if not p in self.activePlayers:
					for callback in self.activePlayerListChangeCallback:
						callback(activePlayers)
					break
		else:
			for callback in self.activePlayerListChangeCallback:
				callback(activePlayers)
				
				
		self.activePlayers = activePlayers
		if not self.player in activePlayers:
			self.disconnectActivePlayer()
		if self.player == None and len(self.activePlayers) > 0:
			try:
				self.connectPlayer(self.activePlayers[0])
			except: pass
		return True
		
		
		
		if self.player != None and self.player.is_active(self.dbus_iface):
			return True

		if self.player != None:
			self.player = None
			self.is_connected = False
			if self.playerDisconnected != None:
				self.playerDisconnected()
			
		# find first active player
		for player in self.player_list:
			if player.is_active(self.dbus_iface):
				player.connect()
				self.is_connected = True
				if self.onSongChanged != None:
					player.registerOnSongChange(self.onSongChanged)
				if self.onPlay != None:
					player.registerOnPlay(self.onPlay)
				if self.onStop != None:
					player.registerOnStop(self.onStop)
				if self.onElapsed != None:
					player.registerOnElapsedChanged(self.onElapsed)
				
				self.player = player
				if self.playerConnected != None:
					self.playerConnected()
					
				break
		return True
		
		
	def connectPlayer(self, player):
		#print "connect to %s" % player.__name__
		if player.is_active(self.dbus_iface):
			if self.player != None:
				wasPlaying = self.player.is_playing()
				wasSong    = self.player.getCurrentFile()
			else:
				wasPlaying = False
				wasSong    = None
					
			self.disconnectActivePlayer()
			player.connect()
			self.player = player
			
			self.is_connected = True
			if self.onSongChanged != None:
				player.registerOnSongChange(self.onSongChanged)
			if self.onPlay != None:
				player.registerOnPlay(self.onPlay)
			if self.onStop != None:
				player.registerOnStop(self.onStop)
			if self.onElapsed != None:
				player.registerOnElapsedChanged(self.onElapsed)
			
			# generate events
			isPlayingNow = player.is_playing()
			songNow      = player.getCurrentFile()
			#print "%s %s" % (isPlayingNow, songNow)
			if wasSong != songNow and self.onSongChanged != None:
				self.onSongChanged(songNow)
			# what is a chance that both players has the same elapsed time ? almost zero, so don't even test it
			if self.onElapsed != None:
				self.onElapsed(player.getElapsed())
			if wasPlaying != isPlayingNow:
				if isPlayingNow == True and self.onPlay != None:
					self.onPlay()
				if isPlayingNow == False and self.onStop != None:
					self.onStop()
				
			if self.playerConnected != None:
				self.playerConnected()
	
	def disconnectActivePlayer(self):
		if self.player != None:
			self.player.disconnect()
			self.player = None
			
	def registerOnActivePlayerListChange(self, callback):
		self.activePlayerListChangeCallback.append(callback)
		
	def registerOnSongChange(self, callback):
		PlayerEvents.registerOnSongChange(self, callback)
		#self.onSongChanged = callback
		if self.player != None:
			self.player.registerOnSongChange(self.onSongChanged)
			
	def registerOnElapsedChanged(self, callback):
		PlayerEvents.registerOnElapsedChanged(self, callback)
		#self.onElapsed = callback
		if self.player != None:
			self.player.registerOnElapsedChanged(self.onElapsed)
			
	def registerOnPlay(self, callback):
		PlayerEvents.registerOnPlay(self, callback)
		#self.onPlay = callback
		if self.player != None:
			self.player.registerOnPlay(self.onPlay)
			
	def registerOnStop(self, callback):
		PlayerEvents.registerOnStop(self, callback)
		#self.onStop = callback
		if self.player != None:
			self.player.registerOnStop(self.onStop)
			
	def getCurrentSong(self):
		if self.player != None:
			return self.player.getCurrentFile()
			
	def getElapsed(self):
		if self.player != None:
			return self.player.getElapsed()
			
	def is_playing(self):
		if self.player != None:
			return self.player.is_playing()
			
	def registerOnPlayerConnected(self, callback):
		self.playerConnected = callback
		
	def registerOnPlayerDisconnected(self, callback):
		self.playerDisconnected = callback
			
	def getPlayerName(self):
		if self.player != None:
			return self.player.__name__
	
	def getTitle(self):
		return self.player.get_title()
	
	def getArtist(self):
		return self.player.get_artist()
	
	def getAlbum(self):
		return self.player.get_album()
	
	def getMetadata(self):
		pass
