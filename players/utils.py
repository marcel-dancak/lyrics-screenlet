import gnomevfs

def get_local_path_from_uri(uri):
	if uri != None and uri != "":
		try:			
			local_path = gnomevfs.get_local_path_from_uri(uri)
			#print "converting URI to local_path"
			return local_path
		except Exception, e:
			print e
			print "Cannot convert URI: \"%s\"to local path" % uri
			print "URI calss: %s" % uri.__class__
			try:
				unicodeUri = unicode(str(uri), 'utf-8')
				local_path = gnomevfs.get_local_path_from_uri(uri)
				return local_path
			except Exception, e:
				print e
				print "Cannot convert unicoded URI: \"%s\"to local path" % uri
		return uri
