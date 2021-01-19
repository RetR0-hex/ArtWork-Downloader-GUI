import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.utils import general as gen
import re
import random
import time
import selenium.common
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count
from src.utils.txtDatabaseHandling import json_to_dict, dict_to_json
from src.utils.general import image_counter, successful_download_dict

# Artwork extended fetch = pixiv.net/ajax/illust/{artwork_id} All artworks fetch of an artist =
# https://www.pixiv.net/ajax/user/{artist_id}}/profile/all?lang=en header required to request images =  {"referer":
# f"https://www.pixiv.net/member_illust.php?mode=medium&illust_id={artwork_id}}"} header = {"referer":
# f"https://www.pixiv.net/en/artworks/{artist_id}}"} both work


class PixivCore:
    def __init__(self, arguments):
        self.request_session = requests.Session()
        retry = Retry(total=10, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        self.request_session.mount('https://', HTTPAdapter(max_retries=retry))
        self.request_session.mount('http://', HTTPAdapter(max_retries=retry))
        self.cookie_for_header = ""
        self.is_user_logged_in = False
        self.arguments = arguments
        self.artist_link = self.arguments.url
        if self.artist_link[-1] != '/':
            self.artist_link = self.artist_link + '/'
        self.artist_id = re.search(r'(?!users/")\d+/', self.artist_link).group()
        self.artist_id = re.sub(r"\/", "", self.artist_id)
        self.artist_name = gen.make_windows_legal(self.get_artist_name())

        if self.arguments.username:
            self.chrome = gen.WebDriverChrome()
            self.cookies_load()
            self.is_user_logged_in = True
        else:
            # Checks if cookies exists or not, if they do.. they are loaded into request's session
            if os.path.exists(os.path.join('cookies', "cookies_pixiv.json")):
                print("Reloading Existing cookies.")
                json_cookies = json_to_dict('cookies', "cookies_pixiv.json")
                if not gen.cookies_expiry_check(json_cookies):
                    self.set_cookies_request(json_cookies)
                    self.is_user_logged_in = True

    def cookies_load(self, recursion=False):
        if os.path.exists(os.path.join('cookies', "cookies_pixiv.json")):
            if not recursion:
                print("Reloading Existing cookies")
            json_cookies = json_to_dict('cookies', "cookies_pixiv.json")
            if not gen.cookies_expiry_check(json_cookies):
                self.set_cookies_request(json_cookies)
            else:
                self.save_cookies()
        else:
            print("Didn't find existing cookies, generating new ones...")
            self.save_cookies()

    def save_cookies(self):
        if os.path.exists('cookies'):
            result = self.auto_login()
            if result != 'wrong_credentials':
                cookies = self.cookies_cleaner(result)
                dict_to_json(cookies, 'cookies', 'cookies_pixiv.json')
                self.cookies_load(recursion=True)
            else:
                cookies = self.login()
                dict_to_json(cookies, 'cookies', 'cookies_pixiv.json')
                self.cookies_load(recursion=True)
        else:
            os.mkdir('cookies')
            self.save_cookies()

    def cookies_cleaner(self, cookies):
        keep_data_list = ['privacy_policy_agreement', 'first_visit_datetime_pc', 'yuid_b', 'device_token',
                          '__cfduid', 'PHPSESSID', 'p_ab_id_2', 'p_ab_d_id', 'p_ab_id']
        return_cookies = []
        for data in keep_data_list:
            try:
                return_cookies.append(next(x for x in cookies if x["name"] == data))
            except StopIteration:
                pass
        return return_cookies

    def login(self):
        login_url = 'https://accounts.pixiv.net/login'
        self.chrome.set_driver()
        self.chrome.set_windows_size(1000, 1000)
        self.chrome.driver.get(login_url)
        while True:
            current_url = self.chrome.driver.current_url
            if current_url != login_url:
                if self.chrome.driver.execute_script('''return document.readyState''') == 'complete':
                    break
            else:
                time.sleep(3)
        cookies = self.chrome.driver.get_cookies()
        cookies = self.cookies_cleaner(cookies)
        self.chrome.driver.close()
        return cookies

    def auto_login(self):
        self.chrome.set_driver()
        self.chrome.set_windows_size(1000, 1000)
        login_url = 'https://accounts.pixiv.net/login'
        self.chrome.driver.get(login_url)
        try:
            self.chrome.driver.find_element_by_css_selector('''#LoginComponent > form > div 
                                                            > div > input''').send_keys(self.arguments.username)
            self.chrome.driver.find_element_by_css_selector('''#LoginComponent > form > div.input-field-group
                                                            > div:nth-child(2) > input''').send_keys(
                self.arguments.password)
            # self.chrome.driver.find_element_by_css_selector('#LoginComponent > form > button').click()
            while True:
                current_url = self.chrome.driver.current_url
                if self.chrome.driver.execute_script('''return document.readyState''') == 'complete':
                    if current_url != login_url:
                        break
                    else:
                        time.sleep(3)
            cookies = self.chrome.driver.get_cookies()
            cookies = self.cookies_cleaner(cookies)
            self.chrome.driver.close()
            return cookies
        except selenium.common.exceptions.NoSuchElementException:
            print("Captcha.....")
            self.chrome.driver.close()
            return 'wrong_credentials'

    def set_cookies_request(self, json_cookies):
        for cookie in json_cookies:
            name = cookie['name']
            value = cookie['value']
            # Cookies for headers to bypass scraping protection.
            self.cookie_for_header = self.cookie_for_header + name + '=' + value + "; "
            self.request_session.cookies[name] = str(value)

    def request(self, url, **kwargs):
        res = self.request_session.get(url, **kwargs)
        res.raise_for_status()
        return res

    def get_artist_name(self):
        url = f'https://www.pixiv.net/ajax/user/{self.artist_id}/profile/top?lang=en'
        res = self.request(url).json()
        name = res['body']['extraData']['meta']['title']
        return name

    def extended_artwork_fetch(self, artwork_id):
        url = f'https://www.pixiv.net/ajax/illust/{artwork_id}'
        if self.is_user_logged_in:
            headers = {
                "sec-ch-ua": '"\"Not\\A;Brand";v="99", "Chromium";v="86", "Microsoft Edge";v="86"',
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36 Edg/86.0.622.63",
                "cookie": self.cookie_for_header
            }
            res = self.request(url, headers=headers).json()
        else:
            res = self.request(url).json()
        return res['body']

    def artist_artwork_id_list(self, artist_id):
        print("Getting image links.")
        url = f'https://www.pixiv.net/ajax/user/{artist_id}/profile/all?lang=en'
        # Cookies in headers as needed by the new pixiv website
        if self.is_user_logged_in:
            header = {
                "referer": f"https://www.pixiv.net/en/users/{artist_id}",
                "sec-ch-ua": '"\"Not\\A;Brand";v="99", "Chromium";v="86", "Microsoft Edge";v="86"',
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36 Edg/86.0.622.63",
                "cookie": self.cookie_for_header
            }
            res = self.request(url, headers=header).json()
        else:
            res = self.request(url).json()
        res = res['body']['illusts']
        res = list(res.keys())
        return res

    def get_title(self, a_extended):
        title = a_extended['illustTitle']
        return title

    def download_artwork(self, save_dir, artwork_id, check_existing):
        current_info = {
                    'artwork_id': artwork_id,
                    'isDownloaded': True
                     }

        if check_existing:
            for x in self.existing_images:
                if x["artwork_id"] == artwork_id:
                    print(f"ID: {artwork_id} is already present.")
                    image_counter.val += 1
                    # I know this looks ugly and barely works
                    successful_download_dict.append(current_info)
                    return

        artwork_extended = self.extended_artwork_fetch(artwork_id)
        title = gen.make_windows_legal(self.get_title(artwork_extended))
        url = artwork_extended['urls']['original']
        ext = gen.ext_finder(url)
        header = {"referer": f'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={artwork_id}'}
        # Image_counter.increments() ads +1 to the class member "val" and returns val after the increment
        print(f"Currently Downloading: {title} ({str(image_counter.increment())}/{str(image_counter.max)})")
        r_stream = self.request(url, headers=header, stream=True)
        path_with_name = os.path.join(save_dir, title + f"_by{self.artist_name}" + ext)
        img_number = random.randint(0, 1000)
        if os.path.exists(path_with_name):
            path_with_name = os.path.join(save_dir, title + f"_by{self.artist_name}_{img_number}" + ext)
        with open(path_with_name, 'wb') as file:
            try:
                for data in r_stream:
                    file.write(data)
            except Exception as e:
                print(f"{title}")
                print(f"Error {e}")

        successful_download_dict.append(current_info)

    def save_artwork(self):
        save_dir = self.arguments.save_location
        starting_time = time.time()
        # CHecks if the download folder already exists
        if os.path.exists(os.path.join(save_dir, f'{self.artist_name}_pixiv', 'successful_download.json')):
            self.existing_images = json_to_dict(os.path.join(save_dir, f"{self.artist_name}_pixiv"), 'successful_download.json')
            save_dir = os.path.join(save_dir, f"{self.artist_name}_pixiv")
            backup = True
        else:
            save_dir = gen.make_directory(save_dir, self.artist_name + '_pixiv')
            backup = False

        gen.save_dir_global.update(save_dir)

        artwork_ids = self.artist_artwork_id_list(self.artist_id)
        image_counter.max = len(artwork_ids)
        threads = cpu_count() * self.arguments.threads
        pool = ThreadPool(threads)
        pool.map(partial(self.download_artwork, save_dir, check_existing=backup), artwork_ids)
        pool.close()
        pool.join()
        print(f'Time to Download: {time.strftime("%H:%M:%S", time.gmtime(int(time.time() - starting_time)))}')
