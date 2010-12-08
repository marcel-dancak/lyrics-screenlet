#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


import dbus
import utils
import gobject
from player import PlayerEvents

REFRESH_INTERVAL = 1000

class ListenPlayer(PlayerEvents):
	
	__name__     = "Listen"
	session_bus  = None
	playerAPI    = None
	timer        = None
	lastSong     = None
	lastState    = None
	lastTime     = 0
	
	def __init__(self, session_bus):
		self.session_bus = session_bus
	
	def is_active(self, dbus_iface):
		return "org.gnome.Listen" in dbus_iface.ListNames()

	def connect(self):
		proxy = self.session_bus.get_object("org.gnome.Listen", "/org/gnome/listen")
		self.playerAPI = dbus.Interface(proxy, "org.gnome.Listen")
		if self.timer != None:
			gobject.source_remove(self.timer)
		self.timer = gobject.timeout_add(REFRESH_INTERVAL, self.refresh)
		self.lastSong = self.getCurrentFile()

	def disconnect(self):
		PlayerEvents.disconnect(self)
		if self.timer != None:
			gobject.source_remove(self.timer)
			
	def getCurrentFile(self):
		uri = self.playerAPI.get_uri()
		return utils.get_local_path_from_uri(uri)
		
	def get_title(self):
		return self.playerAPI.get_title()

	def get_artist(self):
		return self.playerAPI.get_artist()

	def get_album(self):
		return self.playerAPI.get_album()

	def is_playing(self):
		return self.playerAPI.current_playing() != ""

	def getElapsed(self):
		return self.playerAPI.current_position()

	def refresh(self):
		try:
			# song change events
			if self.onSongChanged != None:
				playing_song = self.playerAPI.get_uri()
				if playing_song != "":
					if playing_song != self.lastSong:
						self.onSongChanged(utils.get_local_path_from_uri(playing_song))
					self.lastSong = playing_song
		
			# elapsed events
			if self.onElapsed:				
				elapsed = self.getElapsed()
				if elapsed-self.lastTime not in range (0,3):
					#print str(elapsed) +' '+str(self.lastTime)
					self.onElapsed(elapsed)
				self.lastTime = elapsed	
		
			# play/stop events
			state = "play" if self.is_playing() else "stop"
			if (state != self.lastState):
				if state == "play" and self.onPlay != None:
					self.onPlay()
				if state == "stop" and self.onStop != None:
					self.onStop()
				self.lastState = state

			return True
		except Exception, e:
			print e
			return False
