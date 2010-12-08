import gtk
from animation import *

import utils


class TestClass(object):
	attrib = 0
	val    = None
	
	def setVal(self, val):
		self.val = val
		
	def update(self):
		print self.val


trayIcon = gtk.StatusIcon()
trayIcon.set_from_stock(gtk.STOCK_ABOUT)

window = gtk.Window()

def end():
	print "end"
	print window.skip_taskbar_hint
	#window.hide()
	#window.show()
	utils.set_icon_geometry(window, 500,100, 22, 22)
	window.skip_taskbar_hint = True
	window.iconify()
	#window.hide()

o = TestClass()
anim = Animation(1000, 10)
anim.addLinearTransition('attrib', 0.0, 1.0, LINEAR)
anim.addTaskOnFinish(end)
a = anim.create(o)
a.start(o.update)



window.connect("destroy", gtk.main_quit)

window.set_decorated(False)
window.set_app_paintable(True)
#gtk.window_set_default_icon_name('exaile')
#window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_TOOLBAR)
#window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
#window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DESKTOP)
window.show()
window.skip_taskbar_hint = True
gtk.main()
