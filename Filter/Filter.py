# -*- coding: utf-8 -*-
#!/usr/bin python

import datetime
import sys
import os
import Mobigen.Common.Log as Log
import time
import traceback

IDX_MAX = 0
IDX_MIN = 1

IDX_IRIS_SYS_STATUS = 0
IDX_IRIS_UPDATE_TIME = 1

IDX_MEMORY_TOTAL = 0
IDX_MEMORY_USED = 1
IDX_MEMORY_AVAILABE = 2
IDX_MEMORY_USE_PER = 3

IDX_DISK_MOUNT = 0
IDX_DISK_1MBLOCKS = 1
IDX_DISK_USED = 2
IDX_DISK_AVAILABLE = 3
IDX_DISK_USE_PER = 4

class Filter() :
	#임계치 Dict, 필터 Dict
	def __init__(self, _Parser, _ValueDict) :
		self.PARSER = _Parser
		self.ValueDict = _ValueDict
		self.GetConfig()

	def GetConfig(self) :
		try :
			self.Thresholddict = {}
			
			#default Threshold 
			self.Thresholddict['DEFAULT'] = {'LOAD_AVG':self.PARSER.get('RESOURCES', 'LOAD_AVG') ,
					 'MEMORY':self.PARSER.get('RESOURCES', 'MEMORY') ,
					 'DISK':self.PARSER.get('RESOURCES', 'DISK') ,
					 'SWAP':self.PARSER.get('RESOURCES', 'SWAP')}
			
			ServerList = self.PARSER.get('RESOURCES','SERVER_LIST').split(',')

			THRESHOLD_TYPE_LIST = ['LOAD_AVG','MEMORY','DISK','SWAP']
			for ServerIP in ServerList :
				for Type in THRESHOLD_TYPE_LIST :
					try :
						self.Thresholddict[ServerIP][Type] = self.PARSER.get(ServerIP,Type)			
					except :
						pass
		except :
			print traceback.format_exc()

	def GetTresholdValue(self, _Server, _Type) :
		try :
			if self.Thresholddict.has_key(_Server) :
				if self.Thresholddict[_Server].haskey(_Type) : return self.Thresholddict[_Server][_Type]
			
			return self.Thresholddict['DEFAULT'][_Type]
			
		except :
			print traceback.format_exc()
		
	def run(self) :
		try :
			for Server in self.ValueDict.keys() :

				#상태가 NOK-접속불가면 확인할 필요 없음
				if self.ValueDict[Server]['STATUS'] == 'NOK' :
					continue

				for Type in self.ValueDict[Server].keys() :
					if Type == 'IRIS' : #{'STATUS':'OK' , 'VALUE':[SYS_STATUS, UPDATE_TIME]}
						Value = self.ValueDict[Server][Type]['VALUE']
						if Value[IDX_IRIS_SYS_STATUS] != 'VALID' : self.ValueDict[Server][Type]['STATUS'] = 'NOK'
						#현재시간보다 1분이 느리다면 
						if datetime.datetime.strptime(Value[IDX_IRIS_UPDATE_TIME], '%Y%m%d%H%M%S') < datetime.datetime.now() - datetime.timedelta(minutes=1) : self.ValueDict[Server][Type]['STATUS'] = 'NOK'
						#if datetime.datetime.strptime(Value[IDX_IRIS_UPDATE_TIME], '%Y%m%d%H%M%S') < datetime.datetime.now() - datetime.timedelta(seconds=5) : self.ValueDict[Server][Type]['STATUS'] = 'NOK'

					elif Type == 'LOAD_AVG' : #{'STATUS':'OK' , 'VALUE':[1분,5분,1시간]}
						for Per in self.ValueDict[Server][Type]['VALUE'] :
							ThreshValue = self.GetTresholdValue(Server, Type)
							if float(Per) > float(ThreshValue) : 
								self.ValueDict[Server][Type]['STATUS'] = 'NOK'
								break
					elif Type == 'MEMORY' or Type == 'SWAP': #{'STATUS':'OK' , 'VALUE':[Total, Used, Available, Use%]}
						ThreshValue = self.GetTresholdValue(Server, Type)
						if int(self.ValueDict[Server][Type]['VALUE'][IDX_MEMORY_USE_PER]) > int(ThreshValue) :
							self.ValueDict[Server][Type]['STATUS'] = 'NOK'
					
					elif Type == 'DISK' : #[{'STATUS':'OK', VALUE[Mount, 1M-blocks, Used, Available, Use%]}]
						ThreshValue = self.GetTresholdValue(Server, Type)
						for Disk in self.ValueDict[Server][Type] :
							if int(Disk['VALUE'][IDX_DISK_USE_PER]) > int(ThreshValue) :
								Disk['STATUS'] = 'NOK'
						
		except :
			print traceback.format_exc()

		return self.ValueDict

def Main() :
	obj = SMSFilter()
	dict = obj.run()
	for ServerID in dict.keys() :
		for Key in dict[ServerID].keys() :
			print '%s %s = %s' % (ServerID, Key, dict[ServerID][Key])

if __name__ == '__main__' :
	Main()	
