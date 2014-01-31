#!/usr/bin/env python

import kconfig
import socket, sys, re
from struct import *

class kcSniffer:
	
	def __init__(self):
		
		try:
			self.s = socket.socket( socket.AF_PACKET , socket.SOCK_RAW , socket.ntohs(0x0003))
		except socket.error , msg:
			print str(msg[0]) + ': ' + msg[1]
			sys.exit()
		
		self.main()
	
	def main(self):

		while True:
			packet = self.s.recvfrom(65565)
			
			## only need the packet string
			packet = packet[0]
			
			i = 0
			j = False
			while i < len(packet):
				##if(packet[i:i+6] == 'image/'):
				if(packet[i:i+4] == socket.inet_aton(kconfig.theServer)):
				##	print [i, packet]
					j = True
					break
				else:
					i += 1
			
			if not j:
				continue
			
			## take first 20 characters for the ip header
			ip_header = packet[:20]
			 
			iph = unpack('!BBHHHBBH4s4s' , ip_header)
			iph_length = (iph[0] & 0xF) * 4
			protocol = iph[6]
			
			## only need tcp
			if(protocol != 6):
				continue
			
			s_addr = socket.inet_ntoa(iph[8]);
			d_addr = socket.inet_ntoa(iph[9]);
			
			tcp_header = packet[iph_length:iph_length+20]
			
			tcph = unpack('!HHLLBBHHH' , tcp_header)
			doff_reserved = tcph[4]
			tcph_length = doff_reserved >> 4
			
			h_size = iph_length + tcph_length * 4
				 
			data = packet[h_size:].strip().translate(None,"\r\n")
			
			if(data[-2:] == "}0"):
				data = data[:-1]
			
			if(len(data) > 0):
				print data

		
kcSniffer()