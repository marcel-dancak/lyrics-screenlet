import os
import re
import shutil

def format2pattern(format):
	pattern = format
	# if "\" is escaped then it must be at first position, otherwise
	# all other characters will be double-escaped ("\\.", "\\(", ...)
	chars_to_escape = ("\\", ".", "(", ")", "[", "]", "+", "*", "|")
	for char in chars_to_escape:
		pattern = pattern.replace(char, "\\%s" % char)
	
	pattern = pattern.replace("%{artist}", "(?P<artist>.+)")
	pattern = pattern.replace("%{album}", "(?P<album>.+)")
	pattern = pattern.replace("%{title}", "(?P<title>.+)")
	return pattern

class Convertor(object):
	#__slots__ = ("lyrics_folder", "format", "dir_count", "dir_format", "dir_pattern", "file_format", "file_pattern")
	def __init__(self, lyrics_folder, old_format, new_format):
		self.lyrics_folder = lyrics_folder
		self.old_format = old_format
		self.new_format = new_format
		# kwformat = format for keywords (dictionary) string formatting
		self.new_kwformat = new_format.replace("%{artist}", "%(artist)s").replace("%{album}", "%(album)s").replace("%{title}", "%(title)s")
		self.dir_format = os.path.dirname(old_format)
		self.dir_pattern = format2pattern(self.dir_format)
		self.dir_count = self.dir_format.count("/")
		
		self.file_format = os.path.basename(old_format)
		self.file_pattern = format2pattern(self.file_format)
		
		self.files_to_rename = {}

	def convert(self):
		os.path.walk(self.lyrics_folder, self._collect_lyrics_files, None)
		out_lyrics_folder = self.lyrics_folder#os.path.join(self.lyrics_folder, "tmp")
		src_dirs = set()
		dest_dirs = set()
		src_files = []
		dest_files = []
		for old_folder, data in self.files_to_rename.iteritems():
			print old_folder
			coppied = 0
			src_dir = os.path.join(self.lyrics_folder, old_folder)
			coppied_into_same_folder = False
			for old_filename, new_relative_path in data:
				src = os.path.join(src_dir, old_filename)
				dest = os.path.join(out_lyrics_folder, new_relative_path)
				#print print new_filename
				#print src
				#print dest
				dest_dir = os.path.dirname(dest)
				dest_dirs.add(dest_dir)
				if not os.path.exists(dest_dir):
					os.makedirs(dest_dir)
				shutil.copy2(src, dest)
				src_files.append(src)
				dest_files.append(dest)
				
				if src_dir == dest_dir:
					coppied_into_same_folder = True
				coppied += 1
			print "coppied_into_same_folder:", coppied_into_same_folder
			print "coppied:", coppied, "/", len(os.listdir(os.path.join(self.lyrics_folder, old_folder)))
			if coppied == len(os.listdir(os.path.join(self.lyrics_folder, old_folder))):
				src_dirs.add(src_dir)
		
		for src_file in src_files:
			if src_file not in dest_files:
				os.remove(src_file)
		
		while src_dirs:
			src_dirs_reduced = set()
			for src_dir in src_dirs:
				if src_dir not in dest_dirs or len(os.listdir(src_dir)) == 0:
					#print "delete", src_dir
					shutil.rmtree(src_dir)
					parent = os.path.dirname(src_dir)
					if len(parent) > len(self.lyrics_folder):
						src_dirs_reduced.add(parent)
			src_dirs = src_dirs_reduced
		print dest_dirs
		

	def _collect_lyrics_files(self, arg, dirname, fnames):
		dirname = dirname.replace(self.lyrics_folder, "").lstrip(os.path.sep)
		#print dirname, dirname.count("/")
		#print self.dir_format
		if dirname.count("/") == self.dir_count:
			dir_pattern = re.compile(self.dir_pattern)
			dir_match = dir_pattern.match(dirname)
			if dir_match:
				metadata = dir_match.groupdict()
				file_pattern = re.compile(self.file_pattern)
				lyrics_files = []
				
				new_file_kwformat = os.path.basename(self.new_kwformat)
				for fname in fnames:
					file_match = file_pattern.match(fname)
					if file_match:
						metadata.update(file_match.groupdict())
						#print metadata
						#lyrics_files.append((fname, new_file_kwformat % metadata))
						new_folder = os.path.dirname(self.new_kwformat) % metadata
						lyrics_files.append((fname, os.path.join(new_folder, new_file_kwformat % metadata)))
						#self.files_to_rename.append(os.path.join(dirname, fname))
						#print self.new_kwformat % metadata
				
				if lyrics_files:
					#print new_folder
					self.files_to_rename[dirname] = lyrics_files
					#print new_folder
					#print lyrics_files

	def can_be_converted(self):
		p = re.compile("%{(\w+)}")
		old_metadata = p.findall(self.old_format)
		new_metadata = p.findall(self.new_format)
		print old_metadata
		print new_metadata
		for x in new_metadata:
			if x not in old_metadata:
				return False
		return True

new_format = "%{artist} - %{album}/%{title}.lrc"
old_format = "%{artist} - %{album} - %{title}.lrc"

#old_format = "%{artist} - %{album}/%{title}.lrc"
#new_format = "%{artist} - %{album} - %{title}.lrc"

#new_format = "%{artist}/%{album}/%{title}.lrc"
#old_format = "%{artist} - %{album} - %{title}.lrc"
#convert("/home/dencer/Lyrics", old_format)
convertor = Convertor("/home/dencer/LyricsX", old_format, new_format)
#convertor.convert()
convertor.can_be_converted()
print len(convertor.files_to_rename)
"""
for new_folder, data in convertor.files_to_rename.iteritems():
	print new_folder
	print data
	print "-----------------------"
"""
