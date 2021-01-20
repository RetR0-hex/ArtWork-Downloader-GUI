import os.path
import time
import re
import logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from urllib.parse import urlparse


class MutableStructure:

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
image_counter = MutableStructure(0, 0)
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
            print("Downloading ChromeWebdriver...")
            self.driver = webdriver.Chrome(ChromeDriverManager(log_level=0).install(), options=self.chrome_options)
        except ValueError as e:
            print("ERROR: Chrome is not installed!")
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
    print('''
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
        print("Error: Enter a valid Directory! ")
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
                print("Outdated Cookies.")
                return True
        except KeyError:
            pass
    return False


def check_existing_images(existing_images, artwork_id):
    for x in existing_images:
        if x["id"] == artwork_id:
            return True

    return False





