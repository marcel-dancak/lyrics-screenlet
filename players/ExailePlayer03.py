#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


import dbus
import gobject
import re
from player import PlayerEvents

elapsed_regex = re.compile('(?P<min>\d(\d)?):(?P<sec>\d\d)') # ([d(d)?:dd])
REFRESH_INTERVAL = 1000

class ExailePlayer03(PlayerEvents):
	
	__name__     = "Exaile 0.3"
	timer        = None
	lastTime     = 0
	wasPlaying   = False
	
	def __init__(self, session_bus):
		self.session_bus = session_bus
		
	def is_active(self, dbus_iface):
		return "org.exaile.Exaile" in dbus_iface.ListNames()
		
	def connect(self):
		proxy = self.session_bus.get_object("org.exaile.Exaile", "/org/exaile/Exaile")
		self.playerAPI = dbus.Interface(proxy, "org.exaile.Exaile")
		if self.timer != None:
			gobject.source_remove(self.timer)
		self.timer = gobject.timeout_add(REFRESH_INTERVAL, self.refresh)
		self.lastSong = self.getCurrentFile()

	def disconnect(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
			
	def is_playing(self):
		status = self.playerAPI.Query()
		s = status.find(':')
		e = status.find(',')
		if s != -1 and e != -1:
			return status[s+1:e].strip() == 'playing'
		return False
		
	
	def get_title(self):
		return self.playerAPI.GetTrackAttr('title')
	
	def get_artist(self):
		return self.playerAPI.GetTrackAttr('artist')
	
	def get_album(self):
		return self.playerAPI.GetTrackAttr('album')
		
	def getElapsed(self):
		if self.is_playing():
			elapsedString = self.playerAPI.CurrentPosition()
			match = elapsed_regex.match(elapsedString)
			if match:
				return 60*int(match.group('min'))+int(match.group('sec'))
		return 0

	def getCurrentFile(self):
		filename = self.playerAPI.GetTrackAttr('__loc')
		if filename != '':
			return filename


	def refresh(self):
		try:
			#print "refresh"
			# song change events
			if self.onSongChanged:
				playing_song = self.getCurrentFile()
				if playing_song != self.lastSong:
					if self.onSongChanged != None:
						self.onSongChanged(playing_song)
				self.lastSong = playing_song
		
			# elapsed events
			if self.onElapsed:				
				elapsed = self.getElapsed()
				if elapsed-self.lastTime not in range (0,3):
					#print str(elapsed) +' '+str(self.lastTime)
					self.onElapsed(elapsed)
				self.lastTime = elapsed	
		
			# play/stop events
			#print "is  %s" % self.is_playing()
			#print "was %s" % self.wasPlaying
			
			if self.is_playing() and self.wasPlaying == False and self.onPlay != None:
				self.onPlay()
			if not self.is_playing() and self.wasPlaying == True and self.onStop != None:
				self.onStop()
				
			self.wasPlaying = self.is_playing()
			return True

		except Exception, e:
			print e
			return False
				
