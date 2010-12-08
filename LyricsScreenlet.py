#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


import logging
logging.basicConfig()
log = logging.getLogger("LyricsScreenlet")
log.setLevel(logging.DEBUG)

import screenlets
from screenlets.options import FloatOption, BoolOption, DirectoryOption, ColorOption, FontOption, StringOption
import cairo
import pango
import gobject
from os import path
import os
import sys
import gtk
import re
import traceback

from lyricsengine.engine import LyricsEngine
from lyricsengine import ALSong

from LyricsAnimation import LyricsAnimation
from LyricsPanel import *
from players import player
import animation

from xgoogle.translate import Translator
from xgoogle.translate import LanguageDetector

from xgoogle.translate import _languages
languages = {}
for k,v in _languages.iteritems():
	languages[v] = k

text_aligns = {'Center' : ALIGN_CENTER, 'Left' : ALIGN_LEFT, 'Right' : ALIGN_RIGHT}
# C module
#import cLyricsEngine

try:
	import socket
	socket.setdefaulttimeout(60)
except:
	pass


LYRICS_NOT_FOUND = Lyrics([LyricEntity(['lyrics not found'], 0)])

#import widget
class LyricsScreenlet(screenlets.Screenlet):#Widget
	# default meta-info for Screenlets
	__name__    = 'Lyrics Screenlet'
	__version__ = '0.7.1'
	__author__  = 'Marcel Dancak'
	__desc__    = 'Shows lyrics of the linux audio players'
	
	invisible          = False
	maximized          = None
	maxi_width		   = 300
	maxi_height        = 155
	state              = None
	player	           = None
	playing			   = False
	songInfo		   = None
	lyricsPanel		   = None
	autoHideTimer	   = None
	autoColorTimer     = None
	
	lyricsList         = None
	lyrics_index       = 0 
	
	install_path       = None
	lyrics_directory   = os.environ['HOME']
	saveFirstLyrics    = False # save flag for addlyrics
	save_lyrics        = False
	dirOption          = None
	filter_cjk         = True
	autoColorAdapt     = False
	autoPanelHide      = True
	colorAdaptation    = 'None'
	textAlign          = 'Center'
	translation_enabled = False
	language           = None
	
	# graphics, forwarded to LyricsPanel
	text_scale      = None
	font            = "sans 9"
	color_normal    = None
	color_highlight = None
	
	canvas          = None
	dimensions      = None
	#controlPanel 	= None
	minimizeToTray  = False
	trayIcon        = None
	safe_minimize   = True
	
	# constructor
	def __init__(self, **keyword_args):

		#call super (and not show window yet)
		screenlets.Screenlet.__init__(self, uses_theme=True, width=64, height=64, drag_drop=True, **keyword_args)
		self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
		self.translateMenuItem = gtk.CheckMenuItem("Google Translate")
		self.translateMenuItem.connect("activate", lambda item: self.__setattr__('translation_enabled', item.get_active()))
		self.translateMenuItem.show()

		#print dir(self.window.get_screen())
		#print self.window.get_screen().is_composited()
		#print self.window.get_screen().get_rgba_colormap()
		
		self.lyricsPanel = LyricsPanel()
		#self.lyricsPanel = LyricsAnimation()

		# path to screenlet installation directory
		self.install_path = path.dirname(path.abspath(__file__)) + os.sep	
		sys.path.append(self.install_path)
		
		# Options
		self.add_options_group('Lyrics', 'Lyrics settings')
		self.add_option(FontOption ('Lyrics', 'font', self.font, 'Font', 'The font of lyrics'))
		self.add_option(ColorOption('Lyrics', 'color_normal', self.color_normal, 'Normal Color', 'Color of the common text'))
		self.add_option(ColorOption('Lyrics', 'color_highlight', self.color_highlight, 'Highlight Color', 'Color of the actual line'))
		self.add_option(StringOption('Lyrics', 'colorAdaptation', self.colorAdaptation, 'Color Adaptation', 'Lyrics text color adaptation by background', choices = ['None', 'Inverse', 'Black or White']))
		self.add_option(FloatOption('Lyrics', 'text_scale', self.text_scale, 'Text Scale', 'Maximum scale of the highlighted text', min=1, max=2, increment=0.05, digits=2))
		self.add_option(StringOption('Lyrics', 'textAlign', self.textAlign, 'Text Align', 'Lyrics text align', choices = sorted(text_aligns)))
		
		self.add_option(BoolOption('Lyrics', 'save_lyrics', self.save_lyrics, 'Save lyrics', 'Allow saving downloaded lyrics to the selected directory'))
		self.dirOption = DirectoryOption('Lyrics', 'lyrics_directory', self.lyrics_directory, 'Lyrics Directory', 'Directory, where will be downloaded lyrics saved')
		self.add_option(self.dirOption)
		self.add_option(BoolOption('Lyrics', 'filter_cjk', self.filter_cjk, 'Filter some languages', 
			'Filter Chinese, Japanese, Korean languages (maybe more), which may cause troubles with scaling text during animation '))
		
		self.add_option(BoolOption('Lyrics', 'autoPanelHide', self.autoPanelHide, 'Hiding Control panel', 'Hide Control panel when window loose focus'))
		self.add_option(BoolOption('Lyrics', 'minimizeToTray', self.minimizeToTray, 'Use Tray Icon', 'Use Tray Icon'))
		self.add_option(BoolOption('Lyrics', 'safe_minimize', self.safe_minimize, 'Safe minimizing', 'Use safe minimizing without real window resizing'))
		
		
		self.add_options_group('Google Translate', 'Google Translate settings')
		self.add_option(BoolOption('Google Translate', 'translation_enabled', self.translation_enabled, 'Enabled', 'Google Translate'))
		self.add_option(StringOption('Google Translate', 'language', self.language, 'Language', 'Language', choices = sorted(languages)))
		
		
		self.lyricsEngine = LyricsEngine(self.addLyrics, self.onEngineFinish)
		self.lyricsEngine.setLyricsSources(['alsong', 'minilyrics', 'lrcdb', 'lyricsscreenlet'])
		#self.lyricsEngine.setLyricsSources(['lyricsscreenlet'])
		
		self.player = player.Player()
		self.xmmsPlayer = None
		for p in self.player.player_list:
			if p.__name__ == "xmms":
				self.xmmsPlayer = p
		self.player.registerOnSongChange(self.onSongChanged)
		self.player.registerOnPlay(self.onPlay)
		self.player.registerOnStop(self.onStop)
		self.player.registerOnElapsedChanged(self.onElapsed)
		self.player.registerOnPlayerConnected(self.onPlayerConnected)
		self.player.registerOnPlayerDisconnected(self.onPlayerDisconnected)
		self.player.registerOnActivePlayerListChange(self.onPlayerListChange)
		
		
		self.disconn = ImageButton('disconnected', 'disconnected')
		self.disconn.registerEvent('button_pressed', self.on_minimized_pressed)
		self.disconn.registerEvent('button_pressed', self.lyricsPanel_pressed) # moving screenlet
		self.disconn.registerEvent('resized', self.on_minimized_resized)
		self.disconn.setPosition(0, 0)
		self.disconn.setVisible(False)
		self.disconn.rectangleBounds = True # better for transparent images/themes
		
		templateAnim = Animation(100, 6)
		templateAnim.addLinearTransition('setOverAlpha', 0.0, 1.0, LINEAR)
		templateAnim.addTransition('scale', LinearVectorInterpolator([1.0, 1.0], [1.4, 1.4]), LINEAR)
				
		pressedAnim = Animation(4, 20)
		pressedAnim.addTransition('scale', LinearVectorInterpolator([1.4, 1.4], [1.25, 1.25]), LINEAR)
		
		self.next = ImageButton('next', 'next_over')
		self.next.registerEvent('button_pressed', self.nextLyrics)
		self.next.setEnterAnimation(templateAnim.create(self.next))
		self.next.setPressedAnimation(pressedAnim.create(self.next))
		
		self.prev = ImageButton('prev', 'prev_over')
		self.prev.registerEvent('button_pressed', self.previousLyrics)
		self.prev.setEnterAnimation(templateAnim.create(self.prev))
		self.prev.setPressedAnimation(pressedAnim.create(self.prev))
		
		self.save = ImageButton('harddisk', 'harddisk')
		self.save.registerEvent('button_pressed', self.saveButtonPressed)
		self.save.setEnterAnimation(templateAnim.create(self.save))
		self.save.setEnabled(self.save_lyrics)
		
		self.search = ImageButton('search', 'search')
		self.search.registerEvent('button_pressed', self.onSearchClicked)
		self.search.setEnterAnimation(templateAnim.create(self.search))
		
		self.upload = ImageButton('upload', 'upload')
		self.upload.registerEvent('button_pressed', self.uploadButtonPressed)
		self.upload.setEnterAnimation(templateAnim.create(self.upload))
		
		self.invisibleButton = ImageButton('bubak', 'bubak')
		self.invisibleButton.visibilityThreshold = 50 # more transparent icon is planned for this
		self.invisibleButton.registerEvent('button_pressed', self.invisible_pressed)
		
		self.notifier = Label('Uploaded ', fixedSize = False)
		self.notifier.bgColor = [0.7, 0.4, 0.4, 0.8]
		self.notifier.setVisible(False)
		self.notifier.animation = animation.CompositeAnimation(10, 500)
		self.notifier.animation.addTransition(self.notifier.__setattr__, animation.LinearScalarInterpolator(1.0, 0.0), 'alpha')
		self.notifier.animation.addTaskOnFinish(self.notifier.setVisible, False)
		self.notifier.animation.startupDelay = 2000
		
		self.label = Label('1 of 1', fixedSize = True)
		prefSize = self.label.getPrefferedSize()
		self.label.setSize(40, prefSize[1]+6)
		self.label.align = Label.CENTER

		# component for resizing screenlet
		self.resize = ImageButton('resize', 'resize')
		self.resize.registerEvent('button_pressed', self.onResizeStart)
		self.resize.registerEvent('mouse_drag_motion', self.onResize)
		self.resize.registerEvent('button_released', self.do_resize)
		
		self.lyricsPanel.setPosition(0, 0)
		self.lyricsPanel.registerEvent('button_pressed', self.lyricsPanel_pressed)
		
		self.searching = ImageButton('searching_bg', 'searching_bg')
		self.searching_arrow = ImageButton('searching_glow', 'searching_glow')
		self.searching.addWidget(self.searching_arrow)
		self.searching.animation = animation.CompositeAnimation(20, 800, loop = True)
		self.searching.animation.addTransition(self.searching_arrow.__setattr__, animation.LinearScalarInterpolator(0.0, 6.29), 'rotation')
		self.searching.setVisible(False)
		
		#"""
		from gui.cairo_widgets import CairoCanvas
		#from gui.ls_widget import VirtualCanvas
		self.canvas = CairoCanvas(self.window)
		#self.canvas = VirtualCanvas(self.window)
		
		self.canvas.addWidget(self.lyricsPanel)
		self.canvas.addWidget(self.notifier)
		self.canvas.addWidget(self.searching)
		self.canvas.addWidget(self.resize)
		self.canvas.addWidget(self.disconn)
		self.canvas.addWidget(self.invisibleButton)
		
		self.playersDropDown = DropDownList(['Not Connected'])
		self.playersDropDown.registerItemSelected(self.activePlayerChanged)
		self.playersDropDown.setSize(100, 20)
		
		self.controlPanel = Widget()
		
		self.controlPanel.addWidget(self.next)
		self.controlPanel.addWidget(self.label)
		self.controlPanel.addWidget(self.prev)
		self.controlPanel.addWidget(self.search)
		self.controlPanel.addWidget(self.save)
		self.controlPanel.addWidget(self.upload)
		
		tf = TextField(100, 30, "heloo")
		#self.canvas.addWidget(tf)
		self.canvas.addWidget(self.controlPanel)
		self.canvas.addWidget(self.playersDropDown)
		
		# set theme
		self.theme_name = 'default'
		self.updateWidgetPositions(self.width, self.height)	

	def translate_callback(self, arg):
		print arg
		print arg.get_active()
	# attribute-"setter", handles setting of attributes
	def __setattr__(self, name, value):
		#if name == 'text_scale' or name == 'font' or name == 'color_highlight' or name == 'color_normal':
		#	print name + ': '+str(value)
		if name == 'colorAdaptation':
			if value == 'None':
				if self.autoColorTimer != None:
					gobject.source_remove(self.autoColorTimer)
					self.autoColorTimer = None
				self.colorAnimation(self.color_normal, self.color_highlight)
			elif self.autoColorTimer == None:
					self.autoColorTimer = gobject.timeout_add(1000, self.doColorAdaptation)
					
		# forward options to LyricsPanel
		if name in ['color_normal', 'color_highlight', 'text_scale', 'theme', 'textAlign']:
			if name == 'textAlign':
				
				self.lyricsPanel.__setattr__(name, text_aligns[value])
			else:
				self.lyricsPanel.__setattr__(name, value)
		if name == 'font' and isinstance(value, str):
			self.lyricsPanel.setFont(pango.FontDescription(value))
			
		if name == 'lyrics_directory':
			if isinstance(value, bool):
				return

		if name == 'save_lyrics':
			self.save.setEnabled(value)
		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
				# forward value to canvas
		if name == 'scale' and self.canvas != None:
			self.canvas.scale = value
		
		screenlets.Screenlet.__setattr__(self, name, value)
		
		if name == 'theme_name':
			#print "THEME CHANGED %s" % value
			self.onThemeChanged(self.theme)
		
		if (name == 'width' or name == 'height') and self.canvas != None:
			self.updateWidgetPositions(self.width, self.height)
		
		if name in [ "playing"]:
			print "UPDATE STATE %s = %s" % (name, value)
			#self.updateState()
	
		if name == 'minimizeToTray':
			if value == True:
				if self.trayIcon == None:
					self.trayIcon = gtk.StatusIcon()
					trayIconImage = os.path.dirname(os.path.abspath(__file__)) + os.sep + "tray.png"
					self.trayIcon.set_from_file(trayIconImage)
					self.trayIcon.set_tooltip("yep, even screenlets can have tray icon :D") 
					self.trayIcon.connect('activate', self.tray_activate)
				else:
					self.trayIcon.set_visible(True)
			if value == False and self.trayIcon:
				self.trayIcon.set_visible(False)
		
		if name == 'language':
			if self.lyricsList != None:
				self.setLyricsIndex(self.lyrics_index)
		if name == 'translation_enabled':
			print "\tGOOGLE TRANSLATE: %s" % (self.translation_enabled)
			self.translateMenuItem.set_active(value)
			if self.lyricsList != None:
				self.setLyricsIndex(self.lyrics_index)

	def on_init (self):
		log.info("Screenlet has been initialized.")
		# add default menuitems
		#self.add_menuitem("translation", "Google Translate")
		
		self.menu.append(self.translateMenuItem)
		self.add_default_menuitems()
		
		self.state = self.load_option('state')
		if self.state == None:
			self.state = 'minimized' # default state
			self.session.backend.save_option(self.id, 'state', self.state)
		log.debug("MINIMIZING Startup state: %s" % self.state)
		
		width  = self.load_option('maxi_width' )
		height = self.load_option('maxi_height')
		if (width != None and height != None):
			self.maxi_width  = int(width )
			self.maxi_height = int(height)
		log.debug("MINIMIZING Initialized maximized dimensions: width=%d height=%d" % (self.maxi_width, self.maxi_height))
			
		self.minimize("disconnected")
		
		
	def tray_activate(self, widget):
		if self.state == 'minimized':
			self.maximize()
		else:
			self.minimize()
			
	def on_menuitem_select(self, item):
		print item

	def on_minimized_resized(self, width, height):
		print "on_minimized_resized: w=%d h=%d" % (width, height)
		if self.state == 'minimized' and not self.safe_minimize:
			self.width  = width
			self.height = height
			#self.canvas.setSize(width, height)
			#self.update_shape()

	def on_minimized_pressed(self, widget, event):
		if event.type == gtk.gdk._2BUTTON_PRESS:
			self.maximize()
		
	def pack(self, widget):
		screen = self.window.get_screen()
		log.debug("MINIMIZING Compute minimized layout")
		log.debug("MINIMIZING Screen: width=%d height=%d" % (screen.get_width(), screen.get_height()))
		log.debug("MINIMIZING Maximized dimmensions: width=%d height=%d" % (self.maxi_width, self.maxi_height))
		#print "x=%s  y=%s width=%s" % (self.x, self.y, self.maxi_width)
		left = self.x
		right = screen.get_width() - (left + self.maxi_width)
		up = self.y
		bottom = screen.get_height() - (up + self.maxi_height)
		#print "PACK LEFT=%s  RIGHT=%s" % (left, right)
		
		ml = (left/float(left+right))*(self.maxi_width-widget.bounds.width)
		#mr = (1.0-(left/float(left+right)))*(self.maxi_width-widget.bounds.width)
		#print "%s vs %s" % (ml, mr)
		mu = (up/float(up+bottom))*(self.maxi_height-widget.bounds.height)
		
		#print "offset  x=%s  y=%s" % (ml, mu)
		return [ml, mu]
		
	def expand(self, widget, width, height):
		screen = self.window.get_screen()
		
		screenWidth  = screen.get_width()
		screenHeight = screen.get_height()
		#print "prev x=%s widget.bounds.x=%s" % (self.x, widget.bounds.x)
		prevX = self.x + widget.bounds.x
		prevY = self.y + widget.bounds.y

		left = prevX
		right = screenWidth - (prevX+widget.bounds.width)
		up = prevY
		bottom = screenHeight - (prevY+widget.bounds.height)
		#print "LEFT=%s  RIGHT=%s" % (left, right)
		#print "right/left %s" % (right/float(left+right))
		#print "MOVE LEFT %s" % ((1.0-right/float(left+right))*(width-widget.bounds.width))
		#print "MOVE RIGHT %s" % (right/float(left+right)*(width-widget.bounds.width))
		
		#left*ratio + right*ratio = width
		ratioH = width/float(left+right)
		ratioV = height/float(up+bottom)

		#left*r + right*r = widget.bounds.width
		rh = widget.bounds.width/float(left+right)
		rv = widget.bounds.height/float(up+bottom)

		newX = int(prevX+rh*left-ratioH*left)
		newY = int(prevY+rv*up-ratioV*up)
		
		new = [int(prevX-(1.0-right/float(left+right))*(width-widget.bounds.width))]
		#print "%s vs %s" % (new, newX)
		
		return [newX, newY]
		
	def load_option(self, name):
		if self.session != None:
			try:
				return self.session.backend.load_option(self.id, name)
			except Exception, e:
				pass
					
	def activePlayerChanged(self, playerName):
		if self.player.getPlayerName() == playerName:
			return
			
		log.debug("Should connect to %s player" % playerName)
		for player in self.player.getActivePlayers():
			if player.__name__ == playerName:
				self.lyricsPanel.stopAnimation()
				self.lyricsPanel.setLyrics(None)
				self.lyricsList = []
				self.player.connectPlayer(player)
				break
		
	def onPlayerListChange(self, players):
		playerNames = []
		for player in players:
			playerNames.append(player.__name__)
			
		#print playerNames
		self.playersDropDown.setItems(playerNames)
		if len(players) == 0:
			self.onPlayerDisconnected()
		
	def addLyrics(self, lyrics):
			#gtk.gdk.threads_enter()
			#print "pending: %s" % gtk.events_pending()
			#while gtk.events_pending():
			#	print "dokoncujem"
			#	gtk.main_iteration(False)
			if lyrics == None:
				return
			if isinstance(lyrics, list):
				log.error("\nlist is unsupported now\n")
				return
			#print lyrics
			processedLyrics = self.processLyrics(lyrics)
			
			if len(processedLyrics.entities) > 1:
				self.lyricsList.append(processedLyrics)
			
			
			if self.state == 'minimized' and self.playing:
				self.maximize()
			if not self.playing:
				self.disconn.image = "paused"
				self.disconn.redraw()
			
			if self.lyricsPanel.getLyrics() == None and len(self.lyricsList) > 0:
				print "SETTING FIRST LYRICS"
				self.searching.animation.stop()
				self.searching.setVisible(False)
				self.searching.redraw()
				
				self.setLyricsIndex(0)
				if self.saveFirstLyrics:
					self.saveActualLyrics()
					self.saveFirstLyrics = False
			
			self.updateLyricsPanel()
	
	def onEngineFinish(self):
		log.info("lyrics engine finished!")
		self.searching.setVisible(False)
		self.searching.animation.stop()
		
		self.defreezeXmmsPlayer()
		if self.search.image != "search":
			self.search.image     = "search"
			self.search.imageOver = "search"
			self.search.redraw()
		if len(self.lyricsList) == 0:
			self.lyricsPanel.setLyrics(LYRICS_NOT_FOUND)
			self.lyricsPanel.redraw()
			gobject.timeout_add(3000, self.minimize, "no_lyrics")
			self.lyricsEngine.reportMissingLyrics(self.songInfo)
		
		self.searching.redraw()
		
	def onPlayerConnected(self):
		log.info('Player Connected: %s' % self.player.getPlayerName())
		"""
		song = self.player.getCurrentSong()
		# some events must be generated here, when switching betwean players. No, no, no, move this to player !!!
		if song != None:
			self.onSongChanged(song)
			self.onElapsed(self.player.getElapsed())
			if self.player.is_playing():
				self.onPlay()
			else:
				self.onStop()
		"""
				
		# maximize
		#if self.state == 'minimized':
		#	self.maximize()
		
	def onPlayerDisconnected(self):
		log.info('Player Disconnected')
		self.lyricsPanel.stopAnimation()
		self.lyricsPanel.setLyrics(None)
		self.lyricsList = []
		self.minimize("disconnected")
	
	fading = False
	
	# SongChange
	# Stop
	# Play(Resume)
	# PositionChange
	
	def onSongChanged(self, songFile):
		log.debug("######## Song Changed: "+str(songFile))			
		if self.lyricsEngine.isRunning:
			self.stopSearchingOnNet()
			
		anim = animation.CompositeAnimation(10, 200)
		anim.addTransition(self.lyricsPanel.__setattr__, animation.LinearScalarInterpolator(self.lyricsPanel.alpha, 0.0), 'alpha')
		anim.addTaskOnFinish(self.changeLyrics, songFile)
		anim.addTaskOnFinish(self.fadeIn)
		self.fading = True
		anim.start(self.lyricsPanel.redraw)
		print "Start TimeLine"
		self.lyricsPanel.startTimeline()
		if not self.player.is_playing():
			self.lyricsPanel.pauseAnimation()
		
		#self.lyricsPanel.start()
		#self.changeLyrics(songFile)
	
	def changeLyrics(self, songFile):
		print "CHANGE LYRICS"
		self.fading = False
		if songFile != None:
			self.lyricsPanel.stopAnimation()
			#self.lyricsPanel.actualLine = 0
			self.lyricsPanel.render_lyrics = False
			self.t1 = gobject.get_current_time()
			self.lyricsPanel.setLyrics(None)
			#print "new song -> set elapsed 0.2" # depends on fade duration
			self.lyricsPanel.setElapsed(0.2)
			
			songInfo = {}
			if not songFile.startswith("http"):
				songInfo = {'file': songFile}
			title = self.player.getTitle()
			if title != None and len(title) > 0:
				songInfo['title']  = self.player.getTitle()
				
			artist = self.player.getArtist()
			if artist != None and len(artist) > 0:
				songInfo['artist'] = artist
				
			album = self.player.getAlbum()
			if album != None and len(album) > 0:
				songInfo['album']  = album
			
			print "Song Info:"
			print songInfo
			if not songInfo.has_key('artist') and title:
				if title.find("-") != -1:
					info = title.split("-")
					songInfo['artist'] = info[0].strip()
					songInfo['title'] = info[1].strip()
					if songInfo['title'].find("(") != -1: songInfo['title'] = songInfo['title'][ : songInfo['title'].find("(")].strip()
			print songInfo		
			self.songInfo = songInfo
			self.lyricsList = []
			
			self.saveFirstLyrics = False
			lyrics = self.getLyricsFromDisk()
			if lyrics != None:
				self.addLyrics(lyrics)
			elif songInfo.has_key('file'):
				alsongEngine = ALSong.ALSongEngine()
				self.freezeXmmsPlayer()
				lyrics = alsongEngine.findByCheckSum(songInfo['file'])
				#print "skipping alsong"
				#lyrics = None
				self.defreezeXmmsPlayer()
				self.saveFirstLyrics = True
				if lyrics != None:
					self.addLyrics(lyrics)
				else:
					#print "GO AND FIND ON NET!"
					self.searchOnNet()
			else:
				self.saveFirstLyrics = True
				self.searchOnNet()
				
				#import time
				#time.sleep(5)
				#print t1
				#print 'download time: '+str(gobject.get_current_time()-t1)
			
				#self.onElapsed(gobject.get_current_time()-t1)
			
	def onElapsed(self, elapsed, correction = False):
		# elapsed parameter may be old, so update it TODO: fix this
		#elapsed = self.player.getElapsed()
		print "############  Elapsed Event"
		print "ELAPSED %d fading = %s" % (elapsed, self.fading)
		if self.fading:
			return
		
		log.debug('set elapsed: %s' % elapsed)
		self.lyricsPanel.setElapsed(elapsed)

		log.debug("redraw in onElapsed")
		self.lyricsPanel.redraw()
		
			
	def onPlay(self):
		log.debug('############  onPlay')
		#self.fadeIn()
		self.lyricsPanel.resumeAnimation()
		
		self.playing = True
		if self.state == 'minimized':
			if self.lyricsPanel.lyrics == None or self.lyricsPanel.lyrics == LYRICS_NOT_FOUND:
				#print "STAY MINIMIZED"
				self.disconn.image = "no_lyrics"
				self.disconn.redraw()
			else:
				#print "MAAXIMIZE"
				self.maximize()
							
	def onStop(self):
		log.debug('############  onStop')
		self.lyricsPanel.pauseAnimation()
		self.playing = False
		#self.fadeOut()
		self.lastStop = gobject.get_current_time()
		gobject.timeout_add(5000, lambda: self.minimize("paused") if not self.playing and (gobject.get_current_time() - self.lastStop) > 4.8 else 1)
		#gobject.timeout_add(5000, self.test)
		
		
	def test(self):
		if not self.playing:
			print gobject.get_current_time() - self.lastStop
			self.minimize()
		
	def minimize(self, icon = None):
		log.debug("MINIMIZING minimalizing screenlet\n**************************")
		if self.minimizeToTray:
			#self.window.hide()
			print "\niconify\n"

			self.trayIcon.set_visible(True)
						
			geometry = self.trayIcon.get_geometry()[1]
			import utils
			utils.set_icon_geometry(self.window, *geometry)
			self.window.iconify()
			self.state = 'minimized'
			
		else:
			self.lyricsPanel.setVisible(False)
			self.controlPanel.setVisible(False)
			self.playersDropDown.setVisible(False)
			self.resize.setVisible(False)
			self.invisibleButton.setVisible(False)
			self.searching.setVisible(False)
			self.searching.animation.stop()
			
		
			if self.state != 'minimized':
				log.debug("MINIMIZING was maximized, must resize and move")
				log.debug("MINIMIZING Actual Layout: x=%d y=%d width=%d height=%d" % (self.x, self.y, self.width, self.height))
				newPos = self.pack(self.disconn)
				log.debug("MINIMIZING Packed Position: x=%d y=%d (offsets x=%d y=%d)" % (self.x+newPos[0], self.y+newPos[1], newPos[0], newPos[1]))
				
				if self.safe_minimize:
					self.disconn.setPosition(newPos[0], newPos[1])
					print "Safe minimize move to: x=%d y=%d" % (newPos[0], newPos[1])
				else:
					self.canvas.setSizeThenPosition(self.disconn.getWidth(), self.disconn.getHeight(), self.x+newPos[0], self.y+newPos[1])
					
				#self.canvas.setSizeThenPosition(self.disconn.getWidth(), self.disconn.getHeight(), self.x+self.maxi_width-self.disconn.getWidth(), self.y)
				self.state = 'minimized'
				if self.session:
					log.debug("saving minimalized state to config")
					self.session.backend.save_option(self.id, 'state', self.state)
			print "minimized"
			if icon != None:
				self.disconn.image = icon
			self.disconn.setVisible(True)
			#self.disconn.redraw()
			self.canvas.redraw()
	
	def updateState(self):
		if self.playing:
			if self.lyricsPanel.getLyrics() == None:
				self.disconn.image = "no_lyrics"
			else:
				self.maximize()
		else:
			if self.lyricsPanel.getLyrics() == None:
				self.disconn.image = "no_lyrics"
			else:
				self.disconn.image = "paused"
				
	def maximize(self):
		if self.state == "maximized":
			return
		log.debug("MINIMIZE maximalizing screenlet")
		print self.window
		print self.window.window
		#print dir(self.window)
		#if self.minimizeToTray: # pozor na to
		if not self.window.window.is_visible() or self.window.iconify_initially:
			#self.window.show()
			print "\ndeiconify\n"
			self.window.deiconify()
			self.canvas.redraw()
			#self.trayIcon.set_visible(False)	
			
		else:
			self.disconn.setVisible(False)
			self.disconn.redraw()
			while gtk.events_pending():
				gtk.main_iteration(False)
		
			newPos = self.expand(self.disconn, self.maxi_width, self.maxi_height)
			log.debug("MINIMIZING Expanded Position: x=%d y=%d" % (newPos[0], newPos[1]))
			# or resize first ?
			if not self.safe_minimize:
				self.canvas.setPosition(newPos[0], newPos[1])
			#self.canvas.setPosition(self.x-(self.maxi_width-self.disconn.getWidth()), self.y)		
			#self.canvas.setSize(width, height)
			"""
			self.width  = self.maxi_width
			self.height = self.maxi_height
		
			self.session.backend.save_option(self.id, 'width',  self.disconn.getWidth())
			self.session.backend.save_option(self.id, 'height', self.disconn.getHeight())
		
			self.update_shape()
			"""
			self.lyricsPanel.setVisible(True)
			self.controlPanel.setVisible(True)
			self.playersDropDown.setVisible(True)
			self.resize.setVisible(True)
			self.invisibleButton.setVisible(True)
			self.controlPanel.redraw()
		
		if self.width != self.maxi_width or self.height != self.maxi_height:
			self.width  = self.maxi_width
			self.height = self.maxi_height
		
			#self.session.backend.save_option(self.id, 'width',  self.disconn.getWidth())
			#self.session.backend.save_option(self.id, 'height', self.disconn.getHeight())
		
		self.state = 'maximized'
		if self.session:
			log.debug("writing maximalizing state to config")
			self.session.backend.save_option(self.id, 'state', self.state)
			
		self.update_shape() # depends on self.state
		

	def fadeIn(self):
		enterAnim = animation.CompositeAnimation(10, 200)
		enterAnim.addTransition(self.lyricsPanel.__setattr__, animation.LinearScalarInterpolator(self.lyricsPanel.alpha, 1.0), 'alpha')
		enterAnim.start(self.lyricsPanel.redraw)
				
	def lyricsFile(self):
		if self.songInfo != None:
			if self.songInfo.has_key('album') and self.songInfo.has_key('artist'):
				lrc_folder = "%s - %s" % (self.songInfo['artist'], self.songInfo['album'])
			# only album
			elif self.songInfo.has_key('album'):
				lrc_folder = self.songInfo['album']
			# only artist
			elif self.songInfo.has_key('artist'):
				lrc_folder = self.songInfo['artist']
			else:
				lrc_folder = "Unknown"
			
			if self.songInfo.has_key('title'):
				lrc_file = self.songInfo['title']
			elif self.songInfo.has_key('file'):
				lrc_file = self.songInfo['file']
				lastDot = lrc_file.rfind('.')
				if lastDot != -1:
					lrc_file = lrc_file[:lastDot]
			else:
				lrc_file = "Unknown"
			return {'folder' : lrc_folder, 'file' : lrc_file+".lrc"}
				
	###################################
	##### save lyrics on the disk #####
	###################################
	def saveButtonPressed(self, widget, event):
		self.saveActualLyrics()
		
	def saveActualLyrics(self):
		log.debug("save lyrics on disk")
		if self.save_lyrics:				
			if self.songInfo != None:				
				text = self.lyricsPanel.getLyrics()
				if text == None:
					log.info('Nothing to save')
					return
				
				lrc_path = self.lyricsFile()
				album_path = self.lyrics_directory + os.sep + lrc_path['folder']
				if not os.path.exists(album_path) or not os.path.isdir(album_path):
					log.info("Creating album directory")
					try:
						os.mkdir(album_path)
					except Exception, e:
						log.error("Can't create album directory: " + str(e))
						return

				lrc_file = album_path + os.sep + lrc_path['file']
				try:
					log.info("writing lyrics into file: %s" % lrc_file)
					fp = open(lrc_file, 'w')
					fp.write(text)
					fp.close()
					self.notifyMessage("Lyrics was saved on disk")
				except Exception, e:
					log.error("Can't create lyrics file: " + str(e))
						
										
	###########################################
	##### load lyrics from file if exists #####
	###########################################
	def getLyricsFromDisk(self):
		log.debug("searching lyrics on disk")
		# check for .lrc file in song file directory
		lrc_file = None
		if self.songInfo.has_key('file'):
			lrc_file = self.songInfo['file'].rstrip("mp3")+"lrc" #TODO: not only mp3 expecting
		if lrc_file == None or not path.exists(lrc_file):
			lrc_path = self.lyricsFile()
			lrc_file = self.lyrics_directory + os.sep + lrc_path['folder'] + os.sep + lrc_path['file']
			log.debug("lyrics should be here: %s" % lrc_file)
			if not path.exists(lrc_file):
				lrc_file = lrc_file[:-4]
				log.debug(" For old compatibility, %s will be checked too" % lrc_file)
				
		print lrc_file
		if lrc_file != None and path.exists(lrc_file):
			f = open(lrc_file, 'r')
			print "lyrics from file: %s" % lrc_file
			lrc = f.read()
			f.close()
			return lrc
		print "Nothing on disk"
		return None

	# Comapre two LyricEntity objects
	def compare(self, e1, e2):
		#print "compare %f %f" % (e1.seconds, e2.seconds)
		if e1.seconds < e2.seconds:
			return -1
		elif e1.seconds > e2.seconds:
			return 1
		else:
			return 0
			
	def parseLine(self, line):
		p = re.compile("^(\s)*\[(?P<min>\d(\d)?):(?P<sec>\d(\d)?(.(\d)+)?)\](?P<text>(.)*)$")
		m = p.match(line)
		if m:
			minutes = int(m.group('min'))
			seconds = float(m.group('sec'))
		
			time = minutes*60 + seconds
			text = m.group('text')
			return [time, text]
	###############################
	##### process lyrics data #####
	############################### 		
	def processLyrics(self, lyrics):
		
		lines = lyrics.rsplit(os.linesep)
		processedLyrics = []
		old = -1
		for line in lines:
			#print "line: %s" % line
			
			times = []
			text = None
			tt = self.parseLine(line)
			while tt != None:
				times.append(tt[0])
				text = tt[1]
				tt = self.parseLine(text)
			
			#print times
			#print text
			
			if len(times) > 1:
				if not self.filter_cjk or not self.isCJK(text):
					log.debug("processing multiple timing tags")
					for t in times:
						processedLyrics.append(LyricEntity([text], t))
					
			if len(times) == 1:
				time = times[0]		
				if text == None:# or len(text) == 0:
					continue

				#print time
				#print text
				# texts with the same time or with [00:00.00] join together
				if old == time or time == 0:
					# if enabled, filter korean, chinese, japanese ...
					if self.filter_cjk and self.isCJK(text):
						continue
					if len(processedLyrics) > 0:
						processedLyrics[-1].text.append(text)
					else:
						# create new lyrics entity, if doesn't exists
						#processedLyrics.append(LyricEntity(["%s %s" % (time, text)], time)) # for debug
						processedLyrics.append(LyricEntity([text], time))
					continue
				# if enabled, filter korean, chinese, japanese ...
				if not self.filter_cjk or not self.isCJK(text):
					# create new lyrics entity
					#processedLyrics.append(LyricEntity(["%s %s" % (time, text)], time)) # for debug
					processedLyrics.append(LyricEntity([text], time))
				old = time
			
			continue	

			# parse additional info
			"""
			else:
				if not artist and line.startswith('artist:'):
					artist = line[7:]
				if not title and line.startswith('title:'):
					title = line[6:]
				if not album and line.startswith('album:'):
					album = line[6:]
			"""	
		if len(processedLyrics) == 0:
			# UNSYNCHRONIZED LYRICS
			return [lyrics]

		
		#insert same info about song at start, if there is "place"
		if len(processedLyrics) > 0 and processedLyrics[0].seconds > 0:
			info = []
			if self.songInfo.has_key('artist'): info.append(self.songInfo['artist'])
			if self.songInfo.has_key('album'):  info.append(self.songInfo['album'])
			if self.songInfo.has_key('title'):  info.append(self.songInfo['title'])
			info.append('')
			processedLyrics.insert(0, LyricEntity(info, 0))
		
		# sort it
		processedLyrics.sort(cmp = self.compare)
		return Lyrics(processedLyrics)
		
	def translateLyrics(self, processedLyrics):
		print "translate Lyrics"
		print self.translation_enabled
		print processedLyrics.translation
		if self.translation_enabled:
			if processedLyrics.translation == languages[self.language]:
				print "ALREADY TRANSLATED"
				return
			if not processedLyrics.showTranslation:
				print "TURNED OFF ANTWAY"
				return
			"""
			for line in processedLyrics:
				if line.translation != None:
					print "ALREADY TRANSLATED"
					return
			"""
			#lang = LanguageDetector().detect(lyrics)
			#if lang != None:
			#	print Translator().translate(lyrics, "en", lang.lang_code)
		
			text = ""
			translated = ""
			url_encoded_length = 0
			import urllib
			
			for l in processedLyrics.entities:
				for line in l.text:
					#for word in line.rsplit(" "):
					#	text += word.lower()+" "
					#text += "|"
					
					# translate by limited string length
					#if (len(text)+len(line) > 1500):
					url_encoded_length += len(urllib.urlencode({'x': line}))
					if url_encoded_length > 1800:
						#urllib.urlencode({'x': text})
						translated += self.translate(text)
						text = ""
						url_encoded_length = 0
					text += line.lower()+"|"
			translated += self.translate(text)
			#translated = translated.encode('utf8')

			translated = translated.replace("&#39;", "'").replace("&quot;", "`").rsplit("|")
			#print translated
			
			i = 0
			for l in processedLyrics.entities:
				trans = []
		
				for line in l.text:
					if i >= len(translated):
						break
			
					if len(translated[i]) < 2:
						i+=1
						continue
				
					trans.append(translated[i])
					i+=1
		
				j = 0
				for line in reversed(l.text):
					if len(line) == 0:
						j+=1
					else:
						break
			
				l.translation = trans
			processedLyrics.translation = languages[self.language]
		
	def translate(self, text):
		"""
		lang = LanguageDetector().detect(text)
		lang = "en"
		if lang != None:
			translated = Translator().translate(text, "es", lang)
			#lines = translated.rsplit(os.linesep)
			lines = translated.rsplit("\r")
		else:
			"CANNOT Translate"	
		"""
		try:
			#import translate2
			#translated = translate2.translate("en", "sk", text[:1000]).rsplit("|")
			print "TRANSLATE %s" % languages[self.language]
			#print text.decode('utf8', 'ignore')
			#print len(text)
			#print text
			translated = Translator().translate(text.encode('utf8', 'ignore'), languages[self.language])
			if translated != None:
				"""
				try:
					import chardet
					encoding = chardet.detect(translated)
					print encoding
				except: pass
				"""
				return translated.encode('utf8', 'ignore')
			return ""
		except Exception, e:
			print e
			traceback.print_exc()
			return ""
	
	def isCJK(self, text):
		#print text
		# isn't unicode ?, will be
		if not isinstance(text, unicode):
			text = unicode(text)
		
		for c in text:
			#if ord(c) > 120: print ord(c)
			if ord(c)>10000:
				return True
		return False
	#"""
	
	# override screenlets.Screenlet expose with no action
	#def expose(self, w, e):
	#	pass
	
	
	def on_draw(self, ctx):
		"""
		if self.state == 'minimized':
			#print self.width
			ctx.set_source_rgba(0,0,1,1)
			ctx.rectangle(0, 0, self.width, 50)
			ctx.fill()
		else:
			self.canvas.expose(ctx)
		"""
		self.canvas.expose(ctx)
		#pass
		
	def on_draw_shape (self, ctx):
		#print "UPADTE SHAPE"
		if self.state == 'minimized':
			#print "UPADTE SHAPE x=%d y=%d %d x %d" % (self.disconn.bounds.x, self.disconn.bounds.y, self.disconn.bounds.width, self.disconn.bounds.height)
			ctx.rectangle(self.disconn.bounds.x, self.disconn.bounds.y, self.disconn.bounds.width, self.disconn.bounds.height)
		else:
			if self.invisible:
				#print "GHOST SHAPE"
				ctx.rectangle(self.invisibleButton.bounds.x*self.scale, self.invisibleButton.bounds.y*self.scale,
					self.invisibleButton.getWidth()*self.scale, self.invisibleButton.getWidth()*self.scale)
			else:
				print "NORMAL SHAPE"
				ctx.rectangle(0, 0, self.maxi_width*self.scale, self.maxi_height*self.scale)
		ctx.fill()
		
	# must override, screenlet moving reason
	def button_press(self, widget, event):
		pass
	
	def on_unfocus (self, event):
		log.debug('unfocus %s' % self.controlPanel.alpha)
		if self.autoPanelHide == True and self.controlPanel.alpha > 0.01:
			if self.autoHideTimer != None:
				gobject.source_remove(self.autoHideTimer)
			self.autoHideTimer = gobject.timeout_add(1000, self.hidePanel)

	def hidePanel(self):
		hideAnim = CompositeAnimation(6, 100)
		hideAnim.addTransition(self.setPanelAlpha, LinearScalarInterpolator(1.0, 0.0))
		hideAnim.start(self.redraw_control_panel)#self.canvas.redraw)
		
		if not self.invisible:
			invisibleButtonHideAnimation = CompositeAnimation(6, 100)
			invisibleButtonHideAnimation.addTransition(self.invisibleButton.__setattr__, LinearScalarInterpolator(1.0, 0.0), 'alpha')
			invisibleButtonHideAnimation.start(self.invisibleButton.redraw)
		return False
	
	def redraw_control_panel(self):
		#self.canvas.redraw()
		self.controlPanel.redraw()
		self.resize.redraw()
		self.playersDropDown.redraw()
		self.invisibleButton.redraw()
		if self.disconn.isVisible():
			self.disconn.redraw()
		
	def setPanelAlpha(self, alpha):
		#print 'setPanelAlpha %s' % alpha
		self.controlPanel.alpha = alpha
		self.playersDropDown.alpha = alpha
		self.resize.alpha = alpha
		if not self.invisible:
			self.invisibleButton.alpha = alpha
		
	def on_focus (self, event):
		log.debug('focus %s' % self.search.alpha)
		if self.controlPanel.alpha < 0.99:
			enterAnim = CompositeAnimation(6, 100)
			enterAnim.addTransition(self.setPanelAlpha, LinearScalarInterpolator(0.0, 1.0))
			enterAnim.start(self.redraw_control_panel)#self.canvas.redraw)
		
	def lyricsPanel_pressed(self, widget, event):
		# move screenlet during mouse drag, only on LyricsPanel
		print self.width
		print self.height
		screenlets.Screenlet.button_press(self, self.window, event)

	def updateLyricsPanel(self):
		nextEnabled = self.lyrics_index != len(self.lyricsList)-1
		if self.next.isEnabled() != nextEnabled:
			self.next.setEnabled(nextEnabled)
			self.next.redraw()
			
		prevEnabled = self.lyrics_index != 0
		if self.prev.isEnabled() != prevEnabled:
			self.prev.setEnabled(prevEnabled)
			self.prev.redraw()
		
		if len(self.lyricsList) < 10:
			width = 40
		elif len(self.lyricsList) < 100:
			width = 50
		else:
			width = 60

		self.label.setText(str(self.lyrics_index+1)+' of '+str(len(self.lyricsList)))
		self.label.setVisible(len(self.lyricsList) > 0)
		self.label.setEnabled(len(self.lyricsList) > 1)
		if self.label.getWidth() != width:
			self.label.setSize(width, self.label.getHeight())
			self.arrangeControlPanel()
			self.controlPanel.redraw()
			self.playersDropDown.redraw()
		else:
			self.label.redraw()
		
		
	def setLyricsIndex(self, index):
		self.lyrics_index = index
		self.label.setText(' '+str(self.lyrics_index+1)+' of '+str(len(self.lyricsList)))
		
		#print "setting lyrics"
		#print self.lyricsList[self.lyrics_index]
		#lyr = "[00:02.00]Lyrics here\n[00:02.50]\n[00:02.90]Lyrics here will be skipped\n[00:03.90][00:04.2]Lyrics here"
		#self.lyricsPanel.setLyrics(self.processLyrics(lyr))
		
		lyrics = self.lyricsList[self.lyrics_index]
		lyrics.showTranslation = self.translation_enabled
		print "Set Lyrics translation=%s enabled=%s" % (lyrics.translation, self.translation_enabled)
		self.translateLyrics(lyrics)
		#lyrics = self.translateLyrics(self.lyricsList[self.lyrics_index])
		self.lyricsPanel.setLyrics(lyrics)
		
		self.next.setEnabled(index != len(self.lyricsList)-1)
		self.prev.setEnabled(index != 0)
		
		self.updateWidgetPositions(self.width, self.height)
		
	def nextLyrics(self, widget, event):
		if event.type != gtk.gdk.BUTTON_PRESS:
			return
		
		if self.lyricsList != None and self.lyrics_index < len(self.lyricsList)-1:
			self.lyrics_index += 1
			self.setLyricsIndex(self.lyrics_index)
		
	def previousLyrics(self, widget, event):
		if event.type != gtk.gdk.BUTTON_PRESS:
			return
		if self.lyricsList != None and self.lyrics_index > 0:
			self.lyrics_index -= 1
			self.setLyricsIndex(self.lyrics_index)
			
						
	def onResizeStart(self, widget, event):
		#log.debug("resizing started %d, %d" % (event.x, event.y))
		x =	self.maxi_width -event.x
		y = self.maxi_height-event.y
		#x = self.width-event.x
		#y = self.height-event.y
		log.debug("drag offset %d, %d" % (x, y))
		self.dragOffset = [x, y]
		
	def onResize(self, event):
		#log.debug("on resize: %d, %d" % (event.x, event.y))
		width = int(event.x+self.dragOffset[0])
		height = int(event.y+self.dragOffset[1])
		self.updateWidgetPositions(width, height)
		size = self.canvas.root.get_size()
		if width > size[0] or height > size[1]:
			self.canvas.setSize(size[0]+100, height+100)
		self.canvas.redraw()
		
	def do_resize(self, widget, event):
		self.maxi_width  = int(event.x+self.dragOffset[0])
		self.maxi_height = int(event.y+self.dragOffset[1])
		
		self.width  = self.maxi_width
		self.height = self.maxi_height
		self.session.backend.save_option(self.id, 'width',  self.disconn.getWidth())
		self.session.backend.save_option(self.id, 'height', self.disconn.getHeight())
		self.session.backend.save_option(self.id, 'maxi_width',  self.maxi_width )
		self.session.backend.save_option(self.id, 'maxi_height', self.maxi_height)
		
		self.canvas.redraw()
		
		
	def onThemeChanged(self, theme):
		if self.canvas != None:
			self.canvas.setTheme(self.theme)
			self.arrangeControlPanel()
			self.canvas.redraw()
		
	def arrangeControlPanel(self):
		self.controlPanel.bounds.height = self.search.getHeight()
		
		self.prev.setPosition(0, 2)
		x = self.prev.bounds.width + 2
		
		self.label.setPosition(x, (self.controlPanel.getHeight()-self.label.getHeight())/2.0)
		x += self.label.bounds.width + 2
		
		self.next.setPosition(x, 2)
		x += self.next.bounds.width + 2
		
		self.search.setPosition(x, 0)
		x += self.search.bounds.width + 2
		
		self.save.setPosition(x, 0)
		x += self.save.bounds.width + 2
		
		self.upload.setPosition(x, 0)
		x += self.upload.bounds.width + 2
		
		self.controlPanel.bounds.width = x
		self.playersDropDown.setPosition(self.controlPanel.getWidth()+5, self.controlPanel.bounds.y)
				
	def updateWidgetPositions(self, width, height):
		
		self.controlPanel.setPosition(0, height-20)
		self.playersDropDown.setPosition(self.controlPanel.getWidth()+5, self.controlPanel.bounds.y)
		
		self.lyricsPanel.setSize(width, height-25)
		#self.searching.setPosition((width-self.searching.getWidth())/2, (height-25-self.searching.getHeight())/2) #center
		self.searching.setPosition(4, height-25-self.searching.getHeight()) # left-bottom
		self.notifier.setPosition(4, height-25-self.searching.getHeight())
		
		self.resize.setPosition(width-18, height-18)
		self.invisibleButton.setPosition(width - 20 - self.resize.getWidth(), height - 18)
		
		self.canvas.redraw()
	
	def invisible_pressed(self, widget, event):
		#log.debug("make invisible")
		self.invisible = not self.invisible
		self.update_shape()
		
	def response(self, lyrics, source_name):
		log.debug("response form C")
		#print lyrics
		self.addLyrics(lyrics)
		log.debug("-----------------")
		
	def onSearchClicked(self, widget, event):
		if not self.lyricsEngine.isRunning:
			self.searchOnNet()
		else:
			self.stopSearchingOnNet()
	
	def notifyMessage(self, message):
		self.notifier.setText(message)
		self.notifier.setVisible(True)
		self.notifier.alpha = 1.0
		self.notifier.redraw()
		self.notifier.animation.start(self.notifier.redraw)
		
	def afterUpload(self, message):
		self.notifyMessage(message)
		
	def uploadButtonPressed(self, widget, event):
		#print self.lyricsPanel.getLyrics()
		self.lyricsEngine.upload(self.songInfo, self.lyricsPanel.getLyrics(), self.afterUpload)
		
	def searchOnNet(self):
		print "search on net"
		self.searching.setVisible(True)
		self.searching.animation.start(self.searching.redraw)
		
		self.freezeXmmsPlayer()
		self.lyricsEngine.search(self.songInfo)
		self.search.image     = "stop_search"
		self.search.imageOver = "stop_search"
		self.search.redraw()
			
	def stopSearchingOnNet(self):
		self.lyricsEngine.stop()
			
	def freezeXmmsPlayer(self):
		if self.xmmsPlayer != None:
			#print "freeze"
			self.xmmsPlayer.freeze()
				
	def defreezeXmmsPlayer(self):
		if self.xmmsPlayer != None:
			self.xmmsPlayer.defreeze()
						
	def doColorAdaptation(self):

		w = gtk.gdk.get_default_root_window()
		sz = w.get_size()
		
		width  = 1#self.maxi_width
		height = 1#self.maxi_height
		
		pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8, width, height)
		pb = pb.get_from_drawable(w,w.get_colormap(),self.x,self.y, 0, 0, width, height)
		try:
			array = pb.get_pixels_array()[0][0]
			pixel = [array[0][0], array[1][0], array[2][0]]
		except:
			#print "%d x %d size: %d" % (width, height, len(self.pixbuf.get_pixels()))
			strColor = pb.get_pixels()#[4*(width*y+x) : 4*(width*y+x+1)]
			pixel = [ord(strColor[0]),ord(strColor[1]),ord(strColor[2])]
			
		bgColor = (pixel[0]/255.0, pixel[1]/255.0, pixel[2]/255.0)
		
		if self.colorAdaptation == 'Inverse':
			textColor = (1.0-pixel[0]/255.0, 1.0-pixel[1]/255.0, 1.0-pixel[2]/255.0)
			
		elif self.colorAdaptation == 'Black or White':
			contrastToBlack = (bgColor[0] + bgColor[1] + bgColor[2])/3.0
			contrastToWhite = ((1.0 - bgColor[0]) + (1.0 - bgColor[1]) + (1.0 - bgColor[2]))/3.0
			#contrastToRed = ((1.0-bgColor[0]) + bgColor[1] + bgColor[2])/3.0
		
			#print "contrast to black %f" % diffToBlack
			#print "contrast to white %f" % diffToWhite
			#print "contrast to red %f"   % diffToRed
		
			possibleColors = {contrastToBlack: [0,0,0], contrastToWhite:[1,1,1] }
			textColor = possibleColors[max(possibleColors)]
		
		difference = abs(self.lyricsPanel.color_highlight[0] - textColor[0]) + abs(self.lyricsPanel.color_highlight[1] - textColor[1]) + abs(self.lyricsPanel.color_highlight[2] - textColor[2])
		if difference < 0.1:
			return True
		#log.info("Time to change color")
		
		normalTextColor    = []
		normalTextColor.extend(textColor)
		normalTextColor.append(0.5) # color alpha value
		
		highlightTextColor = []
		highlightTextColor.extend(textColor)		
		highlightTextColor.append(1.0) # color alpha value
		
		self.colorAnimation(normalTextColor, highlightTextColor)
		#log.debug("textColor: "+str(textColor))
		return True

	def colorAnimation(self, normalTextColor, highlightTextColor):
		animation = CompositeAnimation(6, 400)
		animation.addTransition(self.lyricsPanel.__setattr__, LinearVectorInterpolator(self.lyricsPanel.color_normal, normalTextColor), 'color_normal')
		animation.addTransition(self.lyricsPanel.__setattr__, LinearVectorInterpolator(self.lyricsPanel.color_highlight, highlightTextColor), 'color_highlight')
		animation.start(self.lyricsPanel.redraw)
		
		#animation.addTransition([self.lyricsPanel, 'color_normal'   ], self.lyricsPanel.color_normal, normalTextColor)
		#animation.addTransition([self.lyricsPanel, 'color_highlight'], self.lyricsPanel.color_highlight, highlightTextColor)
		#animation.start(self.lyricsPanel, self.lyricsPanel.redraw)

		
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	try:
		import ctypes, os, sys
		libc = ctypes.CDLL('libc.so.6')
		libc.prctl(15, os.path.basename(sys.argv[0]), 0, 0, 0)
	except Exception: pass
	import screenlets.session
	screenlets.session.create_session(LyricsScreenlet)	
