import urllib
import urllib2
import traceback

URL = 'http://webuser.byethost11.com/'
successful = []
unsuccessful = []
for n in range(1,1210):
	print n
	try:
		req = urllib2.Request(URL+"query.php", urllib.urlencode({'id': n}))
	
		response = urllib2.urlopen(req)
		lyrics = response.read()
		response.close()
		#print lyrics
		f = open("backup/%d.lrc" % n, "w")
		f.write(lyrics)
		f.close()
		successful.append(n)
	except Exception, ex:
		unsuccessful.append(n)
		#traceback.print_exc()
		print "%d - %s" % (n, str(ex))
		

print "Successful:"
print successful
print "-------------"
print "Unsuccessful:"
print unsuccessful
