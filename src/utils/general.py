import glob
import os.path
import pathlib
import time
import re
import logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from urllib.parse import urlparse


successful_download_dict = []


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


# THis is to keep track of image counters and total values out of threads
image_counter = MutableStructure(0, 0)
save_dir_global = save_dir_string("")

def intro():
    print('''
                    _                      _      _____                      _                 _           
         /\        | |                    | |    |  __ \                    | |               | |          
        /  \   _ __| |___      _____  _ __| | __ | |  | | _____      ___ __ | | ___   __ _  __| | ___ _ __ 
       / /\ \ | '__| __\ \ /\ / / _ \| '__| |/ / | |  | |/ _ \ \ /\ / | '_ \| |/ _ \ / _` |/ _` |/ _ | '__|
      / ____ \| |  | |_ \ V  V | (_) | |  |   <  | |__| | (_) \ V  V /| | | | | (_) | (_| | (_| |  __| |   
     /_/    \_|_|   \__| \_/\_/ \___/|_|  |_|\_\ |_____/ \___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|\___|_|   

                                                                                By RetR0-hex
                                                                                (Last tested on 06/11/2020)      

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


# glob.glob functions returns a list which cannot be worked with os.listdir so we
# use this function to kinda join the list and produces a string that can be iterated on
def user_directory_input(dir_input_question):
    path_to_directory_user = input(dir_input_question)
    path_to_directory = glob.glob(path_to_directory_user)
    if os.path.isdir(pathlib.Path(path_to_directory_user)):
        print("\n Ok the File Exists \n")
        return list_dir_to_string(path_to_directory)
    else:
        print("\n Error! This Directory doesn't exist \n")
        user_directory_input(dir_input_question)


def make_directory(path, artist_name):
    new_path = os.path.join(path, artist_name)
    if os.path.exists(new_path):
        pass
    else:
        os.makedirs(new_path)
    return new_path


def infinite_scroll(scroll_pause, driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        print("Waiting for the page to fully load, Please Wait. (Don't Panic)")
        if new_height == last_height:
           break
        last_height = new_height


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






