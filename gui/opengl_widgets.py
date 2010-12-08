import gtk.gtkgl
import utils
from OpenGL.GL import *

from widget import *

class OpenGlCanvas(AbstractVirtualCanvas):
    
    motionBlurEnabled = False
    motionBlur = False
	
    def __init__(self, root):
		AbstractVirtualCanvas.__init__(self, root)
		
		glconfig = utils.getGlConfig(root)
		#OK: 72, 74, 76, 78, 7a, 
		#glconfig = utils.getGlConfigByVisualID(root, int('0x73', 16))

		#glconfig = utils.getGlConfigByVisualID(root, 35)
		
		self.glarea = gtk.gtkgl.DrawingArea(glconfig)
		
		self.glarea.connect_after ('realize',         self.opengl_init)
		self.glarea.connect       ('expose_event',    self.expose)
		self.glarea.connect       ('configure_event', self.opengl_configure)
		root.connect              ('configure_event', self.window_configure)
		self.root.add(self.glarea)
		self.glarea.show()
		
    def window_configure(self, widget, event):
    	self.redraw()
		#self.opengl_drawing(gtk.gdk.Rectangle(0,0,event.width, event.height))
		
    def opengl_init(self, widget):
        print "OpenGl version: %s" % glGetString(GL_VERSION)
        print "OpenGl vendor: %s" % glGetString(GL_VENDOR)
        print "OpenGl renderer: %s" % glGetString(GL_RENDERER)
        try:
            print "OpenGl GLSL: %s" % glGetString(GL_SHADING_LANGUAGE_VERSION)
        except: pass
        print "OpenGl Extensions:"
        print glGetString(GL_EXTENSIONS)
        
        gldrawable = widget.get_gl_drawable()
        glcontext = widget.get_gl_context()
        if not gldrawable.gl_begin(glcontext):
            return
        
        #if not self.init_glsl(): sys.exit()
        #print glGetString(GL_EXTENSIONS).find("GL_ARB_imaging")
        #self.FBO1 = self.newTextureFramebuffer()
        #self.FBO2 = self.newTextureFramebuffer()
        #glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
        redAccumSize = glGetIntegerv(GL_ACCUM_RED_BITS)
        greenAccumSize = glGetIntegerv(GL_ACCUM_GREEN_BITS)
        blueAccumSize = glGetIntegerv(GL_ACCUM_BLUE_BITS)
        alphaAccumSize = glGetIntegerv(GL_ACCUM_ALPHA_BITS)
        
        print "ALPHA SIZE %d" % glGetIntegerv(GL_ALPHA_BITS)
        print "\nACUMULATION BUFER SIZE %d %d %d %d\n" % (redAccumSize, greenAccumSize, blueAccumSize, alphaAccumSize)
        if (redAccumSize & greenAccumSize & blueAccumSize & alphaAccumSize) > 0:
        	print "Motion Blur enabled"
        	self.motionBlurEnabled = True
        
        glEnable (GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_TEXTURE_2D)
        #glEnable(GL_DEPTH_TEST)
        
        glEnable(GL_SCISSOR_TEST)
        gldrawable.gl_end()
        #gobject.timeout_add(30, self.redraw)

    def opengl_configure(self, widget, event):
        print "OPEN GL CONFIGURE"
        
        gldrawable = widget.get_gl_drawable()
        glcontext = widget.get_gl_context()
        if not gldrawable.gl_begin(glcontext):
            return
        
        glViewport (0, 0, event.width, event.height)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity()
        glOrtho (0.0, event.width, 0.0, event.height, -100.0, 100.0)
        glMatrixMode (GL_MODELVIEW)
        glClearAccum(0.0, 0.0, 0.0, 0.0)
        glClear(GL_ACCUM_BUFFER_BIT)
        glClearColor(0, 0, 0, 0.0)
        
        gldrawable.gl_end()
        
        self.redraw()
    
                		
    def expose(self, widget, event):
        gldrawable = widget.get_gl_drawable()
        glcontext = widget.get_gl_context()
        if not gldrawable.gl_begin(glcontext):
            return
        #print "opengl expose"
        
        self.opengl_drawing(event.area)
        
        if gldrawable.is_double_buffered():
            gldrawable.swap_buffers()
        glFlush()
        gldrawable.gl_end()
        
    def opengl_drawing(self, area):
    	#self.doPreprocessTasks()
    	#print area
    	#print "transormed [%d %d %d %d]" % (area.x, self.getHeight()-area.y-area.height, area.width, area.height)
    	glScissor(area.x, self.getHeight()-area.y-area.height, area.width, area.height)
    	
    	#print glIsEnabled(GL_SCISSOR_TEST)
    	glClear(GL_COLOR_BUFFER_BIT)
        
        #if self.blockRendering == True:
        #    print "BLOCKING RENDERING"
        #    return
        
        glLoadIdentity()
        #glTranslate(0, self.getHeight()*self.scale, 0)
        #glScalef(self.scale, -self.scale, 1.0)
        glTranslate(0, self.getHeight(), 0)
        glScalef(self.scale, -self.scale, 1.0)
        
        self.redraw_all(area)
        #self.redraw_all(gtk.gdk.Rectangle(0, 0, self.getWidth(), self.getHeight()))
        #self.opengl_draw()
        #print "OPENGL DRAW"
            
        if self.motionBlurEnabled and self.motionBlur:
        	try:
	            q = 0.75
	            glAccum(GL_MULT, q)
	            glAccum(GL_ACCUM, 1.0-q)
	            glAccum(GL_RETURN, 1.0)
	        except:
	        	print "Motion Blur faild"
        
        #self.doPreprocessTasks()
        
        
    def drawWidget(self, widget):
    	glPushMatrix()
    	glTranslatef(widget.bounds.x, widget.bounds.y, 0)
    	widget.draw(None)
    	glPopMatrix()

class OpenGlWidget(Widget):
    
	texture = None
	background = None
	
	def __init__(self):
		Widget.__init__(self)
		self.texCoordinates = [0.0, 0.0, 1.0, 1.0]

	"""
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
			root.redraw_area(self, root.getBounds())
	"""
	def setPosition2(self, pos):
		self.bounds.x = pos[0]
		self.bounds.y = pos[1]

	def draw(self, ctx):
		if self.visible == True:
			matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
			xScale = matrix[0][0]
			yScale = matrix[1][1]
			#print [xScale, yScale]
			glPushMatrix()
			glTranslatef(self.bounds.width/2.0, self.bounds.height/2.0, 1)
			glScale(self.scale[0], self.scale[1], 1)
			glTranslatef(-self.bounds.width/2.0, -self.bounds.height/2.0, 1)
			
			self.drawComponent(ctx)
			for child in self.children:
				glPushMatrix()
				glTranslatef(child.bounds.x, child.bounds.y, 0)
				child.draw(ctx)
				glPopMatrix()
				
			glPopMatrix()
				
	def drawComponent(self, ctx):
		#print "opengl drawing"
		
		if self.background != None:
			glDisable(GL_TEXTURE_2D)
			glColor4f(1, 0, 1, 1)
			glBegin (GL_QUADS)
			glVertex2i   (0, 0)
			glVertex2i   (self.bounds.width, 0)
			glVertex2i   (self.bounds.width, self.bounds.height)
			glVertex2i   (0, self.bounds.height)
			glEnd()
	         	
		if self.texture != None:
			glEnable(GL_BLEND)
			glEnable(GL_TEXTURE_2D)
			#glDisable(GL_TEXTURE_2D)
			glBindTexture(GL_TEXTURE_2D, self.texture)
			#glBindTexture(GL_TEXTURE_RECTANGLE_ARB, self.texture)
			alpha = self.getTotalAlpha()*self.localAlpha
			
			glColor4f(1, 1, 1, 1*alpha)
			glBegin (GL_QUADS)
			glTexCoord2f (self.texCoordinates[0], self.texCoordinates[1])
			glVertex2i   (0, 0)
			glTexCoord2f (self.texCoordinates[2], self.texCoordinates[1])
			glVertex2i   (self.bounds.width, 0)
			glTexCoord2f (self.texCoordinates[2], self.texCoordinates[3])
			glVertex2i   (self.bounds.width, self.bounds.height)
			
			glTexCoord2f (self.texCoordinates[0], self.texCoordinates[3])
			glVertex2i   (0, self.bounds.height)
			glEnd()

	def free(self):
		for child in self.children:
			child.free()
		if self.texture != None:
			print "deleting texture: %d" % self.texture
			glDeleteTextures(self.texture)
	        
		
