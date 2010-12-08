import engine
import time

global count
count = 0

def lyrics(lyric):
	global count
	count += 1	
	#print lyric
	print count
	
def finish():
	print count
	pass

"""
import xmms

print xmms.is_running()
playlistPosition = xmms.get_playlist_pos()
title = xmms.get_playlist_title(playlistPosition)
metaData = title.split(" - ")

title  = metaData[1]
artist = metaData[0]
print title
print artist
print xmms.get_output_time()/1000.0

e = engine.LyricsEngine(lyrics, finish)
song = {'title': title, 'artist': artist, 'album': None}
print engine.LYRICS_SOURCES
e.setLyricsSources(engine.LYRICS_SOURCES)

e.search(song)

print xmms.is_running()
playlistPosition = xmms.get_playlist_pos()
title = xmms.get_playlist_title(playlistPosition)
metaData = title.split(" - ")
"""


print engine.LYRICS_SOURCES
song = {'title': 'bad', 'artist': 'michael jackson', 'album': None}
e = engine.LyricsEngine(lyrics, finish)
e.setLyricsSources(['alsong', 'lrcdb', 'minilyrics'])
#e.search(song)

import socket
try:
	print socket.gethostbyname("lyrics.alsong.co.kr")
except:
	print "dns shit"

import ALSong
import minilyrics
alsong = ALSong.ALSongEngine(lyrics)
alsong.find(song)
mini = minilyrics.MiniLyricsEngine(lyrics)
#mini.find(song)
time.sleep(10)
print "and now stop"
e.stop()
