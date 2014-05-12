#!/usr/bin/env python

import kconfig
import socket, sys, Queue, threading, time
from struct import *

class kcSniffer:
	
	def __init__(self):
		
		try:
			self.s = socket.socket( socket.AF_PACKET , socket.SOCK_RAW , socket.ntohs(0x0003))
		except socket.error , msg:
			print str(msg[0]) + ': ' + msg[1]
			sys.exit()
			return 1
		
		## init queue
		self.q = Queue.Queue()
		
		## start listener thread
		lst = threading.Thread(target = self.listen, name = 'kcSniff')
		lst.daemon = True
		lst.start()
		
		## start processor (main thread)
		self.process()
	
	def check(self, x):
		return True
		
		t = -1
		for k in sorted(x.keys()):
			
			if((t < 0) or (t == k-1)):
				t = k
			else:
			##	print "Missing: %d" % (t+1)
				return False
		return True
	
	def listen(self):
		
		while True:
			packet = self.s.recvfrom(65565) ## this hangs until there's something
			
			## only need the packet string
			self.q.put(packet[0])

	
	def process(self):

		streams = {}
		
		while True:
			
			packet = self.q.get() ## this hangs too
			
			ethh = 14
			packet = packet[ethh:]
			
			## take first 20 characters for the ip header
			ip_header = packet[:20]
			
			iph = unpack('!BBHHHBBH4s4s' , ip_header)
								
		##	print kconfig.theServer, socket.inet_ntoa(iph[8]), socket.inet_ntoa(iph[9])
			
			if(socket.inet_aton(kconfig.theServer) not in [iph[8], iph[9]]):
				self.q.task_done()
				continue
			
			iph_length = (iph[0] & 0xF) * 4
			protocol = iph[6]
			
			## only need tcp
			if(protocol != 6):
				self.q.task_done()
				continue
			
			tcp_header = packet[iph_length:iph_length+20]
			
			tcph = unpack('!HHLLBBHHH' , tcp_header)
			doff_reserved = tcph[4]
			tcph_length = doff_reserved >> 4
			
			h_size = iph_length + tcph_length * 4
				 
			data = packet[h_size:].strip().translate(None,"\r\n") ## strip all newlines
			
			## first add the current packet to the heap
			if(len(data) > 0):
				
				if(tcph[3] not in streams):
					if(len(streams) > 0):
						self.handle(streams.pop(streams.keys()[0]))
						
					streams[tcph[3]] = {}
				
				## second element is the packet's PUSH flag
				streams[tcph[3]][iph[3]] = [data,tcph[5]&0x8]
			
			##	## debug current packet
			##	print (len(streams), tcph[3], iph[3], tcph[6], (len(streams[tcph[3]]) if tcph[3] in streams else 0),
			##		''.join(map(lambda (n,m): (m if tcph[5]&pow(2,n) else '-'), enumerate(reversed(['C', 'E', 'U', 'A', 'P', 'R', 'S', 'F'])))))
			
			self.q.task_done()
			
	def handle(self, resp):
		## need at least one P or F, continuous ids
		if(self.check(resp)):
			
			## if the last packet (sorted, remember) doesn't have the P flag set when another stream begins,
			## that means it's broken, so we don't want it
			keys = sorted(resp.keys())
			if(resp[keys[-1]][1]):
				
				dmp = ''.join([resp[k][0].strip() for k in keys])
				
				## for some reason sometimes there's a 0 after the end of the json string, breaking everything
				if(dmp[-2:] == "}0"):
					dmp = dmp[:-1]
				
				print dmp ##[:70]
				##print (sys.getsizeof(dmp))
				##print "--------\n"
			
try:
	kcSniffer()
except:
	pass
	
	
	
	