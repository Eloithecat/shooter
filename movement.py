#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random, math

def random_up(limits) :
    """a position in upper screen"""
    return (random.randint(0, limits[0]), random.randint(-limits[1]/6, 0))

def pol2cart(radius, angle) :
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    return x, y

class Trajectory() :
    """a general position modifier"""
    def __init__(self, scene, mobile, params={}) :
        self.scene = scene
        self.mobile = mobile
        #set init position of mobile
        self.mobile.pos = (0, 0)

class Down(Trajectory) :
    """go downward"""
    def next_pos(self, pos, interval, time) :
        """compute new position from floats"""
        offset = self.mobile.speed * interval
        pos = pos[0] , pos[1] + offset
        return pos
        
class Up(Trajectory) :
    """go upward"""
    def next_pos(self, pos, interval, time) :
        """compute new position from floats"""
        offset = self.mobile.speed * interval
        pos = pos[0] , pos[1] - offset
        return pos
        
class Line(Trajectory) :
    """advance in a line with the given angle"""
    def __init__(self, scene, mobile, params={}) :
        Trajectory.__init__(self, scene, mobile, params={})
        #default trajectory is down
        if 'angle' not in params :
            self.angle = 180
        else :
            self.angle = params['angle']
        #convert angle from degree to radians
        self.angle = math.radians(self.angle) - math.pi/2
            
    def next_pos(self, pos, interval, time) :
        """compute new position from floats"""
        offset = self.mobile.speed * interval
        pos = pos[0] + offset*math.cos(self.angle) , pos[1] + offset*math.sin(self.angle)
        return pos

class Align(Trajectory) :
    """can focus on a target"""
    def __init__(self, scene, mobile) :
        Trajectory.__init__(self, scene, mobile)
        #variables to intermitently check for target
        self.last_check = 0
        self.target = None
        
    def search(self, time) :
        #update targets every seconds
        if time > self.last_check + 1000 :
            self.last_check = time
            #target healthier player !
            max_life = 0
            for item in self.scene.content :
                if item.ally and hasattr(item, 'life') :
                    if item.life > max_life :
                        max_life = item.life
                        self.target = item

    def next_pos(self, pos, interval, time) :
        """move only if has a target"""
        self.search(time)
        if self.target != None :
            return self.new_pos(pos, interval)
        else :
            return pos

class AlignV(Align) :
    """align vertically with ship"""
    def __init__(self, scene, mobile) :
        Align.__init__(self, scene, mobile)
        #set init position of mobile
        self.mobile.pos = random_up(self.scene.limits)

    def new_pos(self, pos, interval) :
        """compute new position from floats"""
        offset =  self.mobile.speed * interval
        #move only if far enough
        distance = abs(self.mobile.center[0] - self.target.center[0])
        if distance > offset :
            if self.target.center[0] > self.mobile.center[0] :
                pos = pos[0] + offset, pos[1]
            elif self.target.center[0] < self.mobile.center[0] :
                pos = pos[0] - offset, pos[1]
        return pos

class AlignH(Align) :
    """align horizontally with ship"""
    def __init__(self, scene, mobile) :
        Align.__init__(self, scene, mobile)
        #set init position of mobile
        self.mobile.pos = random_up(self.scene.limits)

    def new_pos(self, pos, interval) :
        """compute new position from floats"""
        offset =  self.mobile.speed * interval
        #move only if far enough
        distance = abs(self.mobile.center[1] - self.target.center[1])
        if distance > offset :
            if self.target.center[1] > self.mobile.center[1] :
                pos = pos[0] , pos[1] + offset
            elif self.target.center[1] < self.mobile.center[1] :
                pos = pos[0], pos[1] - offset
        return pos

class GoFront(AlignV) :
    """try to be in front of ship"""
    def new_pos(self, pos, interval) :
        pos = AlignV.new_pos(self, pos, interval)
        offset =  self.mobile.speed * interval
        #y coord to reach
        y = self.target.center[1] - self.scene.limits[1]/2
        #move only if far enough
        distance = abs(self.mobile.center[1] - y)
        if distance > offset :
            if y > self.mobile.center[1] :
                pos = pos[0] , pos[1] + offset
            elif y < self.mobile.center[1] :
                #dont go outside screen
                if pos[1] - offset > 0 :
                    pos = pos[0], pos[1] - offset
        return pos

class Circular(GoFront) :
    """orbit around"""
    def __init__(self, scene, mobile) :
        GoFront.__init__(self, scene, mobile)
        #set init position of mobile
        self.ref_pos = random_up(self.scene.limits)
        self.radius = 40
        self.init_angle = random.random() * math.pi * 2
        self.omega = random.random() / 1000 * math.pi * 2
        #one turn each second
        self.angular_speed = 2*math.pi / 1000
        
    def abs_pos(self, interval, time) :
        #rotate around reference
        angle = time * self.angular_speed + self.init_angle
        #oscillating radius
        radius = self.radius * math.sin(self.omega * time)
        return pol2cart(radius, angle)

    def rel_pos(self, interval, time) :
        self.ref_pos = GoFront.next_pos(self, self.ref_pos, interval, time)
        return self.ref_pos

    def next_pos(self, pos, interval, time) :
        """add dynamic (relative to others) and passive trajectories"""
        xrel, yrel = self.rel_pos(interval, time)
        xabs, yabs = self.abs_pos(interval, time)
        return xrel+xabs, yrel+yabs
        
class OscillationDown(Trajectory) :
    """go down while oscillating"""
    def __init__(self, scene, mobile, params={}) :
        Trajectory.__init__(self, scene, mobile, params)
        self.ref_pos = None
        self.randomV = random.random()/2
        self.randomH = random.random()*2*math.pi
        if 'amplitude' not in params :
            self.amplitude = 5
        else :
            self.amplitude = params['amplitude']
            
    def rel_pos(self, pos, interval, time) :
        """falling line position (we compute an absolute position relative from this one"""
        if self.ref_pos == None :
            self.ref_pos = (pos[0],
            pos[1] + self.mobile.speed * interval + self.randomV)
        else :
            self.ref_pos = (self.ref_pos[0],
            self.ref_pos[1] + self.mobile.speed * interval + self.randomV)
        return self.ref_pos
            
    def abs_pos(self, interval, time) :
        """sinusoidal oscillation"""
        x = math.sin(self.randomH + time/200.) * self.amplitude
        y = 0
        return x, y

    def next_pos(self, pos, interval, time) :
        """add dynamic (relative to others) and passive trajectories"""
        xrel, yrel = self.rel_pos(pos, interval, time)
        xabs, yabs = self.abs_pos(interval, time)
        return xrel+xabs, yrel+yabs
