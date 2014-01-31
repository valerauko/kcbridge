#!/usr/bin/env python
#coding=utf-8

import kconfig
import re, json, urlparse, math, time
import os.path, threading, Queue
import subprocess as sub
import sqlite3 as lite

__folder__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)));
loaded = threading.Event()

sniffer = Queue.Queue()

class kcBote:
	
	def __init__(self, data, ship, type):
		
		self.base = ship
		self.inst = data
		self.clss = type
		
		self.id = data['id']
		self.lv = data['lv']
		self.name = ship['name']
		self.type = type['name']
		
		##print self.name.encode('utf-8'), [self.inst['onslot']]
		
		self.equip = db.eqobj
	
	def seiq(self):
		
		seiq = 0
		i = 0
		while i < self.inst['slotnum']:
			s = self.inst['slot'][i]
			
			if(s == -1):
				break
			
			if(self.equip[s].type[3] in range(6, 10)):
			##	print [self.equip[s].aa]
				seiq += self.equip[s].aa * math.sqrt(self.inst['onslot'][i])
			
			i+=1
			
		return seiq
	
	def __repr__(self):
		
		return str(self)
	
	def merge(self, ta):
		
		self = ta
	
	def __eq__(self, ta):
		if(not isinstance(ta,kcBote)):
			return NotImplemented
		elif(ta.inst == self.inst):
			return True
		else:
			return False
	
	def __str__(self):
		
		return 'bote #%d' % self.id
		
	
	def __unicode__(self):
		
		return u'%s　%s（lv%d）' % (self.type, self.name, self.lv)


class kcEquip:
	
	def __init__(self, inst, base):
		
		self.inst = inst
		self.base = base
		self.type = json.loads(base['type'])
		self.aa = int(base['aa'])


class kcDb:

	def __init__(self):
		
		self.ship = {} ## used to store ship base data
		self.ship_type = {} ## used to store ship classes (dd bb etc)
		self.equip = {} ## used to store equip base data
		self.item = {} ## used to store user items (bucket etc)
		
		self.eqobj = {} ## used to store individual equipment pieces
		self.bote = {} ## used to store individual bote stats
		self.fleets = {} ## used to store the fleets
		
		self.ndock = {} ## repair docks
		self.kdock = {} ## repair docks
		
		self.ranks = [-1, u'元帥', u'大将', u'中将', u'少将', u'大佐', u'中佐', u'少佐', u'新米少佐'] ## gonna hardcode this
		self.teitoku = {} ## self-explanatory
		
		self.in_sortie = False
		self.current_sortie = {}
		
		self.con = lite.connect(__folder__+'/kcontrol.db')
		
		with self.con:
			self.con.row_factory = lite.Row
			
			self.cur = self.con.cursor()
			
			self.init_tables()
			
			self.main()
			
			
	def init_tables(self):
		
		t = [
		##	self.cur.execute('create table if not exists deck(id int primary key unique not null, name text not null, ships text, exped_id int, exped_end int)'),
			self.cur.execute('create table if not exists ship( id int primary key unique not null, sort int not null, cls int not null, type int not null, name text not null, yomi text not null, maxeq text not null, slots int not null, capa text not null, ammo int not null, fuel int not null, speed int not null, highspd int not null, range int not null, fire int not null, torp int not null, aa int not null, asw int not null, hp int not null, armor int not null, saku int not null, evasion int not null, luck int not null, aftership int, afterlv int, afterfuel int, afterammo int)'),
			self.cur.execute('create table if not exists ship_type( id int primary key unique not null, name text not null)'),
			self.cur.execute('create table if not exists equip( id int primary key unique not null, name text not null, type text not null, aa text not null)'),
			self.cur.execute('create table if not exists mequip( id int primary key unique not null, slotitem int not null)'),
			self.cur.execute('create table if not exists nodestat( world int not null, map int not null, node int not null, comp text not null, form int not null, result text not null, cont int not null, ship_drop int, time real not null)'),
			self.cur.execute('create table if not exists constrstat( fuel int not null, ammo int not null, steel int not null, baux int not null, devmat int not null, ship int not null, time real unique not null)')
		]
		try:
			
			self.cur.execute('select * from ship')
			rows = self.cur.fetchall()
			for row in rows:
				row = dict(row)
				self.ship[row.pop('id')] = row
				
			self.cur.execute('select * from ship_type')
			rows = self.cur.fetchall()
			for row in rows:
				row = dict(row)
				self.ship_type[row.pop('id')] = row
			
			self.cur.execute('select * from equip')
			rows = self.cur.fetchall()
			for row in rows:
				row = dict(row)
				self.equip[row.pop('id')] = row
				
			self.cur.execute('select * from mequip')
			rows = self.cur.fetchall()
			for row in rows:
				row = dict(row)
				self.eqobj[row['id']] = kcEquip({'slotitem_id':row['slotitem']},self.equip[row['slotitem']])
		
		except:
			print "init error"
	
	def sync(self, table, data, detail = None):
		
		##			these tables only occur during sorties
		if(table in ['map.start','map.next','sortie.battle','battle_midnight.battle','sortie.battleresult', 'battle_midnight.sp_midnight']):
			
			self.handle_sortie(table, data, detail)
		
		##					these tables can occur during sortie if you get a drop so gotta exclude
		elif(self.in_sortie and (table not in ['member.ship2','member.slotitem','member.deck'])):
			self.commit_sortie()
			self.in_sortie = False
		
		## load ship type database
		if(table == 'master.ship'):
			self.cur.executemany('replace into ship values(:id, :sortno, :ctype, :stype, :name, :yomi, :maxeq, :slot_num, :tous, :bull_max, :fuel_max, :soku, :sokuh, :leng, :houg, :raig, :tyku, :tais, :taik, :souk, :saku, :kaih, :luck, :aftershipid, :afterlv, :afterbull, :afterfuel)',
				map(lambda y: dict(map(lambda (k, v): (k,v[0]) if (type(v) is list and len(v) == 2) else (k,unicode(v)), y.iteritems())), data) )
				## v[0] for the base values. v[1] would be the max, but that's included with the individual ships -- and we need a base to calculate from to find out if a ship can be upgraded (since equip bonuses are included in the stats)
			self.con.commit()
			
			self.cur.execute('select * from ship')
			rows = self.cur.fetchall()
			for row in rows:
				row = dict(row)
				self.ship[row.pop('id')] = row
			
		## load ship class (dd bb ca etc) database
		elif(table == 'master.stype'):
			self.cur.executemany('replace into ship_type values(:id,:name)',data)
			self.con.commit()
			
			self.cur.execute('select * from ship_type')
			rows = self.cur.fetchall()
			for row in rows:
				row = dict(row)
				self.ship_type[row.pop('id')] = row
			
		## load item database (if for a change it's not fucked in the packet phase)
		elif(table == 'master.slotitem'):
			self.cur.executemany('replace into equip values(:id, :name, :type, :tyku)',
				map(lambda y: {k:unicode(v) for k, v in y.iteritems()},data))
			self.con.commit()
			
			self.cur.execute('select * from equip')
			rows = self.cur.fetchall()
			
			for row in rows:
				row = dict(row)
				self.equip[row.pop('id')] = row
		
		## the data in ship3 ship2 ship are all the same. ship3 has deck data too.
		elif(table == 'member.ship3'):
			self.sync('member.ship2',data.pop('ship_data'))
			self.sync('member.deck',data.pop('deck_data'))
		
		elif(table in ['member.ship', 'member.ship2']):
			
			ids = []
			for b in data:
				if('ship_id' not in b):
				##	print b
					continue
				
				self.bote[b['id']] = kcBote(b, self.ship[b['ship_id']], self.ship_type[self.ship[b['ship_id']]['type']])
				ids.append(b['id'])
				
			for k,b in self.bote.items():
				if(isinstance(b,kcBote) and b.id not in ids):
					del self.bote[k]
		
		## slot items are rare to catch in their entirety so cache cache cache
		elif(table == 'member.slotitem'):
			
			self.cur.executemany('replace into mequip values(:id, :slotitem_id)',data)
			self.con.commit()
			for i in data:
				self.eqobj[i['id']] = kcEquip(i, self.equip[i['slotitem_id']])
			
			ids = [int(d['id']) for d in data] ## take all the ids currently present
			
			## then delete all the equipment that's not around anymore
			dels = []
			for e in self.eqobj.keys():
				if(int(e) not in ids):
					dels.append( [e] )
					del self.eqobj[e]
			
			if(len(dels) > 0):
				self.cur.executemany('delete from mequip where id=?', dels)
				self.con.commit()
		
		## the 4 fleets
		elif(table in ['member.deck_port', 'member.deck']):
			
			for f in data:
				
				f = {k: v for k,v in f.iteritems() if (k in ['id','name','mission','ship'])}
				try:
					f['botes'] = [self.bote[i] for i in f.pop('ship') if i != -1]
				except:
					pass
				
				if((f['id'] not in self.fleets) or ((f != self.fleets[f['id']]) and (len(f) >= len(self.fleets[f['id']])))):
					
					self.fleets[f['id']] = f
		
		## construct docks
		elif(table == 'member.kdock'):
			
			for d in data:
				if(d['complete_time'] > 0):
					self.cur.execute('insert or ignore into constrstat values(:item1, :item2, :item3, :item4, :item5, :created_ship_id, :complete_time)',d)
					self.con.commit()
				
				d = dict([	('id',int(d['id'])),
							('state',int(d['state'])),
							('time',(int(d['complete_time']/1000) if d['complete_time'] > 0 else False)),
							('ship',dict( map( lambda (k,v): (k,self.ship_type[v]) if k == 'type' else (k,v), self.ship[d['created_ship_id']].iteritems() ) ) if d['created_ship_id'] > 0 else False) ])
				
				if(d['id'] not in self.kdock or self.kdock[d['id']] != d):
					self.kdock[d['id']] = d
		
		## repair docks
		elif(table == 'member.ndock'):
			
			for d in data:
				try:
					d = dict([('id',int(d['id'])),
						(('time',int(d['complete_time']/1000)) if d['complete_time'] > 0 else ('time',False)),
						(('bote',self.bote[d['ship_id']]) if d['ship_id'] > 0 else ('bote',False)),
						('state',d['state'])])
				except KeyError, no: ## ship isn't loaded yet, derp. don't want partial data, break here.
				##	print "missing ship %s" % no
					break
				
				if(d['id'] not in self.ndock or self.ndock[d['id']] != d):
					self.ndock[d['id']] = d
		
		## user data
		elif(table == 'member.basic'):
			
			t = dict([('name',data[u'nickname']),('rank',data[u'rank']),('comment',data[u'comment']),('level',data[u'level']),
						('maxship',data[u'max_chara']),('maxitem',data[u'max_slotitem']),('fcoin',data[u'fcoin'])])
			self.teitoku = dict(self.teitoku, **t)
		
		## materials
		elif(table == 'member.material'):
			self.teitoku = dict(self.teitoku, **{'materials':[m[u'value'] for m in data]})
			
			'''
			elif(table == 'member.useitem'):
				print (table, data)
			elif(table == 'member.logincheck'):
				##print 'material +3/+1'
				pass
			elif(re.search(r'quest',table)):
				##print data
				pass
			'''
		
		## mark data ready to fetch if we have everything necessary for the appindicator
		if(	(len(self.ship) > 0) and
			(len(self.ship_type) > 0) and
			(len(self.equip) > 0) and
			(len(self.bote) > 0) and
			(len(self.eqobj) > 0) and
			(not loaded.is_set())):
			
			loaded.set()
			
		return False
	
	def handle_sortie(self, table, data, detail = None):
		
		if(table == 'map.start'): ## sorties start here
			self.in_sortie = True
			self.current_sortie = {
					'world': data['maparea_id'],
					'map':data['mapinfo_no'],
					'fleet': int(detail['deck_id']),
					'nodes':[]
				}
		
		if(self.in_sortie and table in ['map.start','map.next']):
			self.current_sortie['nodes'].append({'node':int(data['no'])})
		
		elif(self.in_sortie and table in ['sortie.battle', 'battle_midnight.sp_midnight']): ## these are the only two options for first battle phase
			self.current_sortie['nodes'][-1]['general'] = {
					'composition':data['ship_ke'][1:], ## don't need the -1
					'enemy_equip':data['eSlot'], ## gotta compare this to data from the db, not sure if needed
					'enemy_stats':data['eParam'], ## and this too
					'friend_stats':data['fParam'], ## and this too
					'enemy_form':data['formation'][1], ## formation is [friend, enemy, encounter]
					'friend_form':data['formation'][0], ## formations: 1 line ahead, 2 double line, 3 diamond, 4 echelon, 5 line abreast
					'encounter':data['formation'][2], ## encounter types: 1 doukousen, 2 hankousen, 3 t adv, 4 t disadv
					'maxhps':data['maxhps'][1:],
					'nowhps':data['nowhps'][1:],
					'search':(data['search'] if 'search' in data.keys() else 0)
				}
				
			self.current_sortie['nodes'][-1]['rounds'] = {k:v for k,v in data.items()
				if k[:7] in ['hougeki','raigeki','opening','support'] 
				or k == 'kouku'}
		
		elif(self.in_sortie and table == 'battle_midnight.battle'):
			self.current_sortie['nodes'][-1]['night'] = {k:v for k,v in data.items()
				if k in ['hougeki','maxhps','nowhps']}
		
		elif(self.in_sortie and table == 'sortie.battleresult'):
			self.current_sortie['nodes'][-1]['result'] = {k:v for k,v in data.items()
				if k[:4] in ['win_','get_','mvp']}
		
	def commit_sortie(self):
		if(not self.in_sortie or not self.current_sortie):
			return False
		
		temp = []
		while len( self.current_sortie['nodes'] ):
			n = self.current_sortie['nodes'].pop(0)
			if(len(n) > 1):
				try:
					## nodestat( world int not null, map int not null, node int not null, comp text not null, form int not null, result text not null, cont int not null, ship_drop int not null, time real not null)
					temp.append({
						'world':self.current_sortie['world'],
						'map':self.current_sortie['map'],
						'node': n['node'],
						'comp': json.dumps(n['general']['composition']),
						'form': n['general']['enemy_form'],
						'result': n['result']['win_rank'],
						'cont': int(len(self.current_sortie['nodes']) > 0),
						'ship_drop': (n['result']['get_ship']['ship_id'] if ('get_ship' in n['result'] and 'ship_id' in n['result']['get_ship']) else None),
						'time':time.time()
						})
				except:
					print "battle results incomplete, skipped"
		
		if(len(temp) > 0):
			self.cur.executemany('insert into nodestat values(:world,:map,:node,:comp,:form,:result,:cont,:ship_drop,:time)',temp)
			self.con.commit()
		
	def handle_request(self, data):
		
		try:
			table, data = tuple(data)
		except:
			return
		
		detail = None
		if(type(table) is tuple):
			table, detail = table
		
		table = re.sub(r'api_[^_]+_(.+)$', r'\1', table)
		data = re.sub(r'\n*','',data)
		data = re.sub(r'api_','',data)
		
		try:
			data = json.loads(data)['data']
		except KeyError:
			return
		except Exception, msg:
		##	print 'Packet for %s borked'%table, str((msg))
			return
		
		try:
			self.sync(table, data, detail)
		except Exception, msg:
			print "Couldn't handle %s"%table, str((msg))
			return
	
	def main(self):
		
		while sniffer.qsize() > 0:
			self.handle_request(sniffer.get())
			sniffer.task_done()
		
		return True
		

class kcListener:
	
	def __init__(self):
		
		self.pop = sub.Popen(('sudo', __folder__+'/kcsniffer.py'),stdout=sub.PIPE)
		self.cap = self.pop.stdout
	
	def main(self):
		
		with self.cap:
			captured = []
			
			for data in self.cap:
				
				get = re.search(r'GET \/kcs\/', data)
				if(get):
					if(captured):
						sniffer.put(captured)
						captured = []
					continue
					
				post = re.search(r'POST \/kcsapi\/(.+) HTTP', data)
				if(post):
					request = re.search(r'(api%5F.+)$', data)
					if(request):
						request = {k.replace('api_',''):(v[0] if len(v) < 2 else v) for k,v in urlparse.parse_qs(request.group(1)).items() if k not in ['api_verno', 'api_token']}
					
					if(captured):
						sniffer.put(captured)
						captured = []
					
					captured.append((re.sub(r'\/','.',post.group(1)), request))
				
				elif len(captured) > 0:
					
					sv = re.search(r"svdata\=(\{.+)", data)
					
					if(sv):
						captured.append(sv.group(1))
					
					elif((not re.search(r'200 OK', data)) and len(captured) > 1):
						captured[1] += data

listener = kcListener()
db = kcDb()





