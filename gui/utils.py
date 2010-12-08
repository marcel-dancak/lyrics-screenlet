import sys
import traceback
import commands

os = commands.getoutput("uname -m")
print os
if os.find("64") != -1:
    print "x86_64"
    try:
        from bin.x86_64 import _glConfigUtil
    except:
        print traceback.print_exc()
            
else:
    print "x86"
    try:
        from bin.x86 import _glConfigUtil
    except:
        print traceback.print_exc()

import sys
import gobject
import pango
"""
import ctypes
class _PyGObject_Functions(ctypes.Structure):
   _fields_ = [
       ('register_class',
        ctypes.PYFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p,
                          ctypes.c_int, ctypes.py_object,
                          ctypes.py_object)),
       ('register_wrapper',
        ctypes.PYFUNCTYPE(ctypes.c_void_p, ctypes.py_object)),
       ('register_sinkfunc',
        ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.c_void_p)),
       ('lookupclass',
       ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.c_int)),
       ('newgobj',
        ctypes.PYFUNCTYPE(ctypes.py_object, ctypes.c_void_p)),
       ]

class PyGObjectCAPI(object):
    def __init__(self):
        addr = ctypes.pythonapi.PyCObject_AsVoidPtr(ctypes.py_object(gobject._PyGObject_API))
        self._api = _PyGObject_Functions.from_address(addr)

    def pygobject_new(self, addr):
        return self._api.newgobj(addr)
"""
def getGlConfigByVisualID(widget, visualid):
    config = _glConfigUtil.get_gl_config_by_visualid(widget, visualid)
    print config
    return config
    #capi = PyGObjectCAPI()
    #pyconfig = capi.pygobject_new(config)
    #print pyconfig
    #return pyconfig

def getGlConfig(widget, antialiasing = 0):
    try:
        print "py call get_gl_config"
        config = _glConfigUtil.get_gl_config(widget, antialiasing)
        print config
        if config == None or config == 0:
            #import AnotherFolderViewScreenlet
            #AnotherFolderViewScreenlet.showError("bla")
            raise Exception
        print "py finished get_gl_config"
        
        #capi = PyGObjectCAPI()
        #pyconfig = capi.pygobject_new(config)
        #print pyconfig
        return config
    except Exception, e:
        print "Troubles in getting OpenGL configuration from binary module: %s" % e
        import gtk.gtkgl
        config = [gtk.gdkgl.RGBA,
                  gtk.gdkgl.DEPTH_SIZE, 24,
                  gtk.gdkgl.RED_SIZE, 8,
                  gtk.gdkgl.BLUE_SIZE, 8,
                  gtk.gdkgl.GREEN_SIZE, 8,
                  gtk.gdkgl.ALPHA_SIZE, 8,

                  gtk.gdkgl.DOUBLEBUFFER,
                  gtk.gdkgl.STENCIL_SIZE, 8,
                  gtk.gdkgl.ACCUM_RED_SIZE, 8,
                  gtk.gdkgl.ACCUM_BLUE_SIZE, 8,
                  gtk.gdkgl.ACCUM_GREEN_SIZE, 8,
                  gtk.gdkgl.ACCUM_ALPHA_SIZE, 16,
                  gtk.gdkgl.ATTRIB_LIST_NONE]
        try:
            print "PYGTKGLEXT"
            print gtk.gdkgl.Config
            return gtk.gdkgl.Config(attrib_list=config)
        except gtk.gdkgl.NoMatches:
            config = [gtk.gdkgl.RGBA,
                  gtk.gdkgl.RED_SIZE, 8,
                  gtk.gdkgl.BLUE_SIZE, 8,
                  gtk.gdkgl.GREEN_SIZE, 8,
                  gtk.gdkgl.ALPHA_SIZE, 8,
                  gtk.gdkgl.ATTRIB_LIST_NONE]
            return gtk.gdkgl.Config(attrib_list=config)
            
    
def pangoLayoutSetHeight(pangoLayout, height):
    try:
        #print "py call layout_set_height"
        _glConfigUtil.layout_set_height(pangoLayout, height)
        #print "py finished layout_set_height"
    except:
        pass
"""
import Image
def thumbnail(path):
    image = Image.open(path)
    print dir(image)
    image.thumbnail((32,32), Image.BILINEAR)
    print image
    print image.info
    print image.mode
    print image.getpixel((10,0))  
thumbnail("/home/dencer/screen.png")
"""
