import re
import gnomevfs
import traceback

pattern = re.compile("^\w+://")

def get_local_path_from_uri(uri):
	if uri != None and uri != "":
		if not isinstance(uri, basestring):
			unicodeUri = unicode(str(uri), 'utf-8')
		
		match = pattern.match(uri)
		if match:
			try:
				local_path = gnomevfs.get_local_path_from_uri(uri)
				#print "converting URI to local_path"
				return local_path
			except Exception, e:
				print "Converting URI: \"%s\"to local path failed" % uri
				traceback.print_exc()
				print "URI calss: %s" % uri.__class__
	return uri
