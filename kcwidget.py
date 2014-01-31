#!/usr/bin/env python
#coding=utf-8

import kconfig, kcdb, kcnotify, kcwindow
from gi.repository import Gtk as gtk, GObject as gobj
from gi.repository import AppIndicator3 as appindicator
import os.path, re
import time

__folder__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)));

class kcItem(gtk.MenuItem):
	
	def __init__(self, name):
		
		super(kcItem, self).__init__(name)
		self.set_sensitive(False)
		self.show()
		
		self.id = 0
		self.type = ''
		self.title = name
		self.readymsg = ''
		
		self.done = 0
	
	def label(self, label):
		
		self.set_label(label)
		self.title = label
	
	def addcd(self, ts, type):
		
		self.type = type
		self.done = int(ts)
		gobj.timeout_add(1000,self.refresh)
	
	def delcd(self):
		
		self.set_label(self.title)
		self.type = ''
		self.done = False
	
	def refresh(self):
		
		if(not self.done):
			return False
		
		diff = self.done-time.time()
		
		if(diff > kconfig.theLimit):
			self.set_label(self.title+' '+self.format_time(diff))
		else:
			self.set_label(self.title+' '+self.readymsg)
			if(type(self.type) == str):
				getattr(notif,self.type)(self.id, self.title, self.done)
		
		return True
		
	
	def format_time(self, sec):
		m, s = divmod(sec, 60)
		h, m = divmod(m, 60)
		return (("%d:%02d:%02d" % (h, m, s)) if (h > 0) else ("%02d:%02d" % (m, s)))


class kcSubmenu(kcItem):
	
	def __init__(self, name, items = []):
		
		super(kcSubmenu, self).__init__(name)
		self.show()
		
		self.menu = gtk.Menu()
		self.menu.show()
		self.set_submenu(self.menu)
		
		self.items = []
		
		for i in items:
			if(type(i) in [kcItem, gtk.MenuItem]):
				self.append(i)
	
	def __call__(self, i):
		try:
			return self.items[i]
		except KeyError:
			return False
	
	def assign(self, labels):
		
		i = 0
		for l in labels:
			
			if len(self.items) < i+1:
				self.append(kcItem(l))
			else:
				self.items[i].label(l)
			
			i += 1
		
	def delete(self, i):
		
		try:
			self.items.pop(i).destroy()
			if(len(self.items) < 1):
				self.set_sensitive(False)
		except:
			pass
	
	def clear(self):
		
		for i in self.items:
			self.delete(i)
	
	def append(self, item):
		self.set_sensitive(True)
		self.items.append(item)
		self.menu.append(self.items[-1])


class kcSep(gtk.SeparatorMenuItem):
	
	def __init__(self):
		super(kcSep, self).__init__()
		self.show()

class kcWidget:
	## self.label.set_label(self.x)
	def __init__(self):
		
		self.icon = 0
		self.change = False
		self.alert = False
		self.icons =__folder__+'/frames/%s%d.png'
		
		self.ind = appindicator.Indicator.new(kconfig.theName, (self.icons % ('default',0)), appindicator.IndicatorCategory.OTHER)
		
		self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
		
		self.items = {}
		
		self.menu = gtk.Menu()
		self.ind.set_menu(self.menu)
				
		self.placeholder = u'データ待ちなう'
		
		self.init_menu()
		
		gobj.timeout_add(150, self.swap_icon)
	
	def quit(self, widget):
		print "got exit request from widget"
		##kcdb.listener.die() # can't kill subprocess because of >sudo
		gtk.main_quit()
	
	def append(self, name, item):
		
		self.items[name] = item
		self.menu.append(self.items[name])
		
	def swap_icon(self):
		
		if(self.icon > 6):
			self.icon = 0
		
		self.ind.set_icon((self.icons % (('active' if self.alert else 'default'), self.icon)))
		
		if(self.change):
			self.change = False
			self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
		
		else:
			self.change = True
			self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)
		
		self.icon += 1
		return True
	
	def init_menu(self):
		
		order= ['misc1','misc2','misc_sep',
				'fleet_head','fleet1','fleet2','fleet3','fleet4','fleet_sep',
				'ndock_head','ndock1','ndock2','ndock3','ndock4','ndock_sep',
				'kdock_head','kdock1','kdock2','kdock3','kdock4','kdock_sep',
				'window_item','quit_item']
		
		for i in order:
			if(i == 'fleet_head'):
				self.append('fleet_head',kcItem(u'艦隊'))
			elif(i == 'ndock_head'):
				self.append('ndock_head',kcItem(u'入渠ドック'))
			elif(i == 'kdock_head'):
				self.append('kdock_head',kcItem(u'建造ドック'))
			elif(re.search(r'fleet[1-4]',i)):
				self.append(i,kcSubmenu(self.placeholder))
			elif(re.search(r'sep$',i)):
				self.append(i,kcSep())
			else:
				self.append(i, kcItem(self.placeholder))
			
			if(i not in ['misc1','quit_item','window_item']):
				self.items[i].hide()
		
		self.items['window_item'].set_label(u'母港執務室')
		self.items['window_item'].set_sensitive(True)
		self.items['window_item'].connect('activate',kcwindow.start)
		
		self.items['quit_item'].set_label(u'あばよ')
		self.items['quit_item'].set_sensitive(True)
		self.items['quit_item'].connect('activate',self.quit)
	
	def fleet_menu(self, f):
				
		k = 'fleet'+str(f['id'])
		
		self.items['fleet_head'].show()
		self.items['fleet_sep'].show()
		self.items[k].show()
		
		if(self.items[k].title != f['name']):
			self.items[k].label(f['name'])
				
		if('botes' not in f or len(f['botes']) < 1):
		##	print f
			self.items[k].clear()
				
		else:
				
			while len(self.items[k].items) > len(f['botes']):
				self.items[k].delete(0)
			
			self.items[k].assign([unicode(s) for s in f['botes']])
			
		
		self.items[k].id = f['id']
		
		if(type(f['mission'][2]) == long):
			f['mission'][2] = int(f['mission'][2]/1000)
		
		if(f['mission'][0] == 1):
			self.items[k].addcd(f['mission'][2],'ensei')
			self.items[k].readymsg = u'艦隊帰投'
		else:
			if(f['mission'][0] == 2):
				notif.ensei(f['id'],f['name'],f['mission'][2])
			
			self.items[k].delcd()
	
	def dock_menu(self, nk, d):
		
		if nk not in ['n','k']:
			return False
		
		k = '%sdock%d' % (nk, d['id'])
		
		self.items[k[:-1]+'_head'].show()
		self.items[k[:-1]+'_sep'].show()
		
		self.items[k].id = d['id']
		self.items[k].show()
		
		if(d['state'] == -1):
			self.items[k].label(u'未開設')
		elif(d['state'] == 0):
			self.items[k].delcd()
			self.items[k].label(u'空渠')
		else:
			self.items[k].label(unicode(d['bote']) if nk == 'n' else
								u'%s %s' % (d['ship']['type']['name'], d['ship']['name']))
			self.items[k].addcd(d['time'],'%sdock' % nk)
			self.items[k].readymsg = u'%s完了' % (u'修復' if nk == 'n' else u'建造')
	
	
	def misc_menu(self, t):
		
		try:
			m1 = u'%s%s（lv%d）' % (t['name'], kcdb.db.ranks[t['rank']], t['level'])
		except:
			return False
			
		try:
			m2 = u'%s' % (t['comment'])
		except:
			return False
		
		if self.items['misc1'].title != m1:
			self.items['misc1'].label(m1)
			self.items['misc1'].show()
		
		if self.items['misc2'].title != m2:
			self.items['misc2'].label(m2)
			self.items['misc2'].show()
		
		self.items['misc_sep'].show()

	def main(self):
		
		if(not kcdb.loaded.is_set()):
			return True
			
		## stuff like admiral level, ship count, stuff 
		self.misc_menu(kcdb.db.teitoku)
		## the 4 fleets' data, captain obvious
		for k, f in kcdb.db.fleets.iteritems():
			self.fleet_menu(f)
		## the repair docks
		for k, d in kcdb.db.ndock.iteritems():
			self.dock_menu('n',d)
		## the construct docks
		for k, d in kcdb.db.kdock.iteritems():
			self.dock_menu('k',d)
		
		return True
		

notif = kcnotify.kcNotif()
widget = kcWidget()

