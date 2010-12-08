import commands
import traceback

os = commands.getoutput("uname -m")
print os
if os.find("64") != -1:
	print "x86_64"
	try:
		from lib.x86_64 import _minimize
	except:
		print traceback.print_exc()
		#print "trying to link compiled library"
		#print commands.getoutput("gcc -pthread -shared -Wl,-O1 -Wl,-Bsymbolic-functions -lgtk-x11-2.0 lib/x86_64/minimize_module.o -o lib/x86_64/_minimize.so -m64")
		#try:
		#	from lib.x86_64 import _minimize
		#except:
		#	print "Faild to link library, will work without it"
			
else:
	print "x86"
	try:
		from lib.x86 import _minimize
	except:
		print traceback.print_exc()
		#print "trying to link compiled library"
		#print commands.getoutput("gcc -pthread -shared -Wl,-O1 -Wl,-Bsymbolic-functions -lgtk-x11-2.0 lib/x86/minimize_module.o -o lib/x86/_minimize.so")
		#try:
		#	from lib.x86 import _minimize
		#except:
		#	print "Faild to link library, will work without it"


def set_icon_geometry(window, x, y, width, height):
	try:
		_minimize.set_icon_geometry(window, x, y, width, height)
	except Exception,e:
		print "faild to call: set_icon_geometry"
		print e
