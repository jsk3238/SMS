# -*- coding: utf-8 -*-
#!/usr/bin python

import datetime
import sys
import signal
import ConfigParser
import os
import time
from Collect.IrisStatus import *
from Collect.ServerResource import *
from Filter.Filter import *
from Noti.SMSSend import *
from Noti.SendEmail import *
from Noti.SendStringEmail import *
import traceback

class ServerManagementService() :
	def __init__(self) :
		self.usege()
		self.GetParser()
		self.SetSignal()

	def GetParser(self) :
		try :
			self.PARSER = ConfigParser()
			self.PARSER.read(sys.argv[4])	
		except :
			print traceback.format_exc()
			sys.exit()

	def usege(self) :
		if len(sys.argv) != 5 :
			print 'usage : Collect Filter Noti ConfigFile' % ( sys.argv[0] )
			sys.exit()
	
	def SetSignal(self) :
		self.SHUTDOWN = True
		signal.signal(signal.SIGTERM, self.Shutdown)
		signal.signal(signal.SIGINT, self.Shutdown)
		signal.signal(signal.SIGHUP, self.Shutdown)
		signal.signal(signal.SIGPIPE, self.Shutdown)
	
	def Shutdown(self, sigNum=0, frame=0):
		self.SHUTDOWN = False

	def run(self) :
		try :
			ColInst = eval(sys.argv[1])
			FilInst = eval(sys.argv[2])
			NotiInst = eval(sys.argv[3])
		
			#Collect
			Colobj = ColInst(self.PARSER)
			dict = Colobj.run()
			
			#Filter
			Filobj = FilInst(self.PARSER, dict)
			dict = Filobj.run()

			#Noti
			Notiobj = NotiInst(self.PARSER, dict)
			Notiobj.run()

		except :
			print traceback.format_exc()

def Main() :
	obj = ServerManagementService()
	obj.run()

if __name__ == '__main__' :
	Main()	
