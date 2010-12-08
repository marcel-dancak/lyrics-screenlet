#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


from plugins.events import EventPlugin
import dbus
import dbus.service


class MyPlugin(EventPlugin, dbus.service.Object):
	PLUGIN_ID = "LyricsScreenlet Informator"
	PLUGIN_NAME = _("LyricsScreenlet Informator")
	PLUGIN_VERSION = "1.0"
	PLUGIN_DESC = ("Extends default dbus interface, especialy to LyricsScreenlet communication.")
	
	song = None
		
	def __init__(self):
		EventPlugin.__init__(self)
		try:
			bus = dbus.SessionBus()
			name = dbus.service.BusName('org.LyricsScreenlet', bus=bus)
			path = '/org/LyricsScreenlet'
			dbus.service.Object.__init__(self, name, path)
		except Exception, e:
			print e
			pass
		
	@dbus.service.signal('org.LyricsScreenlet')
	def onSongChange(self, song):
		pass
		
	@dbus.service.signal('org.LyricsScreenlet')
	def onSeek(self, seek):
		pass
		
	@dbus.service.method('org.LyricsScreenlet')
	def currentSong(self):
		return self.song
		
	def plugin_on_song_started(self, song):
		#print "plugin: %s" % song
		#print "song: %s" % song._song['~filename']
		self.song = song._song['~filename']
		self.onSongChange(self.song)
		
	def plugin_on_seek(self, song, msec):
		#print "plugin seek: %s" % msec
		self.onSeek(msec/1000.0)
		
