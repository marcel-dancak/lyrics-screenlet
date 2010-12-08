import httplib, urllib, urllib2

def request(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    print response.read()
    
def simple():
    f = urllib2.urlopen('http://localhost/')
    print f.read()

def upload():
    h = httplib.HTTPConnection("127.0.0.1")
    headers = {'Content-Type':'application/soap+xml; charset=utf-8', 'Host':'localhost'}
    h.request ('POST', '/alsongwebservice/service1.asmx', request, headers)
    return h.getresponse().read()

def post(url, values):
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    print response.read()

f = open("/home/dencer/Hudba/Test.lrc");
lyrics = f.read()
f.close()

url = 'http://localhost/'
url = 'http://webuser.byethost11.com/'

values = {'artist'    : "Michael Jackson's",
          'title'     : 'Test',
          'album'     : 'Dangerous',
          'lyrics'    : lyrics,
          }


query = {'artist'    : 'michael jackson',
          'title'   : 'Dangerous',
          'album'   : 'Dangerous',
          'user' : 'dencera'
          }

#def find(artist, album, title):
def find(values):
    data = urllib.urlencode(values)
    req = urllib2.Request(url+"search.php", data)
    response = urllib2.urlopen(req)
    print response.read()

def missing(values):
	data = urllib.urlencode(values)
	req = urllib2.Request(url+"missinglyrics.php", data)
	response = urllib2.urlopen(req)
	print response.read()
#request(url)
#post(url+"lyrics.php", values)
#find(query)

missing(query)