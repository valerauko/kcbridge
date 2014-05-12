#!/usr/bin/env python
#coding=utf-8

import kconfig, kcdb
from gi.repository import Gtk as gtk, Gdk as gdk, GObject as gobj
from gi.repository import AppIndicator3 as appindicator
import re, threading
import sys, os.path

__folder__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)));
win = False

class kcNotebook(gtk.Notebook):
	
	def __init__(self):
		
		super(kcNotebook, self).__init__()
		self.show()
		
		self.show_tabs = True ## default to true
		self.set_tab_pos(gtk.PositionType.TOP) ## default to top
		
		self.pages = {}
	
	def append(self, id, obj, label):
		
		self.pages[id] = obj
		self.append_page(self.pages[id], label)
	
	def rename(self, id, new):
		
		self.pages[id].set_label_text(new)

class kcBar(gtk.Table):
	
	def __init__(self, p, label, override):
		
		self.w = 150
		
		super(kcBar, self).__init__(1, self.w, True)
		self.set_size_request(self.w,5)
		self.show()
		self.id = 'kcbar'+str(id(self))
		self.set_name(self.id)
		
		self.p = 0
		
		self.override = override
		
		self.update(p, label)
	
	def update(self, p, label):
		
		global win
		
		self.set_tooltip_text(label)
			
		if p == self.p:
			return bool(win)
		
		if 'bar' in dir(self):
			self.bar.destroy()
			del self.bar
		
		self.bar = gtk.Label()
		self.bar.show()
		
		if type(self.override) == list:
			if p < self.override[0]: ## red
				color = gdk.RGBA(0.8,0,0,1)
			elif p < self.override[1]: ## orange
				color = gdk.RGBA(1,0.5,0,1)
			elif p < self.override[2]: ## yellow
				color = gdk.RGBA(1,0.8,0,1)
			else: ## green
				color = gdk.RGBA(0,0.8,0,1)
		else:
			color = self.override
		
	##	print color.to_string()
		css = gtk.CssProvider()
		css.load_from_data('''
		@define-color barcolor %s;
		#%s GtkLabel {
			font:6px;
			background:-gtk-gradient (linear, center top, center bottom, from (shade (@barcolor, 1.05)), color-stop (0.5, @barcolor), to (shade (@barcolor, 0.95)));
			border-radius:3px;
		}
		''' % (color.to_string(), self.id) )
		self.bar.get_style_context().add_provider(css, gtk.STYLE_PROVIDER_PRIORITY_APPLICATION )
		
		self.p = p
		
		self.attach(self.bar, 0, int(self.w*p), 0, 1)
		
		return bool(win)

class kcFleetBote(gtk.Frame):
	
	def __init__(self, no, bote):
		
		super(kcFleetBote, self).__init__()
		no = (u'①' if no == 1 else str(no))
		self.label = kcLabel(u'<span font="18px">%s</span>')
		self.label.txt(no)
		self.set_label_widget(self.label)
		self.set_border_width(5)
		self.show()
		self.set_halign(gtk.Align.FILL)
		self.set_valign(gtk.Align.START)
		self.set_vexpand(True)
		
		grid = gtk.Grid()
		grid.set_border_width(5)
		grid.show()
		grid.set_halign(gtk.Align.FILL)
		grid.set_valign(gtk.Align.START)
		grid.set_vexpand(True)
		self.add(grid)
		
		self.bote = kcdb.db.bote[bote]
		if(not isinstance(self.bote, kcdb.kcBote)):
			return
		
		self.id = self.bote.id
		
		self.name = kcLabel(u'<span font="18px">%s</span> <span font="32px">%s</span>')
		self.name.txt(self.bote.type, self.bote.name)
		self.name.set_halign(gtk.Align.START)
		self.name.set_valign(gtk.Align.START)
		self.name.show()
		
		slots = gtk.Table(1,5,True)
		slots.set_halign(gtk.Align.START)
		slots.set_size_request(36,36)
		slots.show()
		
		self.items = {}
		
		i = 0
		while i < self.bote.base['slots']:
			self.items[i] = gtk.Image()
			self.items[i].set_size_request(36,36)
			self.items[i].show()
			slots.attach(self.items[i], i, i+1, 0, 1)
			i += 1
		
		bars = gtk.Box(orientation = gtk.Orientation.VERTICAL, spacing = 2)
		bars.show()
		bars.set_margin_left(5)
		bars.set_hexpand(True)
		bars.set_halign(gtk.Align.END)
		bars.set_valign(gtk.Align.START)
		
		## kcbar ( p , label , override )
		self.hpbar = kcBar(0, '', [0.25, 0.5, 0.75])
		self.fuelbar = kcBar(0, '', [0.35, 0.75, 0.95])
		self.ammobar = kcBar(0, '', [0.35, 0.75, 0.95])
		self.kirabar = kcBar(0, '', [0.2, 0.3, 0.5])
		self.xpbar = kcBar(0, '', gdk.RGBA(0.2,0.8,0.7,1))
		
		bars.pack_start(self.hpbar, True, False, 0)
		bars.pack_start(self.fuelbar, True, False, 0)
		bars.pack_start(self.ammobar, True, False, 0)
		bars.pack_start(self.kirabar, True, False, 0)
		bars.pack_start(self.xpbar, True, False, 0)
		
		grid.attach(self.name, 0, 0, 1, 1)
		grid.attach(slots, 0, 1, 1, 1)
		grid.attach(bars, 1, 0, 1, 2)
	
	def update(self):
		self.bote = kcdb.db.bote[self.id]
		if(not isinstance(self.bote, kcdb.kcBote)):
			return
		
		self.name.txt(self.bote.type, self.bote.name)
		
		i = 0
		while i < self.bote.base['slots']:
			s = self.bote.inst['slot'][i]
			if(s == -1):
				n = 0
			else:
				try:
					n = self.bote.equip[s].type[3]
				except KeyError: ## equip not loaded yet? weird but possible
					n = 0 ## fallback to empty until next update
			self.items[i].set_from_file(__folder__+'/equip/circled_'+str(n)+'.png')
			if(n):
				self.items[i].set_tooltip_text(self.bote.equip[s].base['name'])
			i += 1
		
		try:
			self.hpbar.update(self.bote.inst['nowhp'] / float(self.bote.inst['maxhp']), u'耐久: %d/%d' % (self.bote.inst['nowhp'], self.bote.inst['maxhp']))
			self.fuelbar.update(self.bote.inst['fuel'] / float(self.bote.base['fuel']), u'燃料: %d/%d' % (self.bote.inst['fuel'], self.bote.base['fuel']))
			self.ammobar.update(self.bote.inst['bull'] / float(self.bote.base['ammo']), u'弾薬: %d/%d' % (self.bote.inst['bull'], self.bote.base['ammo']))
			self.kirabar.update(self.bote.inst['cond'] / float(100), u'キラ: %d/%d' % (self.bote.inst['cond'], 100))
			x = (100*self.bote.inst['exp'][1]/(100-self.bote.inst['exp'][2]))
			self.xpbar.update(self.bote.inst['exp'][2]/float(100), u'Lv%d: %d/%d' % (self.bote.lv, x-self.bote.inst['exp'][1], x))
		except: ## this borks while loading (no idea why it's ran when the window doesn't exist
			pass
		
		global win
		return bool(win)

class kcFleet(gtk.Box):
	
	def __init__(self, fleet):
		
		super(kcFleet, self).__init__(orientation = gtk.Orientation.VERTICAL, spacing = 5)
		self.show()
		
		self.table = gtk.Table(3, 2, True)
		self.table.show()
		
		self.message = kcLabel(u'平均lv: %0.1f　制空力: %0.1f　%s速艦隊')
		
		self.pack_start(self.message, True, False, 0)
		self.pack_end(self.table, True, False, 0)
		
		self.fleet = fleet
		self.botes = {}
		
		self.update()
		gobj.timeout_add(1000, self.update)
		
	def update(self):
		i = 0
		while i < 6:
			## if there is a ship in the db
			if(len(kcdb.db.fleets[self.fleet]['botes']) > i):
				if(i in self.botes and self.botes[i].id != kcdb.db.fleets[self.fleet]['botes'][i].id):
					self.botes[i].destroy()
					del self.botes[i]
				
				if(not isinstance(kcdb.db.fleets[self.fleet]['botes'][i], kcdb.kcBote)):
				##	print kcdb.db.fleets[self.fleet]['botes'][i]
					i += 1
					continue
				
				if(i not in self.botes):
					self.botes[i] = kcFleetBote(i+1, kcdb.db.fleets[self.fleet]['botes'][i].id)
					self.table.attach(self.botes[i], (i%2), (i%2)+1, (i/2), (i/2)+1)
				
				self.botes[i].update()
				
			## if something that shouldn't be displayed is there, remove it
			elif(i in self.botes):
				self.botes[i].destroy()
			
			i += 1
		
		seiq = 0
		heik = 0
		i = 0
		kous = 1
		for kcb in self.botes.values():
			if(type(kcb) is not kcFleetBote):
				break
			
			b = kcb.bote
			seiq += b.seiq()
			kous *= int(b.base['highspd'])
			heik += b.lv
			i += 1
		
		if(i > 0):
			self.message.txt(heik/float(i), seiq, [u'低', u'高'][kous])
			self.message.show()
		
		global win
		return bool(win)

class kcPage(gtk.Grid):
	
	def __init__(self):
		
		super(kcPage, self).__init__()
		self.show()
		self.set_row_spacing(5)
		self.set_column_spacing(5)
		self.set_vexpand(True)
		self.set_hexpand(True)
		
		self.items = {}

class kcLabel(gtk.Label):
	
	def __init__(self, markup):
		
		super(kcLabel, self).__init__()
		self.set_use_markup(True)
		self.mup = markup
	
	def txt(self, *text):
		return self.set_markup(self.mup % text)
		

class kcBoteStore(gtk.ListStore):
	
	def __init__(self):
		##	  0			1	 2		3			4		5	  6		7		8		9		 10
		## watched | type | name | level | firepower | torp | aa | armor | asw | capacity | luck | 
		super(kcBoteStore, self).__init__(
			bool,		## watched		0
			str, int,	## type			1
			str, int,	## name			3
			str, int,	## level		5
			str, int,	## firepower	7
			str, int,	## torp			9
			str, int,	## aa			11
			str, int,	## armor		13
			str, int,	## asw			15
			str, int,	## capa			17
			str, int	## luck			19
			)
		
		self.storage = {}
		
		self.update()
		
	def update(self):
		
		for b in kcdb.db.bote.values():
			
			##print isinstance(b,kcdb.kcBote), (b.id not in self.storage)
			
			if(isinstance(b,kcdb.kcBote) and b.id not in self.storage):
				
				iter = self.append([
					False, ## 0
					
					b.type, ## 1
					b.base['type'], ## 2
					
					b.name, ## 3
					b.id, ## 4
					
					'%d (next: %d)'%(b.lv,b.inst['exp'][1]), ## 5
					int(b.lv), ## 6
					
					'%d (+%d)'%(b.base['fire']+b.inst['kyouka'][0], b.inst['karyoku'][1]-(b.base['fire']+b.inst['kyouka'][0])), ## 7
					int(b.base['fire']+b.inst['kyouka'][0]), ## 8
					
					'%d (+%d)'%(b.base['torp']+b.inst['kyouka'][1], b.inst['raisou'][1]-(b.base['torp']+b.inst['kyouka'][1])), ## 9
					int(b.base['torp']+b.inst['kyouka'][1]), ## 10
					
					'%d (+%d)'%(b.base['aa']+b.inst['kyouka'][2], b.inst['taiku'][1]-(b.base['aa']+b.inst['kyouka'][2])), ## 11
					int(b.base['aa']+b.inst['kyouka'][2]), ## 12
					
					'%d (+%d)'%(b.base['armor']+b.inst['kyouka'][3], b.inst['soukou'][1]-(b.base['armor']+b.inst['kyouka'][3])), ## 13
					int(b.base['armor']+b.inst['kyouka'][3]), ## 14
					
					str(b.inst['taisen'][0]), ## 15
					int(b.inst['taisen'][0]), ## 16
					
					str(b.base['capa']), ## 17
					int(b.base['capa']), ## 18
					
					'%d (+%d)'%(b.base['luck']+b.inst['kyouka'][4], b.inst['lucky'][1]-(b.base['luck']+b.inst['kyouka'][4])), ## 19
					int(b.base['luck']+b.inst['kyouka'][4]) ## 20
					])
				self.storage[b.id] = gtk.TreeRowReference.new(self, self.get_path(iter))

class kcBoteList(gtk.Box):
	
	def __init__(self):
		
		super(kcBoteList, self).__init__(orientation = gtk.Orientation.VERTICAL, spacing = 5)
		
		filterbox = gtk.Box(orientation = gtk.Orientation.VERTICAL, spacing = 5)
		filterbox.show()
		self.pack_start(filterbox, False, False, 0)
		
		scroll = gtk.ScrolledWindow()
		scroll.set_hexpand(True)
		scroll.set_vexpand(True)
		self.pack_start(scroll, True, True, 0)
		
		self.model = kcBoteStore()
		
		self.view = gtk.TreeView(model=self.model)
		
		##			0		  1		  2		  3		 4		  5		  6		  7		   8	    9	  10
		columns = [u'記録', u'種類', u'艦名', 'Lv', u'火力', u'雷装', u'対空', u'装甲', u'対潜', u'体裁', u'運']
		for i in range(11):
			if(i == 0):
				column = gtk.TreeViewColumn( columns[i], gtk.CellRendererToggle(), active = i)
				column.set_sort_column_id(i)
			else:
				column = gtk.TreeViewColumn( columns[i], gtk.CellRendererText(), text = (2*i)-1)
				column.set_sort_column_id(2*i)
			
			self.view.append_column(column)
		
		scroll.add(self.view)
	

class kcHead(gtk.Box):
	
	def __init__(self):
		
		super(kcHead, self).__init__(orientation = gtk.Orientation.HORIZONTAL)
		
		self.show()
		
		self.name = kcLabel(u'<span font="24px">%s</span>%s　司令部<span font="smallcaps 18px">lv%d</span>')
		self.name.set_halign(gtk.Align.START)
		self.comm = kcLabel(u'<span font="14px">%s</span>')
		self.comm.set_halign(gtk.Align.START)
		self.bucket = kcLabel(u'バケツ <span font="18px">%4s</span>')
		self.bucket.set_halign(gtk.Align.START)
		self.flamet = kcLabel(u'速建材 <span font="18px">%4s</span>')
		self.flamet.set_halign(gtk.Align.START)
		
		namebox = gtk.Box(orientation = gtk.Orientation.VERTICAL, spacing = 2)
		namebox.pack_start(self.name, True, False, 0)
		namebox.pack_start(self.comm, True, False, 0)
		self.pack_start(namebox, True, True, 0)
		namebox.set_halign(gtk.Align.START)
		namebox.show()
		
		matbox = gtk.Box(orientation = gtk.Orientation.VERTICAL, spacing = 2)
		matbox.pack_start(self.bucket, True, False, 0)
		matbox.pack_start(self.flamet, True, False, 0)
		self.pack_end(matbox, True, True, 0)
		matbox.set_halign(gtk.Align.END)
		matbox.show()
		
		self.update()
		
		gobj.timeout_add(1000,self.update)
	
	def update(self):
		
		if('name' in kcdb.db.teitoku):
			self.name.txt(kcdb.db.teitoku['name'], kcdb.db.ranks[kcdb.db.teitoku['rank']], kcdb.db.teitoku['level'])
			self.name.show()
			self.comm.txt(kcdb.db.teitoku['comment'])
			self.comm.show()
		
		if('materials' in kcdb.db.teitoku):
			self.bucket.txt(kcdb.db.teitoku['materials'][5])
			self.bucket.show()
			self.flamet.txt(kcdb.db.teitoku['materials'][4])
			self.flamet.show()

class kcFoot(gtk.Box):
	
	def __init__(self):
		
		super(kcFoot, self).__init__(orientation = gtk.Orientation.HORIZONTAL, spacing = 5)
		self.show()
		
		self.text = kcLabel('<span font="14px">艦娘: %d/%d　装備: %d/%d</span>')
		
		self.set_halign(gtk.Align.START)
		self.pack_start(self.text, False, False, 0)
		
		self.update()
		
		gobj.timeout_add(5000,self.update)
	
	def update(self):
		
		if('maxship' in kcdb.db.teitoku):
			self.text.txt(len(kcdb.db.bote.keys()), kcdb.db.teitoku['maxship'],
							len(kcdb.db.eqobj.keys()), kcdb.db.teitoku['maxitem'])
			self.text.show()
		
class kcNotebookHandle(kcLabel):
	
	def __init__(self, text):
		
		super(kcNotebookHandle, self).__init__('<span font="16px">%s</span>')
		self.set_use_markup(True)
		
		self.txt(text.center(20))
		
class kcWindow(gtk.Window):

	def __init__(self):
		
		super(kcWindow, self).__init__(title = kconfig.theName)
		
		self.set_default_size(300,200)
		self.set_icon_from_file(__folder__+'/frames/default0.png')
		self.set_position(1)
		self.set_border_width(5)
		self.set_vexpand(True)
		
		self.box = gtk.Box(orientation = gtk.Orientation.VERTICAL, spacing = 5)
		self.add(self.box)
		
		self.note = kcNotebook()
		self.note.append('fleets', self.fleets_page(), kcNotebookHandle(u'艦隊'))
		self.note.append('botes', self.botes_page(), kcNotebookHandle(u'艦娘'))
		self.note.append('quests', self.quest_page(), kcNotebookHandle(u'任務'))
		
		self.box.pack_start(kcHead(), False, False, 0)
		self.box.pack_start(self.note, False, True, 0)
		self.box.pack_start(kcFoot(), False, False, 0)
		
		
	def quest_page(self):
		
		grid = kcPage()
		
		return grid
		
	
	def botes_page(self):
		
		return kcBoteList()
		
	
	def fleets_page(self):
		
		grid = kcPage()
		
		fleets = kcNotebook()
		fleets.set_tab_pos(gtk.PositionType.LEFT)
		for n in kcdb.db.fleets.keys():
			fleets.append(n, kcFleet(n), kcNotebookHandle(kcdb.db.fleets[n]['name']))
		fleets.show()
		grid.attach(fleets, 0, 0, 2, 1)
		
		return grid
		
	
	def die(self, *args):
		
		global win
		win = False
		del self.note
		self.destroy()
		
def start(w):
	global win
	if win:
		win.present()
	else:
		win = kcWindow()
		win.connect("delete-event", win.die)
		win.show_all()
##gtk.main()





