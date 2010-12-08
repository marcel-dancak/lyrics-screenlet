#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!


class TimeInterpolator:

	def fraction(self, fraction):
		pass

class Linear:
	def fraction(self, fraction):
		return fraction
		

LINEAR = Linear()


class Animation(object):
	timer             = None
	startupDelayTimer = None
	stopped           = False
	
	startupDelay      = 0
	
	steps_count       = None
	duration          = None
	fraction          = 0.0
	
	targetObject      = None
	
	def __init__(self, duration, steps, loop = False):
		self.duration = duration
		self.steps_count = steps
		self.loop = loop
		self.endTasks = []
		self.transitions = []
		self.timeline = TimeLine()
	
	def create(self, targetObject):
		anim = Animation(self.duration, self.steps_count, self.loop)
		anim.transitions = list(self.transitions)
		anim.endTasks = self.endTasks
		anim.targetObject = targetObject
		return anim
		
	def addLinearTransition(self, attrib, startVal, endVal, timeline):
		if isinstance(startVal, list):
			self.addTransition(attrib, LinearVectorInterpolator(startVal, endVal), timeline)
		else:
			self.addTransition(attrib, LinearScalarInterpolator(startVal, endVal), timeline)
		
	def addTransition(self, callback, interpolator, timeline, *params):
		assert isinstance(interpolator, Interpolator), "Interpolator object expected, got: %s" % interpolator
		self.transitions.append([callback, interpolator, params])
		
	def addTaskOnFinish(self, callback, *params):
		self.endTasks.append([callback, params]) 

	def start(self, after_callback, reverse = False):
		#print "START ANIMATION"
		self.after_callback = after_callback
		self.reverse = reverse
		
		self.stop()
		
		if self.reverse:
			self.time = self.steps_count
		else:
			self.time = 0
			
		self.timeline.start()
		if self.startupDelay > 0:
			self.startupDelayTimer = gobject.timeout_add(self.startupDelay, self.__start)
		else:
			self.__start()
			
	def __start(self):
		self.timer = gobject.timeout_add(self.duration/self.steps_count, self.animation)
			
	def pause(self):
		print "############## Pause Animation"
		self.timeline.pause()
		self.stop()
		
	def stop(self):
		if self.timer != None:
			gobject.source_remove(self.timer)
		if self.startupDelayTimer != None:
			gobject.source_remove(self.startupDelayTimer)
			
			
	def resume(self):
		print "############## Resume Animation"
			
		if self.startupDelayTimer != None:
			print "resume startup delay"
			self.startupDelayTimer = gobject.timeout_add(int(self.startupDelay - self.timeline.getTime()*1000), self.__start)
		else:
			self.__start()
			
		self.timeline.resume()
		    
	def onFinish(self):
		for task in self.endTasks:
		    #task[0](*task[1])
		    self.call(task[0], *task[1])
		    
	def animation(self):
		if self.reverse:
		    self.time -= 1
		else:
		    self.time += 1
		
		if self.time < 0 or self.time > self.steps_count:
		    if self.loop:
		        self.start(self.after_callback, self.reverse)
		    else:
		        self.onFinish()
		    return False
		    
		self.fraction = self.time/float(self.steps_count)
		self.interpolateTransitions()
		self.after_callback()
		return True
	
	def interpolateTransitions(self):
		for transition in self.transitions:
			callback     = transition[0]
			interpolator = transition[1]
			params       = transition[2]

			args = list(params)
			value = interpolator.value(self.fraction)
			#args.extend(list(value))
			#print value
			args.append(value)
			try:
				#callback(*tuple(args))
				self.call(callback, *tuple(args))
			except Exception, e:
				traceback.print_exc()
	
	def call(self, attrib, *params):
		if callable(attrib):
			attrib(*params)
		else:
			attr = self.targetObject.__getattribute__(attrib)
			if callable(attr):
				attr(*params)
			else:
				self.targetObject.__setattr__(attrib, *params) #TODO params check
		
class Interpolator(object):
	def __init__(self, startVal, endVal):
		self.startVal = startVal
		self.endVal   = endVal
		
	def value(self, fraction):
		pass
		
"""
anim = Animation()
anim.addLinearTransition('attrname', 1.0, 0.0, TimeLine.LINEAR)
anim.addLinearTransition('attrname', [1.0, 1.0], [0.0, 0.0], TimeLine.LINEAR)


anim.addTransition(callback, LinearInterpolator([1.0, 1.0], [0.0, 0.0], extract_values = True), TimeLine.SIN)   --> callback(x, y)

anim.addTransition(callback, [1.0, 1.0], [0.0, 0.0], LINEAR) --> callback([x, y])
"""
import gobject
import traceback
    
class TimeLine(object):
	elapsed = 0
	real    = 0.0
	stopped = True
	
	def start(self):
		self.elapsed = 0
		self.real = gobject.get_current_time()
		self.stopped = False
		
	def setTime(self, time):
		print "SET TIME %f" % time
		self.elapsed = time
		self.real = gobject.get_current_time()
		
	def pause(self):
		if not self.stopped:
			self.elapsed += (gobject.get_current_time() - self.real)*1000
			self.stopped = True
		
	def resume(self):
		if self.stopped:
			self.real = gobject.get_current_time()
			self.stopped = False
		
	def getTime(self):
		if self.stopped:
			return self.elapsed
		
		return self.elapsed+(gobject.get_current_time() - self.real)*1000
			
		
class CompositeAnimation(object):
	timer             = None
	startupDelayTimer = None
	time = 0
	stopped = False
	startupDelay   = 0
	_delay_start   = 0
	_delay_elapsed = 0
	_step_start    = 0
	_step_elapsed  = 0
	
	steps_count = None
	duration = None

	fraction = 0.0

	def __init__(self, steps, duration, loop = False):
		self.steps_count = steps
		self.duration = duration
		self.loop = loop
		self.endTasks = []
		self.transitions = []
		self.timeline = TimeLine()
		#self.isRunning = False
		
	def addTransition(self, callback, interpolator, *params):
		assert isinstance(interpolator, Interpolator), "Interpolator object expected, got: %s" % interpolator
		self.transitions.append([callback, interpolator, params])
		
	def addTaskOnFinish(self, callback, *params):
		self.endTasks.append([callback, params]) 
		
	def pause(self):
		print "############## Pause Animation"
		self.timeline.pause()
		self.stop()
		if self.timer != None:
			self._step_elapsed += (gobject.get_current_time() - self._step_start) * 1000
			print "pause, elapsed %f" % self._step_elapsed
		if self.startupDelayTimer != None:
			self._delay_elapsed += (gobject.get_current_time() - self._delay_start) * 1000
		
	def resume(self):
		self.timeline.resume()
		print "############## Resume Animation"
		print self.timer
		if self.timer != None:
			self._step_start = gobject.get_current_time()
			print "resume main animation"
			#print "elapsed %f" % self._step_elapsed
			#print "wait %d" % int(self.duration/self.steps_count - self._step_elapsed)
			print self.fraction
			self.timer = gobject.timeout_add(int(self.duration/self.steps_count), self.animation)
			remaining_time = self.duration/self.steps_count - self._step_elapsed
			#if remaining_time > 5:
				#self.timer = gobject.timeout_add(int(remaining_time), self.animation)
			#else:
			#	self.animation()
			
		if self.startupDelayTimer != None:
			print "resume startup delay"
			self._delay_start = gobject.get_current_time()
			self.startupDelayTimer = gobject.timeout_add(int(self.startupDelay - self._delay_elapsed), self.__start)
		
	def stop(self):
		if self.timer != None:
			#print "STOP MAIN ANIMATION"
			gobject.source_remove(self.timer)
		if self.startupDelayTimer != None:
			gobject.source_remove(self.startupDelayTimer)

	def start(self, after_callback, reverse = False):
		#print "START ANIMATION"
		self.after_callback = after_callback
		self.stop()
		self.reverse = reverse
		
		if self.reverse:
			self.time = self.steps_count
		else:
			self.time = 0
		if self.startupDelay > 0:
			#gobject.timeout_add(self.startupDelay, lambda: self.minimize("paused") if not self.playing and (gobject.get_current_time() - self.lastStop) > 4.8 else 1)
			#gobject.timeout_add(self.startupDelay, lambda: self.timer = gobject.timeout_add(self.duration/self.steps_count, self.animation, reverse))
			self.startupDelayTimer = gobject.timeout_add(self.startupDelay, self.__start)
			self._delay_elapsed = 0
			self._delay_start = gobject.get_current_time()
		else:
			self.__start()
			
	def __start(self):
		self._step_start = 0
		self.timeline.start()
		self.timer = gobject.timeout_add(self.duration/self.steps_count, self.animation)
		    
	def onFinish(self):
		for task in self.endTasks:
		    task[0](*task[1])
		    
	def animation(self):
		self._step_elapsed = 0
		self._step_start = gobject.get_current_time()
		if self.reverse:
		    self.time -= 1
		else:
		    self.time += 1
		
		if self.time < 0 or self.time > self.steps_count:
		    if self.loop:
		        self.start(self.after_callback, self.reverse)
		    else:
		        self.onFinish()
		    return False
		    
		self.fraction = self.time/float(self.steps_count)
		self.interpolateTransitions()
		self.after_callback()
		return True
		
	def interpolateTransitions(self):
		for transition in self.transitions:
			callback     = transition[0]
			interpolator = transition[1]
			params       = transition[2]

			args = list(params)
			value = interpolator.value(self.fraction)
			#args.extend(list(value))
			#print value
			args.append(value)
			try:
				callback(*tuple(args))
			except Exception, e:
				traceback.print_exc()
				print args

class TemplateAnimation(object):
	transitions = None
	
	def __init__(self, steps, duration, loop = False):
		self.steps    = steps
		self.duration = duration
		self.loop = loop
		self.transitions = []
		
	def createAnimation(self, *objects):
		anim = CompositeAnimation(self.steps, self.duration, self.loop)
		for obj in objects:
			for transition in self.transitions:
				if callable(obj.__getattribute__(transition[0])):
					anim.addTransition(obj.__getattribute__(transition[0]), transition[1], transition[2])
				else:
					params = list(transition[2])
					params.insert(transition[0], 0)
					anim.addTransition(obj.__setattr__, transition[1], transition[2])
				print obj
		
		return anim
		
	def addTransition(self, attrName, interpolator, *params):
		self.transitions.append([attrName, interpolator, params])

"""
class GenericAnimation(CompositeAnimation)
	objects = None
	
	def start(self, objectsList, after_callback, reverse = False):
		self.objects = objectsList
		CompositeAnimation.start(self, after_callback, reverse = False)
	
	def addTransition(self, attrName, interpolator, *params):
		self.transitions.append([attrName, interpolator, params])
	
	def interpolateTransitions(self, fraction):
		for transition in self.transitions:
		    attrName     = transition[0]
		    interpolator = transition[1]
		    params       = transition[2]
		    
		    if 
		    args = list(params)
		    args.extend(list(interpolator.value(fraction)))

		    callback(*tuple(args))
"""

		
import math

class Interpolator:
    def value(self, fraction):
        pass

class LinearVectorInterpolator(Interpolator):
    def __init__(self, startValue, endValue):
        self.startValue = startValue#[].extend(startValue)
        self.endValue = endValue
        
    def value(self, fraction):
        result = []
        i = 0
        for val in self.startValue:
            result.append(val+(self.endValue[i]-val)*fraction)
            i+=1
        return result
    
            
class LinearScalarInterpolator(Interpolator):
    
    def __init__(self, startValue, endValue):
        self.startValue = startValue
        self.endValue = endValue
        
    def value(self, fraction):
        return self.startValue+(self.endValue-self.startValue)*fraction
    
class BezierInterpolator(Interpolator):
    
    def __init__(self, p1, p2, c1, c2, asList = True):
        self.p1 = []
        self.p1.extend(p1)
        #list(p1)
        self.p2 = list(p2)
        self.c1 = c1
        self.c2 = c2
        self.resultAsList = asList
        
    def linearIteraion(self, dist):
        pass
    
    def value(self, t):
        B0 = math.pow(1.0 - t, 3)
        B1 = 3.0 * t * math.pow(1.0 - t, 2)
        B2 = 3.0 * t * t * (1.0 - t)
        B3 = math.pow(t, 3)
        
        x = self.p1[0] * B0 + self.c1[0] * B1 + self.c2[0] * B2 + self.p2[0] * B3
        y = self.p1[1] * B0 + self.c1[1] * B1 + self.c2[1] * B2 + self.p2[1] * B3
        if self.resultAsList:
            return [x, y]
        else:
            return x, y
        #return [int(x), int(y)]
        
