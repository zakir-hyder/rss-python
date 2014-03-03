import urllib2
import logging
import sys
import getopt
import os
import Queue
import threading
from urlparse import urlparse
from ftplib import FTP

queue = Queue.Queue()

class ThreadUrl(threading.Thread):
	"""Threaded Url Grab"""
	def __init__(self, queue):
	  threading.Thread.__init__(self)
	  self.queue = queue

	def run(self):
	  while True:
	    base = self.queue.get()
	    msg = 'queue start for url ' + base.url
	    logger.info(msg)
	    print msg
	    base.download(download_folder)
	    msg = 'queue end for url ' + base.url
	    logger.info(msg)
	    print msg
	    self.queue.task_done()

class HttpDownload():
	def download(self, url, url_parsed, filename, download_folder, logger):
		download_file = download_folder + '/' + filename + '.rss'
		try:
			response = urllib2.urlopen(url)
		except urllib2.URLError as e:
			msg = 'url is not correct http://ftp.debian.org/debian/README'
			logger.info(msg)
			logger.info(e.reason)
			print msg
			return None
		else:
			remote_file_size = response.info()['Content-Length']

		req = urllib2.Request(url)
		if os.path.isfile(download_file):
			local_file_size = os.path.getsize(download_file)
			if int(remote_file_size) ==	int(local_file_size):
				msg = 'file already downloaded'
				logger.info(msg)
				print msg
				return None
			else:	
				output_file = open(download_file,"a")				
				req.headers['Range'] = 'bytes=%s-%s' % (local_file_size, remote_file_size)		
		else:
			output_file = open(download_file,"w")

		if 'Range' in req.headers:
			try:
				response = urllib2.urlopen(req)
			except urllib2.URLError as e:
				msg = 'url is not correct http://ftp.debian.org/debian/README'
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

		msg = 'file downloaded at ' + download_file
		print msg
		logger.info(msg)


class FtpDownload():
	def ftp_connect(self, host, password, user, path='/'):
		link = FTP(host = host, timeout = 5)
		if user != '' and password != '':
			link.login(passwd = password, user = user)
		else :
			link.login()
		link.cwd(path)
		return link	

	def download(self, url, url_parsed, filename, download_folder, logger):
		ftp_pass = ftp_user = ''
		try:
		  ftp_url_details = url_parsed.netloc.split('@')
		except Exception as ex:
			msg = 'ftp url is not correct ftp://username:passowrd@ftp.website.com/downloads.rss'
			logger.info(msg)
			logger.info(ex)
			print msg
			return None

		try:
		  ftp_user_detail = ftp_url_details[0].split(':')
		  ftp_user = ftp_user_detail[0]
		  ftp_pass = ftp_user_detail[1]
		except Exception as ex:
			msg = 'username & password not provided. anonymous mode enabled'
			logger.info(msg)
			logger.info(ex)
			print msg

		try:	
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
			link = self.ftp_connect(host = ftp_url, password = ftp_pass, user = ftp_user, path = ftp_path)
		except Exception as ex:
			msg = 'ftp username or passowrd or url is not correcr'
			logger.info(msg)
			logger.info(ex)
			print msg
			return None

		try:
			file_size = link.size(ftp_file_name)
		except Exception as ex:
			msg = 'file not found'
			logger.info(msg)
			logger.info(ex)
			print msg
			return None	

		local_filename = download_folder + '/' + filename  + '.rss'
		if os.path.isfile(local_filename):
			if file_size ==	os.path.getsize(local_filename):
				msg = 'file already downloaded'
				logger.info(msg)
				print msg
				return None
			else:	
				download_file = open(local_filename,"ab")
		else:
			download_file = open(local_filename,"wb")	
		while file_size > download_file.tell():
			try:
				if download_file.tell() != 0:
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
		download_file.close()
		msg = 'file downloaded at ' + local_filename
		print msg
		logger.info(msg)

class Downloader:
	def __init__(self, url, logger):
		self.logger = logger
		self.url = url
		self.url_parsed = urlparse(url)
		if self.url_parsed.scheme in ['http', 'https']:
			self.downloader = HttpDownload()
		elif self.url_parsed.scheme in ['ftp']: 
			self.downloader = FtpDownload()
		logger.info('Method ' + self.url_parsed.scheme)
		
	def safe_file_name(self):
		return "".join(x for x in self.url if x.isalnum())

	def download(self, download_folder):
		logger.info('downloading from ' + self.url)
		self.downloader.download(self.url, self.url_parsed, self.safe_file_name(), download_folder, self.logger)	

logging.basicConfig(format='%(asctime)s %(message)s', filename='basic.log',level=logging.INFO)
logger = logging.getLogger('log')
logger.info('init')

try:
  opts, args = getopt.getopt(sys.argv[1:],"feed:output:",["feed=","output="])
except getopt.GetoptError as e:
  print 'python downloader.py --feed=<RSS-Feed-URL>||<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>'
  logger.info('argv error')
  sys.exit(1)
  
download_folder = os.getcwd() + '/download'
	
for opt, arg in opts:
	if opt in ('--feed'):
		urls = arg.split('-AH-')
	elif opt in ('--output'):
		download_folder = arg	

logger.info('download folder url is ' + download_folder)

if not os.path.exists(download_folder):
	try:
	  os.makedirs(download_folder)
	except OSError:
	  if not os.path.isdir(download_folder):
	  	logger.info('Can not create download folder ' + download_folder)
	  	print 'Can not create download folder ' + download_folder
	  	sys.exit(1)

for i in range(5):
	t = ThreadUrl(queue)
	t.setDaemon(True)
	t.start()
  
#populate queue with data   
for url in urls:
	if url != '':
		base = Downloader(url, logger)
		queue.put(base)

#wait on the queue until everything has been processed     
queue.join()
