from gtk.gdk import Rectangle

from LyricsPanel import LyricsPanel

class LyricsAnimation(LyricsPanel):
	def __init__(self):
		LyricsPanel.__init__(self)
	
	#"""
	def drawComponent(self, ctx):
		if self.layout == None:
			self.layout = ctx.create_layout()
			self.setAlignment()
			self.layout.set_font_description(self.font)
		
		if self.lyrics_need_update:
			self.updateLyrics()
		
		self.clipBounds = Rectangle(*ctx.clip_extents())
		
		if self.anim_fraction == 1.0:
			self.anim_fraction = 0.0
			self.textForAnimation = None
			self.actualLine += 1
			
		if self.lyrics != None and self.actualLine < len(self.lyrics.entities):
			print self.anim_fraction
			
			center_y = 60
			ctx.translate(0, center_y)
			
			if self.actualLine > 0:
				
				ctx.set_source_rgba(*self.color_normal)
				ctx.translate(0, -self.lyrics.entities[self.actualLine-1].height)
				
				#if self.anim_fraction > 0:
				ctx.save()
				ctx.translate(-200*self.anim_fraction, 0)
				self.drawScaledLyric(ctx, self.lyrics.entities[self.actualLine-1])
				ctx.restore()
				ctx.translate(0, self.lyrics.entities[self.actualLine-1].height)
			
			ctx.set_source_rgba(*self.color_highlight)
			ctx.translate((self.anim_fraction)*200, 0)
			self.drawScaledLyric(ctx, self.lyrics.entities[self.actualLine])
			ctx.translate(-self.anim_fraction*200, 0)
			if self.actualLine+1 < len(self.lyrics.entities):
				if self.anim_fraction > 0:
					ctx.save()
					ctx.translate((1-self.anim_fraction)*-200, 0)
					self.drawScaledLyric(ctx, self.lyrics.entities[self.actualLine+1])
					ctx.restore()
				
				ctx.translate(0, max(self.lyrics.entities[self.actualLine].height, self.lyrics.entities[self.actualLine+1].height))
				ctx.set_source_rgba(*self.color_normal)
				if self.anim_fraction > 0:
					ctx.translate(-200*self.anim_fraction, 0)
				self.drawScaledLyric(ctx, self.lyrics.entities[self.actualLine+1])
				
			#self.layout.set_text("")
	#"""
