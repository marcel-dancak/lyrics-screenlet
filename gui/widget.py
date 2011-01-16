#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

import logging
log = logging.getLogger("LyricsScreenlet")

import cairo
import gobject
import gtk
import os
#import array
import sys
import math
from math import ceil
import traceback

#############################################################
# This classes are probably only temporary solution, later can
# be replaced with some library like goocanvas, clutter
#############################################################

def printRect(res, ret = ''):
	print "%s %d, %d, %d, %d" % (ret, res.x, res.y, res.width, res.height)
	
class Theme:

	delegate = None
	
	#pixmap = gtk.gdk.bitmap_create_from_data(None, "0", 1, 1)
	#pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 1, 1)
	#self.pixmap = gtk.gdk.Pixmap(self.window, self.width, self.height)
			
	def __init__(self, theme):
		self.delegate = theme
		
	def __getattr__(self, name):
		try:
			return self.delegate.__getattribute__(name)
		except:
			return self.delegate.__getattr__(name)
	
	def render_with_alpha(self, ctx, name, alpha):
		#print 'with alpha'
		if self.svgs.has_key(name):
			ctx.push_group()
			self.svgs[name].render_cairo(ctx)
			ctx.pop_group_to_source()
			ctx.paint_with_alpha(alpha)
		elif self.pngs.has_key(name):
			ctx.set_source_surface(self.pngs[name], 0, 0)
			ctx.paint_with_alpha(alpha)

	def get_image_dimensions(self, name):
		if self.svgs.has_key(name):
			return self.svgs[name].get_dimension_data()
		elif self.pngs.has_key(name):
			png = self.pngs[name]
			return [png.get_width(), png.get_height()]
		else:
			return None
	
	def get_pixbuf(self, name):
		if self.svgs.has_key(name):
			return gtk.gdk.pixbuf_new_from_file(self.path+os.sep+name+".svg")
		elif self.pngs.has_key(name):
			return gtk.gdk.pixbuf_new_from_file(self.path+os.sep+name+".png")
			
	def get_pixel(self, name, x, y):
		if self.svgs.has_key(name):
			self.pixmap = gtk.gdk.bitmap_create_from_data(None, "0"*256, 16, 16)
			ctx = self.pixmap.cairo_create()
			self.svgs[name].render_cairo(ctx)
			#print dir(self.pixmap)

			#print (self.pixmap.get_image(0,0,16,16).get_colormap())
			#print dir(ctx)
			#self.pixbuf = self.svgs[name].get_pixbuf()
			#self.pixbuf = gtk.gdk.pixbuf_new_from_file(self.path+os.sep+name+".svg")
			#array = self.pixbuf.get_pixels_array()
			#rgba = array[y][x].tolist()
			#self.pixbuf = None
			#del array
			#array = None
			
			return 255
		elif self.pngs.has_key(name):
			png = self.pngs[name]
			return [png.get_width(), png.get_height()]

def roundRectangle(ctx, x, y, width, height, radius):
	ctx.new_sub_path()
	ctx.arc (x+radius,y+radius, radius, math.pi, math.pi*1.5)      # left-top
	ctx.line_to (width-radius, y)                                  # go right
	ctx.arc (width-radius, y+radius, radius, math.pi*1.5, 0)       # right-top
	ctx.line_to (width, height-radius)                             # go down
	ctx.arc (width-radius, height-radius, radius, 0, math.pi/2.0)  #right-bottom
	ctx.line_to(x+radius, height)                                  # go left
	ctx.arc(x+radius, height-radius, radius, math.pi/2.0, math.pi) # left-bottom
	#ctx.line_to(x, radius)
	ctx.close_path()

# CHECK	
class Rectangle(gtk.gdk.Rectangle):
	def __setattr__(self, name, value):
		gtk.gdk.Rectangle.__setattr__(self, name, value)
		print name
		
class AbstractVirtualCanvas(object):
	root         = None
	parent       = None
	widgets      = None
	lastSelected = None
	theme        = None
	scale        = 1.0
	alpha        = 1.0
	
	rendering      = False
	blockRedrawing = False
	makeSnapshot       = False
	
	originalRedrawArea = None
	mouse_drag_widget  = None
	postPosition       = None
	tooltips_enabled   = False

	def __init__(self, root):
		self.widgets = []
		self.root = root
		size = root.get_size()
		self.bounds = gtk.gdk.Rectangle(0, 0, size[0], size[1])
		self.root.connect("motion-notify-event",self.motion_notify_event)
		self.root.connect("button-press-event", self.button_press)
		self.root.connect("key-press-event", self.key_press)
		self.root.connect("drag_data_received", self.drag_data_received)
		#self.root.connect("expose-event", self.expose)	
		self.root.connect("button-release-event", self.button_release)
		self.root.connect("configure_event", self.configure_event)
		#self.root.connect("query-tooltip", self.tooltip_event)
		#self.root.set_tooltip_text("hey you")
		#self.root.set_has_tooltip(True)

	def configure_event(self, widget, event):
		if self.postPosition != None:
			log.debug("post position: "+str(event))
			self.setPosition(self.postPosition[0] , self.postPosition[1])
		self.postPosition = None
	
	def setTheme(self, theme):
		print "Set THEME"
		self.theme = Theme(theme)
		allWidgets = []
		for widget in self.widgets:
			self._children(widget, allWidgets)
			
		for widget in allWidgets:
			widget.setTheme(self.theme)
			
	def addWidget(self, widget):
		self.widgets.append(widget)
		widget.root = self
		widget.parent = self
		#for child in widget.children:
		#	self.addWidget(child)
			
	def setPosition(self, x, y):
		log.debug("move window to: [%d, %d]" % (x, y))
		self.root.move(x, y)
		
	def getPosition(self):
		return self.root.get_position()

	def setSize(self, width, height):
		log.debug("resize: [%d, %d]" % (width, height))
		self.root.resize(int(width*self.scale), int(height*self.scale))
		#self.widgets[0].bounds.width = width
		
	def setSizeThenPosition(self, width, height, x, y):
		log.debug("set size: %d, %d, then position: %d, %d" % (width, height, x, y))
		self.setSize(width, height)
		self.postPosition = [x, y]

	def processEvent(self, event):
		event.x /= self.scale
		event.y /= self.scale
	
	def translateEvent(self, widget, event):
		x = event.x-widget.bounds.x
		y = event.y-widget.bounds.y
		parent = widget.parent
		b = False
		while parent != None:
			
			x -= parent.bounds.x
			y -= parent.bounds.y			
			parent = parent.parent
			if parent != None:
				b = True
		#if b:print "event.x=%d event.y=%d x=%d y=%d" % (event.x, event.y, x, y)
		return [x,y]
			
	def _children(self, widget, l, addInvisible = True):
		if addInvisible or widget.isVisible():
			for child in reversed(widget.children):
				self._children(child, l, addInvisible)
			l.append(widget)
	"""
	def tooltip_event(self, widget, x, y, keyboard_mode, tooltip):
		print "TOOLTIP"
	"""
	def _check_tooltip(self):
		#print [event.x, event.y]
		if self.lastSelected != None and self.lastSelected != self.root and self.lastSelected.isEnabled():
			for callback in self.lastSelected.eventsCallbacks['tooltip_event']:
				callback(self.lastSelected, None)
		
	tooltip_timmer = None
	def motion_notify_event(self, widget, event):
		if self.tooltips_enabled:
			if self.tooltip_timmer != None:
				gobject.source_remove(self.tooltip_timmer)
			self.tooltip_timmer = gobject.timeout_add(300, self._check_tooltip)
		
		self.processEvent(event)
		#print (str(event.x)+', '+str(event.y))
		
		##### Mouse Drag Motion #####
		if self.mouse_drag_widget != None:
			for callback in self.mouse_drag_widget.eventsCallbacks['mouse_drag_motion']:
				callback(event)
			
		#print str(event.x)+', '+str(event.y)
		allWidgets = []
		for w in reversed(self.widgets):
			self._children(w, allWidgets, addInvisible=False)
		#print allWidgets
		
		selected = None
		#"""
		for wid in allWidgets:
			point = self.translateEvent(wid, event)
			if wid.isVisible() and wid.contains(point[0], point[1]):
				selected = wid
				#print "selected %s at x=%d y=%d" % (wid, point[0], point[1])
				# translate global event coordinates to it's relative coordinates
				event.x = point[0]
				event.y = point[1]
				break
		#"""
		"""
		for wid in self.widgets:
			if wid.isVisible() and wid.contains(event.x, event.y):
				selected = wid
				#break
		"""
		#print selected
		if selected != self.lastSelected and selected != None and selected.isEnabled():
			for callback in selected.eventsCallbacks['mouse_enter']:
				callback(selected, event)
			
		#if selected == None:
		#	selected = self.root

		#print str(selected)+', '+str(self.lastSelected)
		if selected != self.lastSelected and self.lastSelected != None and self.lastSelected != self.root and self.lastSelected.isEnabled():
			for callback in self.lastSelected.eventsCallbacks['mouse_leave']:
				callback(self.lastSelected, event)
		
		self.lastSelected = selected
	
	def button_press(self, widget, event):
		if self.tooltip_timmer != None:
			gobject.source_remove(self.tooltip_timmer)
		#print 'pressed'
		self.processEvent(event)
		#print self.lastSelected
		if self.lastSelected != None and self.lastSelected != self.root and self.lastSelected.isEnabled():
			for callback in self.lastSelected.eventsCallbacks['button_pressed']:
				callback(self.lastSelected, event)
			self.mouse_drag_widget = self.lastSelected
			#print 'DRAG '+str(self.mouse_drag_widget)
		
	def button_release(self, widget, event):
		print 'released'
		self.processEvent(event)
		
		if self.mouse_drag_widget != None:
			releasedWidget = self.mouse_drag_widget
		else:
			releasedWidget = self.lastSelected

		if releasedWidget != None and releasedWidget != self.root and releasedWidget.isEnabled():
			for callback in releasedWidget.eventsCallbacks['button_released']:
				callback(self.lastSelected, event)
			
		self.mouse_drag_widget = None
		
	def key_press(self, widget, event):
		for widget in self.widgets:
			for callback in widget.eventsCallbacks['key_pressed']:
				callback(event)
			
	def drag_data_received(self, widget, dc, x, y, sel_data, info, timestamp):
		for widget in self.widgets:
			for callback in widget.eventsCallbacks['drag_data_received']:
				callback(widget, dc, x, y, sel_data, info, timestamp)
		
	def redraw(self):
		size = self.root.get_size()
		self.redraw_area(self, gtk.gdk.Rectangle(0, 0, size[0], size[1]))
		self.notScaled = gtk.gdk.Rectangle(0, 0, size[0], size[1])
		#self.root.queue_draw()
	
	notScaled = None
	def redraw_area(self, widget, area):
		if self.notScaled == None:
			self.notScaled = area.copy()
		else:
			self.notScaled = self.notScaled.union(area)

		#printRect(area, 'Invalidate area (not scaled): ')
		area.x = area.x*self.scale
		area.y *= self.scale
		area.width = area.width*self.scale
		area.height *= self.scale
		#printRect(area, 'invalidate area: ')
		
		#self.root.window.invalidate_rect(area, True)
		#self.root.window.process_updates(True)
		#self.root.queue_draw()
		self.root.queue_draw_area(area.x, area.y, area.width, area.height)
		
		#size = self.root.get_size()
		#self.root.queue_draw_area(0, 0, size[0], size[1])
		
	def expose(self, ctx):
		pass
		
	def redraw_all(self, area):
		
		area.x /= self.scale
		area.y /= self.scale
		area.width /= self.scale
		area.height /= self.scale
		
		if self.notScaled != None and abs(self.notScaled.width-area.width) <= 1 and abs(self.notScaled.height-area.height) <= 1:
			#printRect(self.notScaled, "Using Not Scaled")
			area = self.notScaled
		else:
			pass
			#area.width  += 1
			#area.height += 1
		
		
		#print len(self.widgets)
		#printRect(area, "area")
		for widget in self.widgets:
			
			if not widget.isVisible():
				continue
			
			widget_bounds = widget.getBounds()
			intersect = area.intersect(widget_bounds)

			if intersect.width == 0 or intersect.height == 0:
				continue
			
			#printRect(widget_bounds, 'bounds ')
			
			"""
			ctx.save()
			ctx.reset_clip()
			ctx.rectangle(intersect)
			ctx.clip()
			#printRect(intersect, 'intersec ')#widget.bounds
			ctx.translate(widget_bounds.x, widget_bounds.y)
			"""
			
			
			try:
				log.debug("rendering %s" % widget)
				self.drawWidget(widget)
				#widget.draw(ctx)
			except Exception, e:
				print "Error in rendering %s widget: %s" % (widget, e)
			#"""
			#ctx.restore()
		#log.debug("Rendering finished")
	def drawWidget(self, widget):
		pass
		
	def getHeight(self):
		return self.root.get_size()[1]
		
	def getWidth(self):
		return self.root.get_size()[0]

	def getBounds(self):
		size = self.root.get_size()
		return gtk.gdk.Rectangle(0, 0, size[0], size[1])

class Widget(object):
	bounds     = None
	lastBounds = None
	parent     = None
	children   = None
	enabled    = True
	visible    = True
	opaque     = False # TODO
	
	alpha      = 1.0
	localAlpha = 1.0
	theme      = None
	rotation   = 0.0
	

	def __init__(self):
		object.__init__(self)
		self.eventsCallbacks = {
			'button_pressed'    : [],
			'button_released'   : [],
			'key_pressed'       : [],
			'drag_data_received': [],
			'mouse_drag_motion' : [],
			'mouse_enter'       : [],
			'mouse_leave'       : [],
			'tooltip_event'     : [],
			'resized'           : [] }

		self.children = []
		self.bounds = gtk.gdk.Rectangle()
		self.lastBounds = self.bounds
		self.scale = [1.0, 1.0]
	"""
	def __setattr__(self, name, value):
		object.__setattr__(self, name, value)
		print name
	"""
	def registerEvent(self, event, callback):
		self.eventsCallbacks[event].append(callback)
		#if self.events.has_key(event):
		#	self.events[event].append(callback)
		
	def setTheme(self, theme):
		self.theme = theme
		
	def setVisible(self, visible):
		self.visible = visible
		#self.redraw()
	
	def isVisible(self):
		return self.visible
		
	def setEnabled(self, enabled):
		self.enabled = enabled
		#self.redraw()
		
	def isEnabled(self):
		return self.enabled
		
	def setScale(self, scale):
		#print 'set scale'
		if not isinstance(scale, list):
			print "error: scale must be list!"
		self.scale = scale
	
	def setAlpha(self, alpha):
		self.alpha = alpha
	
	def setLocalAlpha(self, alpha):
		self.localAlpha = alpha
		
	def setSize(self, width, height):
		self.bounds.width = width
		self.bounds.height = height
		for callback in self.eventsCallbacks['resized']:
			callback(width, height)
	
	def getWidth(self):
		return self.bounds.width
		
	def getHeight(self):
		return self.bounds.height
		
	def getBounds(self):
		bounds = self.bounds.copy()
		#bounds.width = (bounds.width*self.scale[0])
		#bounds.height = (bounds.height*self.scale[1])
		#bounds.x = self.bounds.x - (self.scale[0]-1.0)*self.bounds.width/2.0
		#bounds.y = self.bounds.y - (self.scale[1]-1.0)*self.bounds.height/2.0
		
		return bounds
		
	def addWidget(self, widget):
		self.children.append(widget)
		widget.parent = self
		
	def getTotalAlpha(self):
		alpha = self.alpha
		parent = self.parent
		while parent != None:
			alpha *= parent.alpha
			parent = parent.parent
		return alpha
		
	def redraw(self):
		bounds = self.getBounds()
		parent = self.parent
		root = None
		while parent != None:
			root = parent
			bounds.x += parent.bounds.x
			bounds.y += parent.bounds.y
			parent = parent.parent
		
		#printRect(bounds, "redraw ")
		if root != None:
			root.redraw_area(self, bounds.union(self.lastBounds))
			self.lastBounds = bounds.copy()
		else:
			log.warning("widget: %s x=%d y=%d width=%d height=%d does not have root!" % (self, self.bounds.x, self.bounds.y, self.bounds.width, self.bounds.height))
		
	def setPosition(self, x, y):
		self.bounds.x = x
		self.bounds.y = y

	def drawComponent(self, ctx):
		pass
		
	def draw(self, ctx):
		if self.visible == True:
			ctx.save()
			self.drawComponent(ctx)
			ctx.restore()
			for child in self.children:
				ctx.save()
				#ctx.reset_clip()
				#ctx.rectangle(intersect)
				#ctx.clip()
				ctx.translate(child.bounds.x, child.bounds.y)
				child.draw(ctx)
				ctx.restore()
			
	
	def contains(self, x, y):
		bounds = self.getBounds()
		#x = int(x - bounds.x)
		#y = int(y - bounds.y)
		return (x > 0 and x < bounds.width-1 and y > 0 and y < bounds.height-1)
		
	def button_press_notify(self, widget, event):
		if self.button_pressed_callback != None: #TODO callable test
			self.button_pressed_callback(event)
			
	def key_press_notify(self, event):
		if self.key_press_callback != None:
			self.key_press_callback(event)
			
	def getTheme(self):
		return self.theme
