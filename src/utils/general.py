import os.path
import time
import re
import logging
import random
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from urllib.parse import urlparse
from queue import Queue

class IMAGECOUNTERCLASS:

    def __init__(self, val, _max):
        self.val = val
        self.max = _max

    def increment(self):
        self.val = self.val + 1
        return self.val

    def decrement(self):
        self.val = self.val - 1


class save_dir_string:
    def __init__(self, save_dir):
        self.save_dir = save_dir

    def update(self, save_dir):
        self.save_dir = save_dir


successful_download_dict = []
# THis is to keep track of image counters and total values out of threads
image_counter = IMAGECOUNTERCLASS(0, 0)
print_Queue = Queue(maxsize=0)
save_dir_global = save_dir_string("")


class WebDriverChrome:

    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.622.69 Safari/537.36")
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])


    def set_headless_options(self):
        self.chrome_options.add_argument("--headless")

    def set_driver(self):
        logger = logging.getLogger('WDM')
        logger.disabled = True
        try:
            print_Queue.put("Downloading ChromeWebdriver...")
            self.driver = webdriver.Chrome(ChromeDriverManager(log_level=0).install(), options=self.chrome_options)
        except ValueError as e:
            print_Queue.put("ERROR: Chrome is not installed!")
            exit(0)

    def set_windows_size(self, width, height):
        self.driver.set_window_size(width, height)


class ProgVars:
    def __init__(self):
        self.url = None
        self.save_location = None
        self.username = None
        self.password = None
        self.threads = 3


def intro():
    print_Queue.put('''
     _____     _   _ _ _         _   ____                _           _         
    |  _  |___| |_| | | |___ ___| |_|    \ ___ _ _ _ ___| |___ ___ _| |___ ___ 
    |     |  _|  _| | | | . |  _| '_|  |  | . | | | |   | | . | .'| . | -_|  _|
    |__|__|_| |_| |_____|___|_| |_,_|____/|___|_____|_|_|_|___|__,|___|___|_|
    
                                                        By RetR0-hex
                                                        (Last tested on 20/01/2021)      
''')


def url_validator(url):
    try:
        test = urlparse(url)
        # "All" function returns true if all the elements inside it are true so its a an AND function
        return all([test.scheme, test.netloc, test.path])
    except:
        return False

def random_useragent():
    useragents = [

        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2866.71 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2656.18 Safari/537.36",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.3319.102 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582",
        "Mozilla/5.0 (X11) AppleWebKit/62.41 (KHTML, like Gecko) Edge/17.10859 Safari/452.6",
        "Mozilla/5.0 (X11; Linux ppc64le; rv:75.0) Gecko/20100101 Firefox/75.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/75.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:75.0) Gecko/20100101 Firefox/75.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:70.0) Gecko/20191022 Firefox/70.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:70.0) Gecko/20190101 Firefox/70.0",
        "Mozilla/5.0 (Windows; U; Windows NT 9.1; en-US; rv:12.9.1.11) Gecko/20100821 Firefox/70",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/58.0.1",
        "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; tr-TR) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; ko-KR) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; fr-FR) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; cs-CZ) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; ja-JP) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; zh-cn) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; ja-jp) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; ja-jp) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; zh-cn) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; sv-se) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; ko-kr) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27",
        "Mozilla/5.0 (Windows; U; Windows NT 5.0; en-en) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; nl-nl) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; ja-jp) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; de-de) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_7; en-us) AppleWebKit/533.4 (KHTML, like Gecko) Version/4.1 Safari/533.4",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; nb-no) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16",
        "Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14",
        "Mozilla/5.0 (Windows NT 6.0; rv:2.0) Gecko/20100101 Firefox/4.0 Opera 12.14",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0) Opera 12.14"
    ]

    return useragents[random.randint(0, 35)]


def artwork_url_verifier(url):
    match = re.search(r"(?!www.)(\w+)(?=.com|.net)", url).group()
    if match == 'artstation' or match == 'deviantart' or match == 'pixiv':
        return True
    else:
        return False


def list_dir_to_string(path):
    try:
        directory = str.join(' ', path)
        return directory
    except TypeError:
        pass


def dir_exists(path):
    if not os.path.exists(path):
        print_Queue.put("Error: Enter a valid Directory! ")
        exit(0)


def check_chrome_driver(path=""):
    if os.path.exists(os.path.join(path, "chromedriver.exe")):
        return True
    else:
        return False


def make_directory(path, artist_name):
    new_path = os.path.join(path, artist_name)
    if os.path.exists(new_path):
        pass
    else:
        os.makedirs(new_path)
    return new_path


def make_windows_legal(string):
    string = re.sub(r"[!@#$%^&*(),.?\"/;:{}|<>]", "_", string)
    return string


def ext_finder(url):
    ext = re.search(r'.\w+$', url).group()
    return ext


def cookies_expiry_check(cookies):
    for cookie in cookies:
        try:
            if int(cookie['expiry']) > int(time.time()):
                pass
            else:
                print_Queue.put("Outdated Cookies.")
                return True
        except KeyError:
            pass
    return False


def check_existing_images(existing_images, artwork_id):
    for x in existing_images:
        if x["id"] == artwork_id:
            return True

    return False





