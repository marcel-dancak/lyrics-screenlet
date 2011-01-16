import traceback
from widget import *
import pango

class CairoCanvas(AbstractVirtualCanvas):
	def expose(self, ctx):
	#def expose(self, widget, event):
		#log.debug("rendering wave")
		#ctx = self.root.window.cairo_create()
		#printRect(event.area, 'CREAR AREA ')
		#ctx.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
		#ctx.clip()
		#area = event.area
		
		clip = ctx.clip_extents()
		area = gtk.gdk.Rectangle(int(clip[0]), int(clip[1]), int(clip[2]-clip[0]), int(clip[3]-clip[1]))
		#area = gtk.gdk.Rectangle(clip[0], clip[1], clip[2]-clip[0], clip[3]-clip[1])
		
		#printRect(area, 'REDRAW AREA ')
		ctx.scale(self.scale, self.scale)
		self.redraw_all(ctx, area)
		self.notScaled = None
		#"""
		"""
		try:
			self.redraw_all(ctx, area)
		except Exception,e:
			traceback.print_exc()
		"""
		
	def redraw_all(self, ctx, area):
		clip = area.copy()
		
		area.x /= self.scale
		area.y /= self.scale
		area.width /= self.scale
		area.height /= self.scale
		
		if self.notScaled != None and abs(self.notScaled.width-area.width) <= 1 and abs(self.notScaled.height-area.height) <= 1:
			#printRect(self.notScaled, "Using Not Scaled")
			area = self.notScaled
		else:
			area.width  += 1
			area.height += 1
			#area.x += 1
			#area.y += 1
		
		#if self.notScaled != None:
		#	printRect(self.notScaled, "notScaled = ")
		#ctx.scale(self.scale, self.scale)
		for widget in self.widgets:
			
			if not widget.isVisible():
				continue
			widget_bounds = widget.getBounds()
			intersect = area.intersect(widget_bounds)

			if intersect.width == 0 or intersect.height == 0:
				continue
			#printRect(widget_bounds, 'bounds ')
			ctx.save()
			#ctx.reset_clip()
			ctx.rectangle(intersect)
			ctx.clip()
			#printRect(intersect, 'intersec ')#widget.bounds
			ctx.translate(widget_bounds.x, widget_bounds.y)
			
			try:
				#log.debug("rendering %s" % widget)
				widget.draw(ctx)
			except Exception, e:
				print "Error in rendering %s widget: %s" % (widget, e)
				traceback.print_exc()
			ctx.restore()
		#log.debug("Rendering finished")
		
class ImageButton(Widget):
	image     = None
	imageOver = None

	anim_steps = 6
	anim_fraction = 0.0
	anim_timer = None
	frame = 0
	img_scale = 1.0
	pixbuf = None
	
	bounds_backup = None
	enterAnim     = None
	pressedAnim   = None
	visibleAnim   = None
	rectangleBounds = False
	visibilityThreshold = 100
	
	overAlpha = 0.0
	
	def __init__(self, image, imgOver):
		Widget.__init__(self)
		self.image = image
		self.imageOver = imgOver
		self.registerEvent('button_pressed' , self.startPressedAnim)
		self.registerEvent('button_released', self.startReleasedAnim)
		self.registerEvent('mouse_enter'    , self.enter_notify)
		self.registerEvent('mouse_leave'    , self.leave_notify)
	
	def __setattr__(self, name, value):			
		Widget.__setattr__(self, name, value)
		if name == "image":
			self.updateDimensions()
		
	def setTheme(self, theme):
		Widget.setTheme(self, theme)
		if self.image != None:
			image = self.image
		else:
			if self.imageOver != None:
				image = self.imageOver
			else:
				print "ImageButton without image, wtf?"
		self.updateDimensions()
	
	# scale attribute only scale image, not widget dimmensions, so it is needed to override getBounds
	# to doesn't count scale value
	def getBounds(self):
		return self.bounds.copy()
		
	def updateDimensions(self):
		if not self.theme:
			return
		dimensions = self.theme.get_image_dimensions(self.image)
		if dimensions != None:
			self.setSize(dimensions[0], dimensions[1])
			#stride = self.bounds.width * 4
			#data = array.array('c', chr(0) * self.bounds.width * self.bounds.height * 4)
			#buff = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, self.bounds.width, self.bounds.height, stride)
			# better way
			#buff = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.bounds.width, self.bounds.height)
			
			self.pixbuf = self.theme.get_pixbuf(self.image)
			#print "%s, %s" % (self.bounds.width, self.bounds.height)
		
	def setOverAlpha(self, alpha):
		self.overAlpha = alpha
		
	def drawComponent(self, ctx):
		if not self.theme:
			print "can't render widget, theme not set"
			return
		
		alpha = self.getTotalAlpha()
		
		if not self.enabled:
			self.scale = [1.0, 1.0]
			self.overAlpha = 0.0
		#ctx.save()
		
		ctx.translate(self.bounds.width/2.0, self.bounds.height/2.0)
		ctx.rotate(self.rotation)
		ctx.scale(self.scale[0], self.scale[1])
		ctx.translate(-self.bounds.width/2.0, -self.bounds.height/2.0)
		ctx.set_operator (cairo.OPERATOR_OVER)
		#ctx.set_source_rgb(0, 1, 0)
		#ctx.rectangle(0, 0, self.bounds.width, self.bounds.height)
		#ctx.stroke()
		#self.theme.render(ctx, self.image)
		#self.theme.render(ctx, self.imageOver)
		self.theme.render_with_alpha(ctx, self.image, (1.0-self.overAlpha)*alpha)
		self.theme.render_with_alpha(ctx, self.imageOver, self.overAlpha*alpha)
		
		if not self.enabled:
			ctx.set_operator (cairo.OPERATOR_DEST_OUT)
			ctx.set_source_rgba(0.1, 0.1, 0.1, 0.8)
			ctx.rectangle(0, 0, self.bounds.width, self.bounds.height)
			ctx.fill()
		#ctx.restore()
		"""
		ctx1.scale(1.0/1.3, 1/1.3)
		ctx1.set_source_surface(self.buff)
		ctx1.paint()
		"""
	def setVisible(self, visible):
		Widget.setVisible(self, visible)
		if visible and self.visibleAnim != None:
			self.visibleAnim.start(self.redraw)
			
		if not visible and self.visibleAnim != None:
			self.visibleAnim.stop()
		
	def setVisibleAnimation(self, anim):
		self.visibleAnim = anim
		
	def setEnterAnimation(self, anim):
		self.enterAnim = anim
		
	def setPressedAnimation(self, anim):
		self.pressedAnim = anim
		
	def startPressedAnim(self, widget, event):
		if self.pressedAnim != None:
			self.pressedAnim.start(self.redraw)
			
	def startReleasedAnim(self, widget, event):
		if self.pressedAnim != None:
			self.pressedAnim.start(self.redraw, reverse = True)
			
	def enter_notify (self, widget, event):
		#print 'enter'
		if self.enterAnim != None:
			self.enterAnim.start(self.redraw)
		
	def leave_notify (self, widget, event):
		#print 'leaveee'
		if self.enterAnim != None:
			self.enterAnim.start(self.redraw, reverse = True)
		
	def contains(self, x, y):
		bounds = self.getBounds()
		if x > 0 and x < bounds.width-1 and y > 0 and y < bounds.height-1:
			if not self.rectangleBounds and self.pixbuf != None and self.pixbuf.get_has_alpha():
				try:
					x = int(x)
					y = int(y)
					#print str(x)+', '+str(y)
					alpha =  selfa.pixbuf.get_pixels_array()[y][x][3][0]
					#alpha = self.theme.get_pixel(self.image, x, y)#[3]
					#print alpha
					if alpha < self.visibilityThreshold:
						return False
				except Exception, e:
					try:
						width  = self.pixbuf.get_width()
						height = self.pixbuf.get_height()
						#print "%d x %d size: %d" % (width, height, len(self.pixbuf.get_pixels()))
						strColor = self.pixbuf.get_pixels()[4*(width*y+x) : 4*(width*y+x+1)]
						alpha = ord(strColor[3])
						if alpha < self.visibilityThreshold:
							return False
					except Exception, e:
						print "Can't detect pixel alpha value in ImageButton, bounding box will be used. Cause: %s" % e
			
			return True
		return False
		
class DropDownList(Widget):
	
	items    = None
	selected = None
	label    = None
	unrolled = False
	itemSelectedCallbacks = None
	
	def __init__(self, items = []):
		Widget.__init__(self)
		self.itemSelectedCallbacks = []

		self.selectedItemLabel = Label("", fixedSize = True)
		self.addWidget(self.selectedItemLabel)
		
		self.selectedItemLabel.registerEvent('button_released', self.showList)
		self.registerEvent('button_released', self.showList)
		self.registerEvent('mouse_leave'    , self.mouse_leave)
		self.setItems(items)

	def setSize(self, width, height):
		Widget.setSize(self, width, height)
		self.selectedItemLabel.setSize(self.bounds.width-15, self.bounds.height - 4)
		self.selectedItemLabel.setPosition(2, (self.getHeight()-self.selectedItemLabel.getHeight())/2.0)

	def registerItemSelected(self, callback):
		self.itemSelectedCallbacks.append(callback)
		
	def setItems(self, items):	
		self.items = items
		if len(items) > 0:
			self.selectedItemLabel.setText(items[0])
		else:
			self.selectedItemLabel.setText("")

	def showItem(self, item):
		if self.unrolled == True:
			self.children = []
			self.selectedItemLabel.setText(item)
			self.addWidget(self.selectedItemLabel)
			self.bounds.y      = self.y
			self.bounds.height = self.height
			self.unrolled = False
			self.redraw()
	
	def itemClicked(self, widget, event):
		self.setSelected(widget.text)
		
	def setSelected(self, item):
		if item in self.items:
			self.showItem(item)
			for callback in self.itemSelectedCallbacks:
				callback(item)
		
	def showList(self, widget, event):
		#print "UNROLL"
		if self.unrolled == False and len(self.items) > 1:
			self.unrolled = True
			self.y = self.bounds.y
			self.height = self.bounds.height
			
			sortedItems = []
			for item in self.items:
				if item != self.selectedItemLabel.text:
					sortedItems.append(item)
			sortedItems.append(self.selectedItemLabel.text)
			
			self.children = []	
			labels = []
			
			itemLabelHeight = self.selectedItemLabel.getHeight()
			for item in sortedItems:
				label = Label(item)
				label.registerEvent('button_released', self.itemClicked)
				label.registerEvent('mouse_enter'    , self.enter_notify)
				label.registerEvent('mouse_leave'    , self.itemMouseLeave)
				label.setSize(self.selectedItemLabel.getWidth(), itemLabelHeight)
				if item != self.selectedItemLabel.text:
					label.alpha = 0.5
				labels.append(label)
				self.addWidget(label)
			
			y = 0
			for i in range(0, len(labels)):
				y += 2
				labels[i].setPosition(2, y)
				y += itemLabelHeight + 2
			
			self.bounds.y -= y-self.bounds.height
			self.bounds.height = y
			self.redraw()
		else:
			self.setSelected(self.selectedItemLabel.text)
	
	def enter_notify (self, widget, event):
		widget.alpha = 1.0
		widget.redraw()
	
	def itemMouseLeave(self, widget, event):
		#if widget.text != self.selected:
		widget.alpha = 0.5
		widget.redraw()
		
	def mouse_leave (self, widget, event):
		if not self.contains(event.x, event.y):
			self.showItem(self.selectedItemLabel.text)
			self.redraw()
		
	def drawComponent(self, ctx):
		alpha = self.getTotalAlpha()
		
		width  = self.bounds.width - 1
		height = self.bounds.height -1
		
		ctx.set_source_rgba(1, 1, 1, 0.05*alpha)
		roundRectangle(ctx, 0, 0, width, height, 5)
		ctx.fill()
		
		ctx.set_line_width(2.0)
		ctx.set_source_rgba(1, 1, 1, 0.15*alpha)
		roundRectangle(ctx, 1, 1, width, height, 5)
		ctx.stroke()
		
		ctx.set_line_width(1.0)
		if not self.unrolled:
			if len(self.items) > 1:
				ctx.set_source_rgba(1, 1, 1, 0.8*alpha)
			else:
				ctx.set_source_rgba(1, 1, 1, 0.2*alpha)
			ctx.new_sub_path()
			(2.0/3.0)*height
			ctx.move_to (width -3, (3.0/5.0)*height)
			ctx.line_to (width -6, (2.0/5.0)*height)
			ctx.line_to (width -9, (3.0/5.0)*height)
			ctx.stroke()
		else:
			ctx.set_source_rgba(1, 1, 1, 0.5*alpha)
			h = self.selectedItemLabel.getHeight() + 4
			w = self.selectedItemLabel.getWidth() - 3
			for i in range(1, len(self.items)):
				ctx.move_to (5, i*h)
				ctx.line_to (w, i*h)
				ctx.stroke()

class TextField(Widget):
	text = ""
	
	def __init__(self, width, height, text = ""):
		Widget.__init__(self)
		self.width = width
		self.height = height
		self.text = text
		self.setSize(width, height)
		self.registerEvent('key_pressed', self.keyPressed)
	
	def keyPressed(self, event):
		print event
		#print event.keyval
		self.text += gtk.gdk.keyval_name(event.keyval)
		self.redraw()
		
	def drawComponent(self, ctx):
		layout = ctx.create_layout()
		layout.set_width(self.width)
		layout.set_text(self.text)
		ctx.save()
		ctx.set_source_rgba(0,0,0,1)
		ctx.rectangle(0, 0, self.width, self.height)
		ctx.stroke()
		
		ctx.set_source_rgba(1,0,0,1)
		ctx.show_layout(layout)
		print "Info"
		
		pos = layout.get_cursor_pos(len(self.text))
		ctx.move_to(pos[0][0]/pango.SCALE, 0)
		ctx.line_to(pos[0][0]/pango.SCALE, 12)
		ctx.stroke()
		ctx.restore()
		
class Label(Widget):

	text = ""
	textExtents = None
	CENTER = 0
	LEFT   = 1
	align = LEFT
	minimalSize = None
	
	drawBackground = True
	textColor      = [1,1,1,0.8]
	bgColor        = [0.1, 0.1, 0.1, 0.9]
	font     = ["sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL]
	fontSize = 10
	initialised = False
	
	def __init__(self, text, fixedSize = False):
		Widget.__init__(self)
		self.fixedSize = fixedSize
		buff = cairo.ImageSurface(0, 10, 10)
		self.ctx = cairo.Context(buff)
		self.setText(text)
		self.initialised = True
		
	def __setattr__(self, name, value):
		Widget.__setattr__(self, name, value)
		#if name == 'scale' and self.initialised:
		#	self.setText(self.text)
			
	def setText(self, text):
		if not isinstance(text, str) or not isinstance(text, unicode):
			#print "ERRORRRR, I wanna string"
			text = str(text)			
		self.text = text
		
		self.ctx.select_font_face(*self.font)
		self.ctx.set_font_size(self.fontSize)
		self.textExtents = self.ctx.text_extents(text)
		
		if self.fixedSize == False:
			width  = self.textExtents[2] + 6
			height = self.textExtents[3] + 4
			if self.minimalSize != None:
				if width < self.minimalSize[0]:
					width = self.minimalSize[0]
				if height < self.minimalSize[1]:
					height = self.minimalSize[1]
			self.setSize(width, height)
		#self.redraw()
	
	def setMinimalSize(self, width, height):
		self.minimalSize = [width, height]
		
	def getPrefferedSize(self):
		if self.textExtents != None:
			return [self.textExtents[2], self.textExtents[3]]
		else:
			return [0, 0]
		
	def drawComponent(self, ctx):
		alpha = self.getTotalAlpha()
		if not self.enabled:
			alpha *= 0.5
		
		ctx.scale(*self.scale)
		self.textExtents = ctx.text_extents(self.text)
		
		
		width  = self.bounds.width  -1
		height = self.bounds.height -1
		if self.drawBackground:
			ctx.set_source_rgba(self.bgColor[0], self.bgColor[1], self.bgColor[2], self.bgColor[3]*alpha)
			#ctx.rectangle(0, 0, width, height)
			roundRectangle(ctx, 0, 0, width, height, 3)
			ctx.fill()
			
		#"""
		if self.align == self.CENTER:
			#print self.textExtents
			ctx.translate((width-self.textExtents[2])/2.0, (height-self.textExtents[3])/2.0)
		elif self.align == self.LEFT:
			ctx.translate(2, (height-self.textExtents[3])/2.0)
		#"""
		#ctx.move_to(0, -extents[1])
		#ctx.text_path(self.text)
		#ctx.stroke()
		
		color = list(self.textColor)
		ctx.set_source_rgba(self.textColor[0], self.textColor[1], self.textColor[2], self.textColor[3]*alpha)
		ctx.move_to(-self.textExtents[0], -self.textExtents[1])
		ctx.select_font_face(*self.font)
		ctx.set_font_size(self.fontSize)
		ctx.show_text(self.text)
		"""
		if not self.enabled:
			ctx.set_operator (cairo.OPERATOR_DEST_OUT)
			ctx.set_source_rgba(0.1, 0.1, 0.1, 0.8*alpha)
			ctx.rectangle(0, 0, self.bounds.width, self.bounds.height)
			ctx.fill()
		"""

