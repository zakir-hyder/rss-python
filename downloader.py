import urllib2, logging, sys, getopt, os
from urlparse import urlparse
from ftplib import FTP

class HttpDownload():
	def __init__(self):
		print 'http class'

	def download(self, url, filename, download_folder):
		download_file = download_folder + '/' + filename + '.rss'
		print download_file
		existSize = 0
		loop = 1


		try:
			response = urllib2.urlopen(url)
		except urllib2.URLError as e:
			return e.reason
		else:
			remote_file_size = response.info()['Content-Length']
			print remote_file_size

		req = urllib2.Request(url)
		if os.path.isfile(download_file):
			outputFile = open(download_file,"a")
			existSize = os.path.getsize(download_file)
			req.headers['Range'] = 'bytes=%s-%s' % (existSize, remote_file_size)		
		else:
			outputFile = open(download_file,"w")


		try:
			response = urllib2.urlopen(req)
		except urllib2.URLError as e:
			return e.reason
		else:
			remote_file_size = response.info()['Content-Length']
			print remote_file_size	

			if int(remote_file_size) == existSize:
				loop = 0

			while loop:
				data = response.read(8192)
				print data
				if not data:
					break
				outputFile.write(data)
			# html = response.read()	
			# print 'asas'			
			# outputFile = open(download_file,"w")
			# outputFile.write(html)
			outputFile.close()
		return download_file + ' file downloaded'


class FtpDownload():
	def ftp_connect(self, host, password, user, path = '/'):
		link = FTP(host = host, timeout = 5)
		if (user and password):
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
			return msg

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
			return msg

		try:
			link = self.ftp_connect(host = ftp_url, password = ftp_pass, user = ftp_user, path = ftp_path)
		except Exception as ex:
			msg = 'ftp username or passowrd or url is not correcr'
			logger.info(msg)
			logger.info(ex)
			print msg
			return msg

		try:
			file_size = link.size(ftp_file_name)
		except Exception as ex:
			msg = 'file not found'
			logger.info(msg)
			logger.info(ex)
			print msg
			return msg	

		local_filename = download_folder + '/' + filename  + '.rss'
		download_file = open(local_filename,"wb")
		while file_size != download_file.tell():
			try:
				if download_file.tell() != 0:
					link.retrbinary('RETR ' + ftp_file_name, download_file.write, download_file.tell())
				else:
					link.retrbinary('RETR ' + ftp_file_name, download_file.write)
			except Exception as ex:
				msg = 'file not found'
				logger.info(msg)
				logger.info(ex)
				print msg
				return msg

		msg = 'file downloaded at ' + local_filename
		print msg
		logger.info(msg)
		return msg		

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
		msg = self.downloader.download(self.url, self.url_parsed, self.safe_file_name(), download_folder, self.logger)	
		self.logger.info(msg)



logging.basicConfig(format='%(asctime)s %(message)s', filename='basic.log',level=logging.INFO)
logger = logging.getLogger('log')
logger.info('init')

try:
  opts, args = getopt.getopt(sys.argv[1:],"feed:output:",["feed=","output="])
except getopt.GetoptError as e:
  print 'python downloader.py --feed=<RSS-Feed-URL> --output=<PATH-TO-DIRECTORY>'
  logger.info('argv error')
  sys.exit(1)
  
download_folder = os.getcwd() + '/download'
	
for opt, arg in opts:
	if opt in ('--feed'):
		url = arg
	elif opt in ('--output'):
		download_folder = arg	

logger.info('feed url is ' + url)
logger.info('download folder url is ' + download_folder)

if not os.path.exists(download_folder):
	try:
	  os.makedirs(download_folder)
	except OSError:
	  if not os.path.isdir(download_folder):
	  	logger.info('Can not create download folder ' + download_folder)
	  	print 'Can not create download folder ' + download_folder
	  	sys.exit(1)

base = Downloader(url, logger)
base.download(download_folder)
