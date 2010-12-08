#!/usr/bin/env python
"""
import gtk 
import pygtk 

def quit_cb(widget, data = None): 
    if data: 
        data.set_visible(False) 
    gtk.main_quit() 

def cb(widget, data=None): 
    print 'cb' 

def popup_menu_cb(widget, button, time, data = None): 
    if button == 3: 
        if data: 
            data.show_all() 
            data.popup(None, None, None, 3, time) 

statusIcon = gtk.StatusIcon() 

menu = gtk.Menu() 
menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT) 
menuItem.connect('activate', quit_cb, statusIcon) 
menu.append(menuItem) 

sm = gtk.Menu() 
menuItem = gtk.MenuItem('asd') 
menuItem.set_submenu(sm) 
menuItem2 = gtk.MenuItem('asdf') 
menuItem2.connect('activate', cb) 
sm.append(menuItem2) 
menu.append(menuItem) 

statusIcon.set_from_stock(gtk.STOCK_HOME) 
statusIcon.set_tooltip("StatusIcon test") 
statusIcon.connect('popup-menu', popup_menu_cb, menu) 
statusIcon.set_visible(True) 

gtk.main()
"""

from animation import *

class MyClass(object):
	
	atrib = 0
	
	def method(self):
		print "Method"
		
m = MyClass()
print m
print m.__dict__
#print dir(m)

print m.__getattribute__('method')
print m.__getattribute__('atrib')

m.__getattribute__('method')()

t = TemplateAnimation(5, 200)
t.createAnimation(m, m)


