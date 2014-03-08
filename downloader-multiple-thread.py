import urllib2
import logging
import sys
import getopt
import os
import Queue
import threading
from urlparse import urlparse
from ftplib import FTP
from xml.dom.minidom import parseString
import httplib

# def write(filename,data,offset):
# 	try:
# 		output_file = open(filename,"r+b")
# 	except IOError:	
# 		output_file = open(filename,"w+")
# 	output_file.seek(offset)
# 	output_file.write(data)
# 	output_file.close()

# filename = 'tempfile'
# write(filename,'1' * (1024*32),1024*1024)
# write(filename,'0' * (1024*32),0)
# print os.path.getsize(filename)
# exit(1)

queue = Queue.Queue()

class ThreadUrl(threading.Thread):
	"""Threaded Url Grab"""
	def __init__(self, queue):
	  threading.Thread.__init__(self)
	  self.queue = queue

	def run(self):
	  while True:
	  	#retriving from Downloader object
	    base = self.queue.get()
	    msg = 'thread start for url ' + base.url
	    logger.info(msg)
	    print msg
	    base.download(download_folder)
	    msg = 'thread end for url ' + base.url
	    logger.info(msg)
	    print msg
	    self.queue.task_done()

class FetchUrl(threading.Thread):
	"""Threaded Url Grab"""
	def __init__(self, lock, url, filename, download_folder, logger, start_range, end_range):
	  threading.Thread.__init__(self)
	  self.lock = lock
	  self.url = url
	  self.url_parsed = urlparse(url)
	  self.filename = filename
	  self.download_folder = download_folder
	  self.logger = logger
	  self.start_range = start_range
	  self.end_range = end_range

	def run(self):
		print "start download %s %s" % (self.start_range, self.end_range)
		downloader = HttpDownload()
		data = downloader.partial_download(self.url, self.url_parsed, self.logger, self.start_range, self.end_range)
		download_file_name = self.download_folder + '/' + self.filename
		self.lock.acquire()	
		try:
			output_file = open(download_file_name,"r+b")
		except IOError:	
			output_file = open(download_file_name,"w+")
		print "file writeing"	
		output_file.seek(self.start_range)
		output_file.write(data)
		output_file.close()
		self.lock.release()

class HttpDownload():
	def download(self, url, url_parsed, filename, download_folder, logger, download_file_name = ''):
		if download_file_name == '':
			download_file = download_folder + '/' + filename + '.rss'
		else: 
			download_file = download_folder + '/' + download_file_name
		#sending a request to url 
		try:
			response = urllib2.urlopen(url)
		except urllib2.URLError as e:
			msg = 'url is not correct http://debian.org/debian/README'
			logger.info(msg)
			logger.info(e.reason)
			print msg
			return None
		else:
			#setting remote file size
			remote_file_size = response.info()['Content-Length']

		req = urllib2.Request(url)

		#checkeing file already downloaded or not
		if os.path.isfile(download_file):
			local_file_size = os.path.getsize(download_file)
			if int(remote_file_size) ==	int(local_file_size):
				msg = 'file already downloaded'
				logger.info(msg)
				print msg
				return None
			else:
				#file partially downloaded adding Range header 
				output_file = open(download_file,"a")				
				req.headers['Range'] = 'bytes=%s-%s' % (local_file_size, remote_file_size)		
		else:
			output_file = open(download_file,"w")

		#file partially downloaded so requesting again with Range header
		if 'Range' in req.headers:
			try:
				response = urllib2.urlopen(req)
			except urllib2.URLError as e:
				msg = 'url is not correct http://debian.org/debian/README'
				logger.info(msg)
				logger.info(e.reason)
				print msg
				return None

		while True:
			data = response.read(8192)
			if not data:
				break
			output_file.write(data)
		output_file.close()

		if download_file_name == '':
			msg = 'rss file downloaded at ' + download_file
		else:
			msg = 'file downloaded at ' + download_file	
		print msg
		logger.info(msg)
	
	def partial_download(self, url, url_parsed, logger, start_range = 0, end_range = 0):
		req = urllib2.Request(url)
		req.headers['Range'] = 'bytes=%s-%s' % (start_range, end_range)

		try:
			response = urllib2.urlopen(url)
		except urllib2.URLError as e:
			msg = 'url is not correct http://debian.org/debian/README'
			logger.info(msg)
			logger.info(e.reason)
			print msg
			return None
		
		msg = url + ' downloaded'
		print msg
		logger.info(msg)
		return response.read()
		
class FtpDownload():
	#connect to ftp. if user/password not given it will try to log anonymously 
	def ftp_connect(self, host, password, user, path='/'):
		link = FTP(host = host, timeout = 5)
		if user != '' and password != '':
			link.login(passwd = password, user = user)
		else :
			link.login()
		link.cwd(path)
		return link	

	def download(self, url, url_parsed, filename, download_folder, logger, download_file_name = ''):
		ftp_pass = ftp_user = ''
		try:
			#checking url
			ftp_url_details = url_parsed.netloc.split('@')
		except Exception as ex:
			msg = 'ftp url is not correct ftp://username:passowrd@ftp.website.com/downloads.rss'
			logger.info(msg)
			logger.info(ex)
			print msg
			return None

		try:
			#checking for username & password
			ftp_user_detail = ftp_url_details[0].split(':')
			ftp_user = ftp_user_detail[0]
			ftp_pass = ftp_user_detail[1]
		except Exception as ex:
			msg = 'username & password not provided. anonymous mode enabled'
			logger.info(msg)
			logger.info(ex)
			print msg

		try:
			#checking for path from url	
			ftp_path_array = url_parsed.path.split('/')
			ftp_url = ftp_url_details[len(ftp_user_detail)-1]
			ftp_file_name = ftp_path_array[len(ftp_path_array) - 1]
			ftp_path = url_parsed.path.replace(ftp_file_name, '')
		except Exception as ex:
			msg = 'ftp url is not correct ftp://username:passowrd@ftp.website.com/downloads.rss'
			logger.info(msg)
			logger.info(ex)
			print msg
			return None

		try:
			#connecting to ftp
			link = self.ftp_connect(host = ftp_url, password = ftp_pass, user = ftp_user, path = ftp_path)
		except Exception as ex:
			msg = 'ftp username or passowrd or url is not correcr'
			logger.info(msg)
			logger.info(ex)
			print msg
			return None

		try:
			#checkeing remote fie size
			remote_file_size = link.size(ftp_file_name)
		except Exception as ex:
			msg = 'file not found'
			logger.info(msg)
			logger.info(ex)
			print msg
			return None	


		if download_file_name == '':
			local_filename = download_folder + '/' + filename  + '.rss'
		else: 
			local_filename = download_folder + '/' + download_file_name	

		#checkeing file already downloaded or not
		if os.path.isfile(local_filename):
			if remote_file_size ==	os.path.getsize(local_filename):
				msg = 'file already downloaded'
				logger.info(msg)
				print msg
				return None
			else:	
				download_file = open(local_filename,"ab")
		else:
			download_file = open(local_filename,"wb")

		#looping until the local file is same size as remote 		
		while remote_file_size > download_file.tell():
			try:
				if download_file.tell() != 0:
					#file partially downloaded
					# link.set_debuglevel(2)
					link.voidcmd('TYPE I')
					sock = link.transfercmd('RETR ' + ftp_file_name, download_file.tell())
					while True:
					  block = sock.recv(1024*1024)
					  if not block:
					      break
					  link.voidcmd('NOOP')
					  download_file.write(block)
					sock.close()
				else:
					link.retrbinary('RETR ' + ftp_file_name, download_file.write)
			except Exception as ex:
				msg = 'file not found'
				logger.info(msg)
				logger.info(ex)
				print msg
				return None

		#close file
		download_file.close()
		msg = 'file downloaded at ' + local_filename
		print msg
		logger.info(msg)

class Downloader:
	def __init__(self, url, logger, filename = ''):
		self.logger = logger
		self.url = url
		self.url_parsed = urlparse(url)
		#checking if the url scheme is http/https/ftp
		if self.url_parsed.scheme in ['http', 'https']:
			#creating HttpDownload object and setting it to downloader
			self.downloader = HttpDownload()
		elif self.url_parsed.scheme in ['ftp']:
			#creating FtpDownload object and setting it to downloader 
			self.downloader = FtpDownload()
		self.download_filename = filename	
		logger.info('Method ' + self.url_parsed.scheme)

	#creating file name from url	
	def safe_file_name(self):
		return "".join(x for x in self.url if x.isalnum())

	def download(self, download_folder):
		logger.info('downloading from ' + self.url)
		#calling download function from downloader object
		download_file_name = ''
		if self.download_filename != '': 
			download_file_name = self.download_filename	
			file_name = download_file_name
		else:
			file_name = self.safe_file_name()	
		self.downloader.download(self.url, self.url_parsed, file_name, download_folder, self.logger, download_file_name)
		return file_name

#intilizing logging
logging.basicConfig(format='%(asctime)s %(message)s', filename='basic.log',level=logging.INFO)
logger = logging.getLogger('log')
logger.info('init')

try:
	#checking for arguments
	opts, args = getopt.getopt(sys.argv[1:],"feed:output:",["feed=","output="])
except getopt.GetoptError as e:
	#arguments are not corret exit from program
	print 'python downloader.py --feed=<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>'
	logger.info('argv error')
	sys.exit(1)
 
#set default download folder  
download_folder = os.getcwd() + '/download'
	
for opt, arg in opts:
	if opt in ('--feed'):
		#setting url
		url = arg
	elif opt in ('--output'):
		#setting download folder
		download_folder = arg	

logger.info('feed url is ' + url)
logger.info('download folder url is ' + download_folder)

#checking download folder exits otherwise crete folder
if not os.path.exists(download_folder):
	try:
	  os.makedirs(download_folder)
	except OSError:
		#download folder can be created exit from program
		if not os.path.isdir(download_folder):
			logger.info('Can not create download folder ' + download_folder)
			print 'Can not create download folder ' + download_folder
			sys.exit(1)

#create Downloader object with url and logger
base = Downloader(url, logger)
#calling download function 
file_name = base.download(download_folder)

download_file = download_folder + '/' + file_name + '.rss'
output_file = open(download_file,"r")
data = output_file.read()
output_file.close()
os.remove(download_file)
dom = parseString(data)
for i in range(10):
	t = ThreadUrl(queue)
	t.setDaemon(True)
	t.start()
for item in dom.getElementsByTagName('item'):
	download_file_link = item.getElementsByTagName('link')[0].childNodes[0].data
	download_file_parsed = urlparse(download_file_link)
	# print download_file_parsed
	download_file_array = download_file_parsed.path.split('/')
	download_file_name = item.getElementsByTagName('title')[0].childNodes[0].data
	port = 80
	if download_file_parsed.scheme == 'ftp':
		port = 21
	conn = httplib.HTTPConnection(download_file_parsed.netloc, port)
	conn.request("GET", download_file_parsed.path, headers={'Range': 'bytes=0-10'})
	resp = conn.getresponse()
	if resp.status <> 206:
		# base = Downloader(download_file_link, logger, download_file_name)
		# queue.put(base)
		print '++++++++++++++++++'
	else:
		total_size = resp.getheader('content-range').split('/')[1]
		start_range = 0
		end_range = int(total_size)/2

		lock = threading.Lock()
		thread = FetchUrl(lock, download_file_link, download_file_name, download_folder, logger, start_range, end_range)
		thread.start()
		thread.join()
		start_range = start_range + 1
		end_range = total_size
		thread = FetchUrl(lock, download_file_link, download_file_name, download_folder, logger, start_range, end_range)
		thread.start()
		thread.join()
		print '-----------------'	
	# exit(1)	
queue.join()	