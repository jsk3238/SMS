# -*- coding: utf-8 -*-
#!/usr/bin python

import paramiko
import datetime
import sys
import signal
#import ConfigParser
import os
import time
#import subprocess
import traceback

FILEPATH = '/home/iris/IRIS/bin/Admin/NodeList'

IDX_NODEID = 0
IDX_SYS_STATUS = 1
IDX_ADM_STATUS = 2
IDX_UPDATE_TIME = 3
IDX_IP = 4
IDX_CPU = 5
IDX_LOADAVG = 6
IDX_MEMP = 7
IDX_MEMF = 8
IDX_DISK = 9

class IrisStatus() :
	def __init__(self, _Parser) :
		self.PARSER = _Parser
		self.GetConfig()

	def GetConfig(self) :
		try :
			self.IRIS_IP =  self.PARSER.get('IRIS','IRIS_IP')
			self.SSH_PORT = self.PARSER.get('IRIS','SSH_PORT')
			self.USER = self.PARSER.get('IRIS','USER')
			self.PASSWD = self.PARSER.get('IRIS','PASSWD')
			self.CMDPATH = self.PARSER.get('IRIS','CMDPATH')

		except : 
			print traceback.format_exc()
	def sshProc(self) :
		result = None
		try :
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh.connect(self.IRIS_IP, port = int(self.SSH_PORT), username = self.USER, password = self.PASSWD, timeout=5 )
			
			stdin, stdout, stderr = ssh.exec_command('bash -lc %s' % self.CMDPATH)
	
			result = stdout.readlines()
			if len(result) == 0 : result = stderr.readlines()
			ssh.close()
		except :
			#Connect Error?
			print traceback.format_exc()

		return result

	def run(self) :
		
		ResultDict = {}
		try :
			strResult = self.sshProc()

			if strResult == None :
				ResultDict[self.IRIS_IP] = {'STATUS' : 'NOK'}
				print 'Connect Fail'
			elif str(strResult).find('Failed') >= 0 :
				ResultDict[self.IRIS_IP] = {'STATUS' : 'NOK'}
				print strResult
			else :
				#0 - Header
				#1 , lastLine ===========
				for line in strResult[2:] :
					li = line.replace(' ','').replace('\n','').split(',')
					#Key(Type) : [Value, Desc]
					irisDict = {'STATUS' : 'OK' ,'VALUE' : [li[IDX_SYS_STATUS], li[IDX_UPDATE_TIME]]}
					dict = {'STATUS' : 'OK' , 'IRIS' : irisDict}
					ResultDict[li[IDX_IP]] = dict
		except :
			print traceback.format_exc()
		return ResultDict

def Main() :
	obj = IrisStatus(sys.argv[1], sys.argv[2], sys.argv[3])
	dict = obj.run()
	for NodeID in dict.keys() :
		for Key in dict[NodeID].keys() :
			print '%s %s = %s' % (NodeID, Key, dict[NodeID][Key])

if __name__ == '__main__' :
	Main()	
