#!/usr/bin/env python
#coding=utf-8

import kconfig
from gi.repository import Notify
import sys, os.path

__folder__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)));

class kcNotif():
	
	def __init__(self):
		
		self.notified = {'ensei':[], 'ndock':[], 'kdock':[]}
		self.path = __folder__+'/icons/%s.png'
		
		Notify.init(kconfig.theName)
	
	def notify(self, title, body, icon):
		
		n = Notify.Notification.new(title, body, (self.path % icon))
		n.show()
		
	def ensei(self, id, name, time):
		
		if((id,time) not in self.notified['ensei']):
			self.notify(u'艦隊帰投',u'第%d艦隊「%s」が遠征から帰投したお' % (id, name), 'ensei')
			self.notified['ensei'].append(tuple((id,time)))
			while len(self.notified['ensei']) > 3:
				self.notified['ensei'].pop(0)
	
	def ndock(self, id, name, time):
		
		if((id,time) not in self.notified['ndock']):
			self.notify(u'修復完了',u'%sの修復オワタお' % name, 'repair')
			self.notified['ndock'].append(tuple((id,time)))
			while len(self.notified['ndock']) > 4:
				self.notified['ndock'].pop(0)

	def kdock(self, id, name, time):
		
		if((id,time) not in self.notified['kdock']):
			self.notify(u'建造完了',u'%sが建造されたお' % name, 'constr')
			self.notified['kdock'].append(tuple((id,time)))
			while len(self.notified['kdock']) > 4:
				self.notified['kdock'].pop(0)