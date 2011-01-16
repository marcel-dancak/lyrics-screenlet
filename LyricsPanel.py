#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


import os
import screenlets
import gtk
from gtk.gdk import Rectangle
import cairo
import pango
import math
import gobject
from gui.cairo_widgets import *
from animation import *
from math import ceil

class Lyrics:
    entities = None
    translation = None
    showTranslation = True 
    
    def __init__(self, entities):
        self.entities = entities
        
class LyricEntity:
	seconds        = None
	text           = None
	translation    = None
	height         = None
	trimmed_height = None 
	lengths        = None
	tlengths       = None
	show_time      = False # TODO implement
	
	def __init__(self, text, seconds):
		self.text = text
		self.seconds = seconds
		self.tlengths = [0]
		
class PixmapBuffer:
	pixmap = None
	ctx    = None
	
	def __init__(self, drawable, width, height):
		self.width  = int(width)
		self.height = int(height)
		self.pixmap = gtk.gdk.Pixmap(drawable, self.width, self.height, -1)
		self.ctx    = self.pixmap.cairo_create()
		self.drawable = drawable
	
	def clear(self):
		self.ctx.set_operator(cairo.OPERATOR_CLEAR)
		self.ctx.rectangle(0, 0, self.width, self.height)
		self.ctx.fill()
		self.ctx.set_operator(cairo.OPERATOR_OVER)
	
	def resize(self, width, height):
		del self.pixmap
		self.width  = int(width)
		self.height = int(height)
		self.pixmap = gtk.gdk.Pixmap(self.drawable, self.width, self.height, -1)
		self.ctx    = self.pixmap.cairo_create()
		
ALIGN_CENTER = 0
ALIGN_LEFT   = 1
ALIGN_RIGHT  = 2

class LyricsPanel(Widget):
	lyrics = None
	layout = None
	textForAnimation = None

	timeOffset = 0.0
	actualLine = 0
	render_lyrics = True
	mode = 'playing'
	lyrics_need_update = False
	elapsed = [None, None, 'stopped']
	
	color_normal = None
	color_highlight = None
	font = pango.FontDescription("sans 9")
	translationFont = pango.FontDescription("sans italic 7")
	text_scale = 1.5
	textAlign  = ALIGN_CENTER
	
	lyrics_timer = None
	anim_timer = None
	
	# animation settings
	anim_steps    = 10
	anim_duration = 350
	anim_fraction = 0.0
	animation     = None
	timeline      = None
	gscale        = 1.0
	
	def __init__ (self):
		Widget.__init__(self)
		self.registerEvent('key_pressed', self.on_key_press)
		self.registerEvent('drag_data_received', self.on_drag_data_received)
		
		self.button = ImageButton(None, 'record')
		self.button.setPosition(10,10)
		self.button.registerEvent('button_pressed', self.stopEditing)
		#self.button.setVisible(False)
		
		overAnim = CompositeAnimation(6, 500, loop = True)
		overAnim.addTransition(self.button.setOverAlpha, LinearScalarInterpolator(0.1, 1.0))
		self.button.setVisibleAnimation(overAnim)
		
		self.time = Label("0:00:00")
		#self.time.setSize(42, 20)
		self.time.animation = CompositeAnimation(16, 1000, loop = True)
		self.time.setPosition(10, 5)
		self.time.setVisible(False)
		
		keyAnimation = Animation(200, 6)
		keyAnimation.addLinearTransition('scale', [1.0, 1.0], [2.0, 2.0], LINEAR)
		keyAnimation.addLinearTransition('alpha', 1.0, 0.0, LINEAR)
		keyAnimation.addTaskOnFinish('setVisible', False)
		
		self.seekUp = Label("")
		self.seekUp.drawBackground = False
		self.seekUp.textColor = [1.0, 0.25, 0.25, 1]
		#self.seekUp.fontSize = 10
		self.seekUp.setVisible(False)
		self.seekUp.animation = keyAnimation.create(self.seekUp)
		
		self.seekDown = Label("")
		self.seekDown.drawBackground = False
		self.seekDown.textColor = [1.0, 0.25, 0.25, 1]
		#self.seekDown.fontSize = 12
		self.seekDown.setVisible(False)
		self.seekDown.animation = keyAnimation.create(self.seekDown)
		
		self.addWidget(self.seekUp)
		self.addWidget(self.seekDown)
		self.addWidget(self.time)
		self.addWidget(self.button)
		
		self.gradient = cairo.LinearGradient(0, 0, 0, 10)
		self.gradient.add_color_stop_rgba(0, 1, 1, 1, 1)
		self.gradient.add_color_stop_rgba(1, 1, 1, 1, 0)
		
		self.timeline = TimeLine()
		self.editAnim = CompositeAnimation(self.anim_steps, self.anim_duration)
		
	def __setattr__(self, name, value):
		#print name+' '+str(value)
		Widget.__setattr__(self, name, value)
		
		if name == 'font' or name == 'text_scale':
			# on this two values depends text height of lyrics (text_scale can change number of lines)
			self.lyrics_need_update = True
			self.textForAnimation = None
			self.redraw()
		if name == 'textAlign':
			self.setAlignment()
			self.textForAnimation = None
			self.redraw()
			
		
	def setSize(self, width, height):
		Widget.setSize(self, width, height)
		self.seekUp.setPosition  (30, height/2-self.seekUp.getHeight()-10)
		self.seekDown.setPosition(30, height/2+5)
		
		self.resizeBuffers()
		self.lyrics_need_update = True
		
	def resizeBuffers(self):
		if self._buffer1 != None:
			self._buffer1.resize(self.bounds.width*self.gscale*0.9, self._buffer1.height)
		if self._buffer2 != None:
			self._buffer2.resize(self.bounds.width*self.gscale, self._buffer2.height)
		
		
	def setFont(self, font):
		print 'setFont %s' % font
		self.font = font
				
	def setLyrics(self, lyrics):
		self.render_lyrics = True
		if lyrics != None and len(lyrics.entities) == 1 and isinstance(lyrics.entities[0], str):
			#print 'unsynchronized lyrics'
			self.setUnsynchLyrics(lyrics.entities[0])
			return
		self.setMode('playing')
		self.lyrics = lyrics
		self.lyrics_need_update = True
		self.cache = None
		self.textForAnimation = None
		self.lastState = None # to update text positioning (align to center)
		
		self.startAnimation()
		#if self.animation. == 'playing':
		#	self.stopAnimation()
		if self.timeline.stopped:
			self.pauseAnimation()
		
		#self.redraw()
			
	def setElapsed(self, elapsed):
		#print 'set elapsed: '+str(elapsed)
		self.timeline.setTime(elapsed*1000)
		self.startAnimation()
		
	def synchronizeLyrics(self, elapsed):
		for i,lyric in enumerate(self.lyrics.entities):
			if lyric.seconds > elapsed:
				self.actualLine = i-1
				print self.actualLine
				return
		# set last line
		self.actualLine = len(self.lyrics.entities)-1
			
	def startAnimation(self):
		if self.animation != None:
			print "STOP ANIMATION"
			self.animation.stop()
			
		if self.lyrics == None:
			return
		self.anim_fraction = 0.0
		elapsed = self.timeline.getTime()/1000.0
		self.synchronizeLyrics(elapsed)
		if self.actualLine+1 < len(self.lyrics.entities):
			#print "Start Animation: current limeline: %f" % self.timeline.getTime()
			alarm = int((self.lyrics.entities[self.actualLine+1].seconds - elapsed)*1000)
			#print "Start ANIMATION elapsed: %d delay: %d with: %s" % (elapsed, alarm, .entities[self.actualLine+1].text)
			if self.animation != None:
				self.animation.stop()
			else:
				self.animation = CompositeAnimation(self.anim_steps, self.anim_duration)
				#self.animation.addTransition(self.__setattr__, LinearVectorInterpolator(self.color_highlight, self.color_normal), 'dec_color')
				self.animation.addTaskOnFinish(self.onAnimEnd)
			
			self.animation.startupDelay = alarm
			self.animation.start(self.update)
			#if self.time.isVisible():
			#	self.time.animation.start(self.update_timelabel)
	
	def update_timelabel(self):
		time = self.timeline.getTime()/1000.0
		m = int(time/60)
		s = time % 60
		mili = (s - int(s))*100
		
		s = "0%d" % s if s < 10 else "%d" % s
		mili = "0%d" % mili if mili < 10 else "%d" % mili
		self.time.setText("%d:%s:%s" % (m, s, mili))
		self.time.redraw()
		
	def startTimeline(self):
		#self.timeline = TimeLine()
		self.timeline.start()
	
	def update(self):
		#print "UPDATE %f" % self.animation.fraction
		self.anim_fraction = self.animation.fraction
		self.redraw()
		
	def onAnimEnd(self):
		#print "END OF ANIMATION"
		if self.lyrics and self.actualLine+1 < len(self.lyrics.entities):
			#print "Animation duration: %f" % self.animation.timeline.getTime()
			time = self.timeline.getTime()
			#print "Current time: %f" % time
			#print "Next line: %f" % self.lyrics.entities[self.actualLine+1].seconds
			
			self.animation.duration = self.anim_duration
			if self.actualLine+2 < len(self.lyrics.entities):
				diff = self.lyrics.entities[self.actualLine+2].seconds - self.lyrics.entities[self.actualLine+1].seconds
				#print "##### next diff %f" % diff
				if diff < self.anim_duration/900.0:
					#print "HURRY UP %f" % ((self.lyrics.entities[self.actualLine+2].seconds - self.lyrics.entities[self.actualLine+1].seconds)*900)
					self.animation.duration = (self.lyrics.entities[self.actualLine+2].seconds - self.lyrics.entities[self.actualLine+1].seconds)*1000
					
			
			alarm = int(self.lyrics.entities[self.actualLine+1].seconds*1000-time)
			#print "Wait %f" % alarm
			#alarm = int((self.lyrics.entities[self.actualLine+1].seconds - self.lyrics.entities[self.actualLine+0].seconds)*1000 - self.animation.timeline.getTime())
			
			#print "next anim at %d" % alarm
			"""
			self.animation.startupDelay = 0#alarm
			self.animation.duration = alarm
			self.animation.steps = int(alarm/30)
			"""
			self.animation.startupDelay = alarm
			self.animation.start(self.update)
			#self.animation.addTaskOnFinish(self.onAnimEnd)

	def resumeAnimation(self):
		if self.timeline:
			self.timeline.resume()
		if self.animation:
			self.animation.resume()
		
	def pauseAnimation(self):
		#print 'pause animation'
		print "************\nSTOP\n************"
		self.timeline.pause()
		if self.animation != None:
			self.animation.pause()
						
	def stopAnimation(self):
		#print 'stop animation'
		#self.anim_fraction = 0.0 ????
		if self.animation != None:
			self.animation.stop()
			
	def setMode(self, mode):
		self.mode = mode
		#self.updateLyrics()
		if mode == 'playing':
			#self.button.setVisible(False)
			self.time.setVisible(False)
			self.time.animation.stop()
			#self.startLyricsLoop()
		elif mode == 'editing':
			self.stopAnimation()
			self.actualLine = 0
			#self.button.setVisible(True)
			self.time.setVisible(True)
			self.time.animation.start(self.update_timelabel)
			#self.startLyricsLoop()
			
	def stopEditing(self, widget, event):
		self.setMode('playing')
		
	def on_key_press(self, event):
		key = gtk.gdk.keyval_name(event.keyval)
		if event.state & gtk.gdk.CONTROL_MASK:
			print 'Ctrl'
		elapsed = self.timeline.getTime()/1000.0
		print elapsed
		if key == 'Down' or key == 'Up':
			if key == 'Down':
				if event.state & gtk.gdk.SHIFT_MASK:
					offset = -0.1
					self.seekDown.setText("-0.1s")
				else:
					offset = -0.5
					self.seekDown.setText("-0.5s")
					
				self.seekDown.setVisible(True)
				self.seekDown.animation.start(self.seekDown.redraw)
			else:
				if event.state & gtk.gdk.SHIFT_MASK:
					offset = 0.1
					self.seekUp.setText("+0.1s")
				else:
					offset = 0.5
					self.seekUp.setText("+0.5s")
					
				self.seekUp.setVisible(True)
				self.seekUp.animation.start(self.seekUp.redraw)
			
			self.timeOffset += offset
			print "total offset: %f" % self.timeOffset
			for line in self.lyrics.entities:
				if line.seconds != 0:
					line.seconds += offset
			
			#self.setElapsed(elapsed)
			self.startAnimation()
			self.redraw()
			
		if key == 'space' and self.mode == 'editing':
			if self.actualLine + 1 < len(self.lyrics.entities):
				#print elapsed
				self.lyrics.entities[self.actualLine+1].seconds = elapsed # TODO delay
				#self.lyrics.entities[self.actualLine+1].text[0] = str(round(elapsed,2))+self.lyrics.entities[self.actualLine+1].text[0]
				
				self.editAnim.start(self.editAnimUpdate)
				"""
				if self.anim_timer != None:
					gobject.source_remove(self.anim_timer)
				self.count = self.anim_steps
				self.anim_timer = gobject.timeout_add(self.anim_duration/self.anim_steps, self.anim)
				"""
	def editAnimUpdate(self):
		self.anim_fraction = self.editAnim.fraction
		self.redraw()
		
	_buffer1 = None
	_buffer2 = None
	
	def createBuffer(self):
		#print self.root.root.window
		self.__buffer = gtk.gdk.Pixmap(self.root.root.window, self.bounds.width, 50, -1)
		
	
	def setAlignment(self):
		if self.layout != None:
			if self.textAlign == ALIGN_CENTER:
				align = pango.ALIGN_CENTER
			elif self.textAlign == ALIGN_LEFT:
				align = pango.ALIGN_LEFT
			else:
				align = pango.ALIGN_RIGHT
			
			self.layout.set_alignment(align)
	#######################
	##### Draw lyrics #####
	#######################
	lastState = None
	
	def drawComponent(self, ctx):
		#print "redraw Lyrics Panel"
		#print self.anim_fraction
		#print self.actualLine
		t_start = gobject.get_current_time()
		matrix = ctx.get_matrix()
		self.text_matrix = cairo.Matrix(1, matrix[1], matrix[2], 1, matrix[4], matrix[5])
		lastScale = self.gscale
		self.gscale = matrix[0]
		if self.gscale != lastScale:
			self.resizeBuffers()
		
		ctx.set_matrix(self.text_matrix)
		#ctx.scale(1.0/scale_x, 1.0/scale_y)
		
		if self.layout == None:
			self.layout = ctx.create_layout()
			self.setAlignment()
			self.layout.set_font_description(self.font)
		
		self.clipBounds = Rectangle(*[int(ceil(v))for v in ctx.clip_extents()])
		#print self.clipBounds
		#print 'draw: '+str(ctx.clip_extents())
		
		#ctx.set_source_rgba(1, 0, 0, 1)
		#ctx.rectangle(0, 0, self.bounds.width, self.bounds.height)
		#ctx.fill()
		
		#ctx.set_operator(cairo.OPERATOR_SOURCE)
		ctx.set_operator(cairo.OPERATOR_OVER)
		
		if not self.text_scale or not self.font:# or not self.color_highlight or not self.color_normal:
			return
		
		#########################
		##### RENDER LYRICS #####
		#########################
		if self.lyrics_need_update:
			self.updateLyrics()
		
		"""
		if ([self.actualLine, self.animation.fraction] == self.lastState): #TODO add lyrics to state
			print "EQUAL"
			#return
		else: print "NOT EQUAL"
		self.lastState = [self.actualLine, self.animation.fraction]
		"""
		#options = ctx.get_font_options()
		#options.set_hint_metrics(cairo.HINT_METRICS_OFF)
		#options.set_hint_style(cairo.HINT_STYLE_FULL)
		#ctx.set_font_options(options)
		
		if self._buffer1 == None:
			self._buffer1 = PixmapBuffer(self.root.root.window, self.bounds.width*self.gscale*0.9, 20)
		if self._buffer2 == None:
			self._buffer2 = PixmapBuffer(self.root.root.window, self.bounds.width*self.gscale, 20)
		
		if self.anim_fraction == 1.0:
			self.anim_fraction = 0.0
			self.textForAnimation = None
			self.actualLine += 1
		if self.render_lyrics and self.lyrics and self.actualLine < len(self.lyrics.entities):
			#fraction = math.sin(self.animation.fraction*1.57)
			fraction = math.sin(self.anim_fraction*1.57) # non-linear interpolation of animation fraction
			#fraction = self.anim_fraction
			
			###############################
			##### Compute positioning #####
			###############################
			
			if ([self.actualLine, self.anim_fraction] != self.lastState): #TODO add lyrics to state
				actual_y = (self.bounds.height - self.lyrics.entities[self.actualLine].trimmed_height*self.text_scale)/2.0
				if self.actualLine+1 < len(self.lyrics.entities):
					next_y = (self.bounds.height - self.lyrics.entities[self.actualLine+1].trimmed_height*self.text_scale)/2.0
					# center y position, interpolation between actual and next texts y-center position (if their heights are diffrent)
					self.center_y = actual_y+(next_y-actual_y)*fraction
				else:
					self.center_y = actual_y
				self.center_y = int(self.center_y)
				# texts moving animation - actual text must translate about it's height by y-axle
				self.motion_y = -fraction*(self.lyrics.entities[self.actualLine].height)
					 
				# decreasing scale text factor in animation
				self.dec_scale = self.text_scale-fraction*(self.text_scale-1.0)
				# increasing scale text factor in animation
				self.inc_scale = 1.0+fraction*(self.text_scale-1.0)
				
				# must be integer due to nice text rendering on raster
				
				if self.textAlign == ALIGN_CENTER:
					self.center_x = int(((self.bounds.width-self.bounds.width/self.text_scale)/2.0)*self.gscale)
				elif self.textAlign == ALIGN_LEFT:
					self.center_x = 0
				else:
					self.center_x = int((self.bounds.width-self.bounds.width/self.text_scale)*self.gscale)
				#self.center_x = ((self.bounds.width-self.bounds.width/self.text_scale)/2.0)*self.gscale
				
				#print (self.center_y + self.motion_y)*self.gscale
				
				if self.textForAnimation != self.actualLine:
					#print "treba to %f" % self.anim_fraction
					self.textForAnimation = self.actualLine
					# resize text buffer if needed
					if self.lyrics.entities[self.actualLine].height*self.gscale > self._buffer1.height:
						self._buffer1.resize(self._buffer1.width, self.lyrics.entities[self.actualLine].height*self.gscale)
					
					self._buffer1.clear()
					#options = self._buffer1.ctx.get_font_options()
					#options.set_hint_metrics(cairo.HINT_METRICS_OFF)
					#self._buffer1.ctx.set_font_options(options)
					self.drawScaledLyric(self._buffer1.ctx, self.lyrics.entities[self.actualLine], 1)
			
					# create text path for next line for animation
					if self.actualLine + 1 < len(self.lyrics.entities):
						#self.next_text_i = self.getScaledText(ctx, self.lyrics.entities[self.actualLine+1], self.text_scale)
						ctx.set_source_rgba(1, 1, 1, 1)
				
						# resize text buffer if needed
						if self.lyrics.entities[self.actualLine+1].height*self.gscale*self.text_scale > self._buffer2.height:
							self._buffer2.resize(self._buffer2.width, self.lyrics.entities[self.actualLine+1].height*self.gscale*self.text_scale)
				
						self._buffer2.clear()
						self.drawScaledLyric(self._buffer2.ctx, self.lyrics.entities[self.actualLine+1], self.text_scale)
				
				options = ctx.get_font_options()
			
			#else: print "NETREBA"
			self.lastState = [self.actualLine, self.anim_fraction]
			
			self.dec_color = (self.color_highlight[0]+(self.color_normal[0]-self.color_highlight[0])*fraction,
						 self.color_highlight[1]+(self.color_normal[1]-self.color_highlight[1])*fraction,
						 self.color_highlight[2]+(self.color_normal[2]-self.color_highlight[2])*fraction,
						 self.color_highlight[3]+(self.color_normal[3]-self.color_highlight[3])*fraction)
			self.inc_color = (self.color_normal[0]+(self.color_highlight[0]-self.color_normal[0])*fraction,
						 self.color_normal[1]+(self.color_highlight[1]-self.color_normal[1])*fraction,
						 self.color_normal[2]+(self.color_highlight[2]-self.color_normal[2])*fraction,
						 self.color_normal[3]+(self.color_highlight[3]-self.color_normal[3])*fraction)
			
			#################################
			##### And finally Rendering #####
			#################################
			
			ctx.translate(0, (self.center_y + self.motion_y)*self.gscale)
			#ctx.translate(0, int((self.center_y + self.motion_y)*self.gscale))
			
			self.dec_scale2 = 1.0-fraction*(1.0 - 1.0/self.text_scale)
			
			##############################
			##### render actual text #####
			##############################
			
			if self.anim_fraction == 0.0:
				# render actual line - scaled at maximum
				ctx.set_source_rgba(self.color_highlight[0], self.color_highlight[1], self.color_highlight[2], self.color_highlight[3])
				self.drawScaledLyric(ctx, self.lyrics.entities[self.actualLine], self.text_scale)
				
			else:
				ctx.save()
				#ctx.translate(center_x, 0)
				ctx.translate(self.center_x*fraction, 0)
				ctx.scale(self.dec_scale, self.dec_scale)
				
				"""
				ctx.set_source_rgba (*self.dec_color)
				ctx.rectangle(0,0, self.bounds.width, 50)
				ctx.fill()
				ctx.set_operator(cairo.OPERATOR_DEST_IN)
				ctx.set_source_pixmap(self.__buffer, 0, 0)
				ctx.paint()
				"""
				ctx.rectangle(0,0, self._buffer1.width, self._buffer1.height)
				ctx.clip()
				ctx.set_source_pixmap(self._buffer1.pixmap, 0, 0)
				ctx.paint()
				ctx.set_operator(cairo.OPERATOR_IN)
				ctx.set_source_rgba (*self.dec_color)
				ctx.rectangle(0,0, self._buffer1.width, self._buffer1.height)
				ctx.fill()
				
				ctx.restore()
			
			###############################
			##### render texts before #####
			###############################
			#"""
			
			
			ctx.translate(self.center_x, 0) #CENTER
			# set graphics state for text before and after actual lyrics line
			ctx.set_source_rgba (self.color_normal[0], self.color_normal[1], self.color_normal[2], self.color_normal[3])
			ctx.save()
			i = self.actualLine
			y = self.center_y + self.motion_y
			while i > 0 and y > 0:
				i -= 1
				ctx.translate(0, -self.lyrics.entities[i].height*self.gscale)
				#matrix = ctx.get_matrix()
				#print matrix
				#self.drawScaledLyric(ctx, self.lyrics.entities[i], 1, cache = self.anim_fraction != 0.0)
				self.drawScaledLyric(ctx, self.lyrics.entities[i], 1, cache = True)
				#extents = self.last_text_extents[1]
				#ctx.rectangle(*extents)
				#ctx.stroke()
				#ctx.fill()
				y -= self.lyrics.entities[i].height

			ctx.restore()
			#"""
			###############################
			##### render texts behind #####
			###############################
			# height after text scale operation
			h = self.lyrics.entities[self.actualLine].trimmed_height*self.dec_scale+self.lyrics.entities[self.actualLine].height-self.lyrics.entities[self.actualLine].trimmed_height
			h = int(h)
			ctx.translate(0, h*self.gscale)
			i = self.actualLine
			y = self.center_y + self.motion_y + h
			while i+1 < len(self.lyrics.entities) and y < self.bounds.height:
				i += 1
				if i == self.actualLine+1:
					# next text - need some animation
					ctx.save()
					#ctx.set_source_rgba (*self.inc_color)
					ctx.set_source_rgba (*self.inc_color)
					if fraction != 0:
						ctx.save()
						# align to center, correction after scale operation
						ctx.translate(-self.center_x*fraction, 0)
						self.inc_scalei = 1.0/self.text_scale + (1.0 - (1.0/self.text_scale))*fraction
						ctx.scale(self.inc_scalei, self.inc_scalei)						
						#ctx.set_source_rgba (*self.inc_color)
						#ctx.mask(self.next_text_i)
						ctx.rectangle(0,0, self._buffer2.width, self._buffer2.height)
						ctx.clip()
						ctx.set_source_pixmap(self._buffer2.pixmap, 0, 0)
						ctx.paint()
						ctx.set_operator(cairo.OPERATOR_IN)
						ctx.set_source_rgba (*self.inc_color)
						ctx.rectangle(0,0, self._buffer2.width, self._buffer2.height)
						ctx.fill()

						ctx.restore()
						
					if fraction == 0:
						self.drawScaledLyric(ctx, self.lyrics.entities[i], 1)
						#text = self.getScaledText(ctx, self.lyrics.entities[i], 1);ctx.mask(text);ctx.fill()
						
					ctx.restore()
					# height after text scale operation
					h = self.lyrics.entities[i].trimmed_height*self.inc_scale+self.lyrics.entities[i].height-self.lyrics.entities[i].trimmed_height
					ctx.translate(0, h*self.gscale)
					y += h
				else:
					#self.drawScaledLyric(ctx, self.lyrics.entities[i], 1, cache = self.anim_fraction != 0)
					self.drawScaledLyric(ctx, self.lyrics.entities[i], 1, cache = True)
					ctx.translate(0, self.lyrics.entities[i].height*self.gscale)
					y += self.lyrics.entities[i].height
		
		# make soft edges
		ctx.save()
		ctx.set_operator(cairo.OPERATOR_DEST_OUT)
		ctx.set_source(self.gradient)
		ctx.rectangle(0, 0, self.bounds.width, 10)
		ctx.fill()
		ctx.scale(1, -1)
		ctx.translate(0, -self.bounds.height)
		ctx.set_source(self.gradient)
		ctx.rectangle(0, 0, self.bounds.width, 10)
		ctx.fill()

		ctx.set_source_rgba(1,0,1, 1.0-self.alpha)
		ctx.rectangle(0, 0, self.bounds.width, self.bounds.height)
		ctx.fill()
		ctx.restore()
		
		ctx.save()
		ctx.set_operator(cairo.OPERATOR_DEST_OVER)
		ctx.scale(self.bounds.width/300.0, self.bounds.height/130.0)
		self.theme.render(ctx,'background')
		ctx.restore()
		
		"""
		# render message instead of lyrics
		if not self.render_lyrics:
			ctx.translate(center_x, self.bounds.height/2)
			ctx.set_source_rgba (1, 1, 1, 1)
			self.layout.set_text(self.message)
			ctx.show_layout(self.layout)
		"""
		#while gtk.events_pending():
		#	gtk.main_iteration(False)
		t_end = gobject.get_current_time()
		#print 'rendering time: %s' % (t_end-t_start)

		
	def updateLyrics(self):
		#print 'Update of Lyrics splitting: %s'% self.font
		self.layout.set_width(int(pango.SCALE*self.bounds.width*0.9/self.text_scale))
		if self.lyrics:
			for lyric in self.lyrics.entities:
				lyric.height = 0
				lyric.trimmed_height = 0
				lyric.lengths = []
				tmp = 0
				
				lyric.linesBounds = []
				self.layout.set_font_description(self.font)
				for text in lyric.text:
					self.layout.set_text(text)
					height = self.layout.get_pixel_size()[1]
					bounds = self.layout.get_pixel_extents()[1]
					
					bounds = [bounds[0]+self.bounds.width*0.05/self.text_scale, bounds[1], bounds[2], bounds[3]]
					lyric.linesBounds.append(bounds)
					lyric.height += height
					if len(text) == 0:
						tmp += height
					else:
						lyric.trimmed_height += height
						lyric.trimmed_height += tmp
						tmp = 0
					for line in range(0, self.layout.get_line_count()):
						lyric.lengths.append(self.layout.get_line(line).length)
				
				#"""
				if self.lyrics.showTranslation and lyric.translation != None:
					lyric.tlengths = []
					for ttext in lyric.translation:
						self.layout.set_font_description(self.translationFont)
						self.layout.set_text(ttext)
						height = self.layout.get_pixel_size()[1]
						lyric.height += height
						lyric.trimmed_height += height
						
						for line in range(0, self.layout.get_line_count()):
							lyric.tlengths.append(self.layout.get_line(line).length)
				#"""
			self.lyrics_need_update = False

	def drawScaledLyric(self, ctx, lyric, scale = 1, cache = False):
		backup_layout_width = self.layout.get_width()
		backup_font_size = self.font.get_size()
		backup_translationFont_size = self.translationFont.get_size()
		
		ctx.save()
		self.font.set_size(int(backup_font_size * scale * self.gscale))
		self.translationFont.set_size(int(backup_translationFont_size * scale * self.gscale))
		self.layout.set_font_description(self.font)
		self.layout.set_width(int(pango.SCALE*self.bounds.width*self.gscale*scale/self.text_scale))

		j = 0
		for length in reversed(lyric.lengths):
			if length == 0:
				j+=1
			else:
				break
				
		i = len(lyric.lengths) - j
		stext = ""
		for text in lyric.text:
			stext += text
					
		start = 0
		#for length in lyric.lengths:
		linesBounds = []
		for l in range(0, i):
			length = lyric.lengths[l]
			if l < len(lyric.linesBounds):
				bounds = lyric.linesBounds[l]
				intersection = Rectangle(*[int(ceil(v))for v in bounds]).intersect(self.clipBounds)
				if intersection.width == 0 or intersection.height == 0:
					#print "NETREBA"
					#print intersection
					#break
					pass
				else:
					#print "TREBA"
					pass
				ctx.save()
				ctx.scale(scale, scale)
				#ctx.rectangle(*bounds)
				#ctx.fill()
				ctx.restore()
			
			text = stext[start : start+length].strip()
			start += length # new start position
			
			if cache and False:
				self.drawText(ctx, text, scale)
			else:
				#"""
				self.layout.set_text(text)
				ctx.show_layout(self.layout)
				bounds = self.layout.get_pixel_extents()[1]
				#print bounds
				#ctx.rectangle(*bounds)
				#ctx.fill()
				#print "____"
				#print self.layout.get_extents()
				#print self.layout.get_pixel_extents()
				#print self.layout.get_pixel_size()
				linesBounds.append(self.layout.get_pixel_extents())
				if l == 0:
					self.last_text_extents = self.layout.get_pixel_extents()
				#self.last_text_extents[1]
				height = self.layout.get_pixel_size()[1]
			
				ctx.translate(0, height)
				#"""
			
		"""
		stext = ""
		for text in lyric.text:
			stext += text
					
		start = 0
		for length in lyric.lengths:
			text = stext[start : start+length].strip()
			start += length # new start position
			self.layout.set_text(text)
			ctx.show_layout(self.layout)
				
			height = self.layout.get_pixel_size()[1]				
			ctx.translate(0, height)
		"""
		"""
		j = 0
		for line in reversed(lyric.text):
			if len(line) == 0:
				j+=1
			else:
				break
		i = len(lyric.text) - j
		#for text in lyric.text:
		#print "%s %d %d %d" % (lyric.text, len(lyric.text), j, i)
		for t in range(0, i):
			text = lyric.text[t]
			self.layout.set_text(text)
			ctx.show_layout(self.layout)
				
			height = self.layout.get_pixel_size()[1]				
			ctx.translate(0, height)
		"""
		if self.lyrics.showTranslation and lyric.translation != None:
			self.layout.set_font_description(self.translationFont)
			ttext = ""
			for text in lyric.translation:
				ttext += text
			start = 0
			for tl in lyric.tlengths:
				self.layout.set_text(ttext[start:start+tl])
				start += tl
				#self.layout.set_text(lyric.translation)
				#self.layout.set_text("[ preklad ]")
				#break
				ctx.show_layout(self.layout)
				height = self.layout.get_pixel_size()[1]				
				ctx.translate(0, height)
		
			self.layout.set_font_description(self.font)
			
		# empty lines at the end
		for t in range(0, j):
			self.layout.set_text("")
			ctx.show_layout(self.layout)
				
			height = self.layout.get_pixel_size()[1]				
			ctx.translate(0, height)
			
		ctx.restore()
		
		self.font.set_size(backup_font_size)
		self.translationFont.set_size(backup_translationFont_size)
		#self.layout.set_font_description(self.font)
		self.layout.set_width(backup_layout_width)
	
	textCache = {}
	
	def drawText(self, ctx, text, scale):
		key = "%s:%f" % (text, scale)
		if not self.textCache.has_key(key):
			textBuffer = PixmapBuffer(self.root.root.window, self.bounds.width*self.gscale*0.9, 18)
			self.layout.set_text(text)
			textBuffer.clear()
			textBuffer.ctx.set_source_rgba(*self.color_normal)
			textBuffer.ctx.show_layout(self.layout)
			height = self.layout.get_pixel_size()[1]
			ctx.set_source_pixmap(textBuffer.pixmap, 0, 0)
			ctx.paint()		
			ctx.translate(0, height)
			self.textCache[key] = [textBuffer, height]
		else:
			#print "Text From Cache !"
			textBuffer = self.textCache[key][0]
			height     = self.textCache[key][1]
			#ctx.set_operator(cairo.OPERATOR_SOURCE)
			ctx.set_operator(cairo.OPERATOR_OVER)
			#ctx.set_operator(cairo.OPERATOR_IN)
			ctx.set_source_pixmap(textBuffer.pixmap, 0, 0)
			#ctx.rectangle(0,0,self.bounds.width*self.gscale*0.9, 15)
			#ctx.fill()
			ctx.paint()
			"""
			ctx.rectangle(0,0, textBuffer.width, textBuffer.height)
			ctx.clip()
			ctx.set_source_pixmap(textBuffer.pixmap, 0, 0)
			ctx.paint()
			ctx.set_operator(cairo.OPERATOR_IN)
			ctx.set_source_rgba (*self.dec_color)
			ctx.rectangle(0,0, self._buffer1.width, self._buffer1.height)
			ctx.fill()
			"""
			ctx.translate(0, height)
    
	def on_drag_data_received(self, widget, dc, x, y, sel_data, info, timestamp):
		print sel_data
		content = sel_data.get_text()
		print content
		if content.startswith("file:///"):
			import gnomevfs
			print content
			path = gnomevfs.get_local_path_from_uri(content)
			print path
			f = open(path.strip(), "r")
			lyrics = f.read()
			f.close()
		else:
			lyrics = content
		self.setUnsynchLyrics(lyrics)

	def setUnsynchLyrics(self, unsynchLyrics):
		lines = unsynchLyrics.rsplit(os.linesep)
		lyrics = Lyrics([])
		LyricEntity([''], 999)
		for line in lines:
			if len(line) == 0:
				lyrics.entities[-1].text.append(line)
			else:
				lyrics.entities.append(LyricEntity([line], 999))
		lyrics.entities[0].seconds = 0
		
		self.stopAnimation()
		self.lyrics = lyrics
		self.lyrics_need_update = True
		self.setMode('editing')
		self.redraw()
	
	
	def contains(self, x, y):
		x = int(x - self.bounds.x)
		y = int(y - self.bounds.y)
		if x > 0 and x < self.bounds.width-1 and y > 0 and y < self.bounds.height-1:
			return True
		return False
		
		
	def getLyrics(self):
		if self.lyrics != None:
			text = ""
			for entity in self.lyrics.entities:
				mins = int(entity.seconds) / 60
				secs = entity.seconds % 60
				#mili = int(100*(entity.seconds-int(entity.seconds)))
				time = "[%d:%.2f]" % (mins, secs)
				#time = time.replace(' ', '0')
				for line in entity.text:
					text += time + line + os.linesep
			return text
	
