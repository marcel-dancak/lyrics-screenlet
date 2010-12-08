import httplib

def response1(request):
	block = 2048
	try:
		# lyrics.alsong.net server
		h = httplib.HTTPConnection("67.192.185.143")
		#h.set_debuglevel(1)
		headers = {'Content-Type':'text/xml; charset=utf-8', 'Host':'lyrics.alsong.net'}
		h.request ('POST', '/alsongwebservice/service1.asmx', request, headers)
		response = h.getresponse()
		while True:
			data = response.read(block)
			print data
			print len(data)
			if len(data) == 0:
				print "end of response"
				break
			
	except Exception, e:
		print e

def findByName(title, artist):

	request = open("query.xml").read()
	request = request.replace('title',  title)
	request = request.replace('artist', artist)
	xmlData = response1(request)
	print xmlData

	
findByName("ironic", "alanis morissette")
