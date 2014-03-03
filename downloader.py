import urllib2
import logging
import sys
import getopt
import os
from urlparse import urlparse
from ftplib import FTP

class HttpDownload():
	def download(self, url, url_parsed, filename, download_folder, logger):
		download_file = download_folder + '/' + filename + '.rss'
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

		msg = 'file downloaded at ' + download_file
		print msg
		logger.info(msg)

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

	def download(self, url, url_parsed, filename, download_folder, logger):
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

		local_filename = download_folder + '/' + filename  + '.rss'
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
	def __init__(self, url, logger):
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
		logger.info('Method ' + self.url_parsed.scheme)

	#creating file name from url	
	def safe_file_name(self):
		return "".join(x for x in self.url if x.isalnum())

	def download(self, download_folder):
		logger.info('downloading from ' + self.url)
		#calling download function from downloader object
		self.downloader.download(self.url, self.url_parsed, self.safe_file_name(), download_folder, self.logger)	

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
base.download(download_folder)
