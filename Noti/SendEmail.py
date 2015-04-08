# -*- coding: utf-8 -*-
#! /bin/env python

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.header import Header
from email import Encoders

import smtplib
import datetime
import re
import signal
import sys
import traceback

class SendEmail(object):
	def __init__(self, confParser, dict_obj):
		self.setSignal()
		self.config = confParser
		self.raw_dict = dict_obj
		self.nok_list = list()
		self.limit_nok = 0
		self.connect_nok = 0
	
	def setSignal(self):
		self.SHUTDOWN = True
		signal.signal(signal.SIGTERM, self.shutdown) # sigNum 15 : Terminate
		signal.signal(signal.SIGINT, self.shutdown)  # sigNum  2 : Interrupt
		signal.signal(signal.SIGHUP, self.shutdown)  # sigNum  1 : HangUp
		signal.signal(signal.SIGPIPE, self.shutdown) # sigNum 13 : Broken Pipe

	def shutdown(self,sigNum, frame):
		self.SHUTDOWN = False
		sys.stderr.write("Catch Signal : %s" % sigNum)
		sys.stderr.flush()
	
	#파서정보를 받아옵니다. run()에서 실행됩니다.
	def getConfParser(self):
		try :
			config_emaillist = self.config.get('EMAIL','EMAILLIST').split(',')
			config_title = self.config.get('EMAIL','TITLE')
			config_user = self.config.get('EMAIL','SEND_USER')
			config_passwd = self.config.get('EMAIL','SEND_PASSWD')
			config_smtpip = self.config.get('EMAIL','SMTP_IP')
			config_smtpport = self.config.get('EMAIL','SMTP_PORT')
		except :
			print traceback.format_exc()

		return (config_emaillist, config_title, config_user, config_passwd, config_smtpip, config_smtpport)

	#메일을 보내는 로직입니다. run()에서 실행됩니다.	
	def send_gmail(self, to, title, html, user, passwd, smtp_ip, smtp_port, attach=None):
		msg = MIMEMultipart('alternative')
		msg['From']=user
		msg['To']=to
		msg['Subject']=Header(title,'utf-8')
		msg.attach(MIMEText(html, 'html', 'utf-8'))

		mailServer = smtplib.SMTP(smtp_ip,smtp_port)
		mailServer.ehlo()
		mailServer.starttls()
		mailServer.ehlo()
		mailServer.login(user,passwd)
		mailServer.sendmail(user, to, msg.as_string())
		mailServer.close()

	#IrisStatus에 보내질HTML 테이블을 만듭니다. getHTMLContent()에서 호출됩니다.
	def getIRISContent(self):
		try:
			mergelist=list()
			strNok=u"<h3 align='left'>이상상태 요약</h3>"
			mergelist.append("<html><head><meta charset='utf-8'><style type='text/css'>TR{height:20pt; font-family:Arial; font-size: 10pt; text-align:center;} TD{height:20pt; font-family:Arial; font-size:10pt; text-align:center;}</style></head><body>")
			mergelist.append("<h2 align='center'>IRIS</h2>")	
			mergelist.append("<center><table width='70%' cellpadding='5' cellspacing='0' border='1'>")
			mergelist.append("<tr bgcolor='#FFFF00'><td>ip</td><td>status</td><td>updatetime</td></tr>")
			for ip in self.raw_dict.keys():
				for key, value in self.raw_dict[ip].items():
					if value=='NOK':
						self.connect_nok = self.connect_nok+1 
						mergelist.append(str(ip)+":CONNECTION NOT OK")
						break
					if value=='OK':
						continue
					
					mergelist.append("<tr>")
					if value['STATUS']=='NOK':
						self.limit_nok = self.limit_nok+1
						strNok = strNok + "<h3 align='left'>["+str(ip)+"]"+key+" ["+value['VALUE'][0]+","+value['VALUE'][1]+"]</h3>"
						mergelist.append("<td><b><font color='red'>"+str(ip)+"</td>")
					else:	
						mergelist.append("<td>"+str(ip)+"</td>")

					for el in value['VALUE']: #['VAILD','20150323135938']
						if value['STATUS']=='NOK':
							mergelist.append("<td><b><font color='red'>"+el+"</font></b></td>")
						else:
							mergelist.append("<td>"+el+"</td>")
					mergelist.append("</tr>")
			mergelist.append("</table></center></body></html>")
			for index in range(len(mergelist)) : 
				if type(mergelist[index]) == unicode : 
					mergelist[index] = mergelist[index].encode('cp949')

			mergelist.insert(1,strNok)
			strResult = ''.join(mergelist)
			return strResult
		except:
			print traceback.format_exc()

	#ServerResource에 보내질 HTML 페이지를 만듭니다. run()에서 실행됩니다.
	def getHTMLContent(self):
		mergelist=list()
		strNok = ''
		mergelist.append("<html><head><meta charset='utf-8'><style type='text/css'>TR{height:20pt; font-family:Arial; font-size: 10pt; text-align:center;} TD{height:20pt; font-family:Arial; font-size:10pt; text-align:center;}P{text-indent:65%;}</style></head><body><h2 align='left'>이상정보 요약</h2>")
		for ip in self.raw_dict.keys():
			mergelist.append("<br><br>")
			mergelist.append("<h1 align='center'>"+ip+"</h1><HR>")
			#connection 부분에서의 ok, nok
			for key,value in self.raw_dict[ip].items():
				if value=='NOK':
					self.connect_nok = self.connect_nok+1
					mergelist.append("<h3 align='center'><b><font color='red'>CONNECTION NOT OK</b></font></h3>")
					strNok += "<h3 align='left'>["+str(ip)+"] CONNECTION NOK</h3>"
					break
				if value=='OK':
					#STATUS 정보는 string으로 만들 필요가 없으므로 pass가 아니라 continue
					continue
				mergelist.append("<h2 align='center'>"+key+"</h2>")
				mergelist.append("<center>(단위MB)<table width='70%' cellpadding='5' cellspacing='0' border='1'>")

				if key=='DISK':
					mergelist.append("<tr bgcolor='#FFFF00'><td>Mount On</td><td>1M-blocks</td><td>Used</td><td>Available</td><td>Use(%)</td></tr>")
					for elem in value: #elem = {'STATUS':'OK','VALUE':['/','12345','12345','12345','%']} * disk 갯수 
						mergelist.append("<tr>")
						if elem['STATUS']=='NOK':
							self.limit_nok = self.limit_nok+1
							strNok += "<h3 align='left'>["+str(ip)+"] "+ key + " ["+elem['VALUE'][0]+","+elem['VALUE'][4]+"]</h3>"
						
						for e in elem['VALUE']: #elem['VALUE'] = ['/','12345','12345','12345','%']
							e = self.commasplit(e)			
							if elem['STATUS']=='NOK':
								mergelist.append("<td><b><font color='red'>"+e+"</b></font></td>")
							else:
								mergelist.append("<td>"+e+"</td>")
						mergelist.append("</tr>")

				elif key=='IRIS':
					return self.getIRISContent()
					
				elif key=='LOAD_AVG':
					mergelist.append("<tr bgcolor='#FFFF00'><td>1 minutes</td><td>5 minutes</td><td>15 minutes</td>")
					mergelist.append("<tr>")
					if value['STATUS']=='NOK':
						self.limit_nok = self.limit_nok+1
						strNok += "<h3 align='left'>["+str(ip)+"]"+key+"  ["+value['VALUE'][0]+","+value['VALUE'][1]+","+value['VALUE'][2]+"]</h3>"

					for el in value['VALUE']: #value['VALUE'] = {'STATUS':'OK','VALUE':['0.1','0.2','0.3']}
						el = self.commasplit(el)
						if value['STATUS']=='NOK':
							mergelist.append("<td><b><font color='red'>"+el+"</td></b>")
						else:
							mergelist.append('<td>'+el+'</td>')
					mergelist.append("</tr>")
			
				else:
					mergelist.append("<tr bgcolor='#FFFF00'><td>Total</td><td>Used</td><td>Available</td><td>Use(%)</td></tr>")
					mergelist.append("<tr>")

					if value['STATUS']=='NOK':
						self.limit_nok = self.limit_nok+1
						strNok += "<h3 align='left'>["+str(ip)+"] "+key+" ["+value['VALUE'][3]+"]</h3>"

					for el in value['VALUE']:
						el = self.commasplit(el)
						if value['STATUS']=='NOK':
							mergelist.append("<td><b><font color='red'>"+el+"</td></b>")
						else:	
							mergelist.append('<td>'+el+'</td>')
					mergelist.append("</tr>")

				mergelist.append("</table></center>")
		mergelist.append("</body></html>")

		for index in range(len(mergelist)) : 
			if type(mergelist[index]) == unicode : 
				mergelist[index] = mergelist[index].encode('cp949')

		if type(strNok) == unicode :
			strNok = strNok.encode('cp949')

		mergelist.insert(1,strNok)
		strResult=''.join(mergelist)
		del(mergelist)
		return strResult

	def commasplit(self, number):
		try:
			if not re.match('\d[^\.\%]',number):
				return number
			tmp = number.split('.')
			num = tmp[0]
			decimal = '.' + tmp[1]
		except:
			num = number; 
			decimal = ''

		head_num = len(num) % 3
		result = ''
		for pos in range(len(num)):
			if pos == head_num and head_num:
				result = result + ','
			elif (pos - head_num) % 3 == 0 and pos:
				result = result + ','
			result = result + num[pos]
		return result + decimal
	
	#config Parser 정보를 불러와서 메일을 보냅니다. 
	def run(self):
		html = self.getHTMLContent()
		t = datetime.datetime.now()
		emails,title,user,passwd,smtpip,smtpport = self.getConfParser()
		title = "[CONN_NOK:"+str(self.connect_nok)+"][NOK:"+str(self.limit_nok)+"]"+title+"-"+str(t.strftime("%h %m %d - %H:%M:%S"))
		for email in emails:
			while not self.SHUTDOWN : 
				return
			email = email.strip()
			if email=='':
				continue
			self.send_gmail(email,title,html,user,passwd,smtpip,smtpport)
