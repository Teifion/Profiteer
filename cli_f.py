from ftplib import FTP
import urllib.request
import signal
import sys
import time
import re

shell_patterns = (
    (re.compile(r"''([^']*)''"), '\033[1;1m\\1\033[30;0m'),# Bold
    (re.compile(r'__([^_]*)__'), '\033[1;4m\\1\033[30;0m'),# Underline
    (re.compile(r"\*\*([^*]*)\*\*"), '\033[1;5m\\1\033[30;0m'),# Blink + Bold
    
    (re.compile(r"\[r\](.*?)\[\/r\]"),          '\033[31m\\1\033[30;0m'),# Red
    (re.compile(r"\[g\](.*?)\[\/g\]"),      '\033[32m\\1\033[30;0m'),# Green
    (re.compile(r"\[y\](.*?)\[\/y\]"),      '\033[33m\\1\033[30;0m'),# Yellow
    (re.compile(r"\[b\](.*?)\[\/b\]"),          '\033[34m\\1\033[30;0m'),# Blue
    (re.compile(r"\[m\](.*?)\[\/m\]"),  '\033[35m\\1\033[30;0m'),# Magenta
    (re.compile(r"\[c\](.*?)\[\/c\]"),          '\033[36m\\1\033[30;0m'),# Cyan
)

html_patterns = (
    (re.compile(r"''([^']*)''"),        r'<span style="font-weight:bold;">\1</span>'),
    (re.compile(r'__([^_]*)__'),        r'<span style="text-decoration:underline;">\1</span>'),
    (re.compile(r"\*\*([^*]*)\*\*"),    r'<span style="font-weight:bold;font-style:italic;">\1</span>'),
    
    (re.compile(r"\[r\](.*?)\[\/r\]"),  r'<span style="color: #A00;">\1</span>'),# Red
    (re.compile(r"\[g\](.*?)\[\/g\]"),  r'<span style="color: #0A0;">\1</span>'),# Green
    (re.compile(r"\[y\](.*?)\[\/y\]"),  r'<span style="color: #AA0;">\1</span>'),# Yellow
    (re.compile(r"\[b\](.*?)\[\/b\]"),  r'<span style="color: #00A;">\1</span>'),# Blue
    (re.compile(r"\[m\](.*?)\[\/m\]"),  r'<span style="color: #A0A;">\1</span>'),# Magenta
    (re.compile(r"\[c\](.*?)\[\/c\]"),  r'<span style="color: #0AA;">\1</span>'),# Cyan
    
    # Whitespace
    (re.compile(r"\n"),                 r'<br />'),
    (re.compile(r"\r"),                 r'<br />'),
    (re.compile(r"  "),                 r'&nbsp;&nbsp;'),
)

def shell_text(text):
    """
    Converts text to display in the shell with pretty colours
    
    Bold:           ''{TEXT}''
    Underline:      __{TEXT}__
    Blink:          **{TEXT}** <= Also makes it bold
    
    Colour:         <colour>{TEXT}</colour> (with the pointed brackets)
    Colours supported: Red, Green, Yellow, Blue, Magenta, Cyan
    """
    if type(text) != str:
        return text
    
    for regex, replacement in shell_patterns:
        text = regex.sub(replacement, text)
    
    # text = text.replace("[t][/t]", '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')
    return text

padding = "".join([" " for x in range(0, 8*1024)])

class Timeout_exception(Exception):
	def __init__(self, value="Timeout error"):
		self.value = value
	
	def __str__(self):
		return repr(self.value)

class Timeout_function:
	def __init__(self, function, timeout):
		self.timeout	= timeout
		self.function	= function
	
	def handle_timeout(self, signum, frame):
		raise Timeout_exception()
	
	def __call__(self, *args):
		old = signal.signal(signal.SIGALRM, self.handle_timeout)
		signal.alarm(self.timeout)
		try:
			result = self.function(*args)
		finally:
			signal.alarm(0)
			signal.signal(signal.SIGALRM, old)
		signal.alarm(0)
		return result

def progressbar(it, prefix = "", size = 60, with_eta=False):
	"""
	for i in progressbar(range(15), "Computing: ", 40):
		 time.sleep(0.1) # long computation
	"""
	
	count = len(it)
	start_time = time.time()
	
	def _show(_i):
		eta_string = ""
		if _i > 0:
			time_so_far = time.time() - start_time
			time_per_item = time_so_far / _i
			eta = (count - _i) * time_per_item
			
			if with_eta:
				eta_string = "  eta %s" % round(eta, 1)
			
			if eta < 0.1:
				eta_string = "           "
		
		x = int(size*_i/count)
		sys.stdout.write("%s[%s%s] %i/%i%s\r" % (prefix, "#"*x, "."*(size-x), _i, count, eta_string))
		sys.stdout.flush()
	
	_show(0)
	for i, item in enumerate(it):
		yield item
		_show(i+1)
	# sys.stdout.write("".join([" " for i in range(size + 40)]))
	# sys.stdout.flush()
	
	# Cleanup
	time_so_far = time.time() - start_time
	
	if with_eta:
		eta_string = " in %ss" % round(time_so_far, 1)
		
		sys.stdout.write("%s[%s%s] %i/%i%s\r" % (prefix, "#"*size, "."*0, count, count, eta_string))
		sys.stdout.flush()
	
	print()

def upload(ftp_host, ftp_user, ftp_pass, files, delay=2, verbose=True):
	if verbose: print("Connecting")
	ftp = FTP(ftp_host, ftp_user, ftp_pass)
	
	# if verbose:
	print("Connected to %s, uploading %s files" % (ftp_user, len(files)))
	
	for file_name, file_path in progressbar(files.items(), "Uploading: ", 60, True):
		fname = 'STOR %s' % file_name
		data = open(file_path, 'rb')
		
		ftp.storbinary(fname, data)
		time.sleep(int(delay))
	
	ftp.quit()
	if verbose: print("Disconnected")

