import requests
from html import unescape
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import random
import os
import re
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count
from src.utils import general as gen
from src.utils.txtDatabaseHandling import json_to_dict, dict_to_json
from src.utils.general import image_counter, successful_download_dict


class DeviantArtCore:
    def __init__(self, arguments):
        self.request_session = requests.Session()
        self.request_session.cookies['agegate_state'] = '1'
        self.is_user_logged_in = False
        self.arguments = arguments
        self.artist_url = self.arguments.url
        self.retry = Retry(total=10, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        self.request_session.mount('http://', HTTPAdapter(max_retries=self.retry))
        self.request_session.mount('https://', HTTPAdapter(max_retries=self.retry))
        if self.artist_url[-1] != '/':
            self.artist_url = self.artist_url + '/'
        self.artist_id = re.search(r"(?<=.com/)[0-9a-zA-Z-]*", self.artist_url).group()

        if self.arguments.username:
            self.chrome = gen.WebDriverChrome()
            self.cookies_load()
            self.is_user_logged_in = True
        else:
            # Checks if cookies exists or not, if they do.. they are loaded into request's session
            if os.path.exists(os.path.join('cookies', "cookies_deviant.json")):
                print("Reloading Existing cookies....")
                json_cookies = json_to_dict('cookies', "cookies_deviant.json")
                if not gen.cookies_expiry_check(json_cookies):
                    self.set_cookies_request(json_cookies)
                    self.is_user_logged_in = True


    def cookies_load(self, recursion=False):
        if os.path.exists(os.path.join('cookies', "cookies_deviant.json")):
            if not recursion:
                print("Reloading Existing cookies....")
            json_cookies = json_to_dict('cookies', "cookies_deviant.json")
            if not gen.cookies_expiry_check(json_cookies):
                self.set_cookies_request(json_cookies)
            else:
                self.save_cookies()
        else:
            print("Didn't find existing cookies, generating new ones.....")
            self.save_cookies()

    def save_cookies(self):
        if os.path.exists('cookies'):
            result = self.auto_login()
            cookies = self.cookies_cleaner(result)
            dict_to_json(cookies, 'cookies', 'cookies_deviant.json')
            self.cookies_load(recursion=True)
        else:
            os.mkdir('cookies')
            self.save_cookies()

    def cookies_cleaner(self, cookies):
        keep_data_list = ['td', 'userinfo', 'auth_secure', 'auth', 'vd']
        return_cookies = []
        for data in keep_data_list:
            try:
                return_cookies.append(next(x for x in cookies if x["name"] == data))
            except StopIteration:
                pass
        return return_cookies

    def cookies_verifier(self, artwork_list):
        for artwork in artwork_list:
            if artwork['isDownloadable']:
                try:
                    html = unescape(self.request(artwork['url']).text)
                    url = re.search(r'(?!href=")https://www.deviantart.com/download/.+?(?=")', html).group()
                    return False
                except AttributeError:
                    return True
        return False

    def set_cookies_request(self, json_cookies):
        for cookie in json_cookies:
            name = cookie['name']
            value = cookie['value']
            self.request_session.cookies[name] = str(value)

    def auto_login(self):
        self.chrome.set_driver()
        self.chrome.set_windows_size(1000, 1000)
        retry_url = 'https://www.deviantart.com/_sisu/do/signin'
        login_url = 'https://www.deviantart.com/users/login'
        self.chrome.driver.get(login_url)
        self.chrome.driver.find_element_by_id('username').send_keys(self.arguments.username)
        self.chrome.driver.find_element_by_id('password').send_keys(self.arguments.password)
        # self.chrome.driver.find_element_by_id('loginbutton').click()
        while True:
            current_url = self.chrome.driver.current_url
            if (current_url != retry_url) and (current_url != login_url):
                break
            else:
                time.sleep(2)
        cookies = self.chrome.driver.get_cookies()
        cookies = self.cookies_cleaner(cookies)
        self.chrome.driver.close()
        return cookies

    def request(self, url, **kwargs):
        result = self.request_session.get(url, **kwargs)
        result.raise_for_status()
        return result

    def request_without_cookies(self, url, **kwargs):
        request_session_without_cookie = requests.Session()
        request_session_without_cookie.cookies['agegate_state'] = '1'
        request_session_without_cookie.mount('http://', HTTPAdapter(max_retries=self.retry))
        request_session_without_cookie.mount('https://', HTTPAdapter(max_retries=self.retry))
        result = request_session_without_cookie.get(url, **kwargs)
        result.raise_for_status()
        return result

    def extended_fetch_artwork(self, artwork):
        url = 'https://www.deviantart.com/_napi/shared_api/deviation/extended_fetch?'
        params = {
            'deviationid': artwork['deviationId'],
            'username': self.artist_id,
            'type': 'art'
        }
        extended_fetch = self.request(url, params=params).json()
        time.sleep(2)
        return extended_fetch['deviation']

    def artist_artworks_list(self):
        url = 'https://www.deviantart.com/_napi/da-user-profile/api/gallery/contents?'
        artwork_list_dict = []
        offset = 0
        while True:
            print("Getting image links (Don't Panic)")
            params = {
                'username': self.artist_id,
                'offset': str(offset),
                'limit': '24',
                'all_folder': 'true',
                'mode': 'newest'
            }
            json_data = self.request(url, params=params).json()
            for data in json_data['results']:
                artwork_list_dict.append(data['deviation'])
            if not json_data['hasMore']:
                break
            offset += 24
        return artwork_list_dict

    # Might remove this in the future because it causes a temp ban after 120-150 image downloads
    def downloadable_artwork_url(self, a_extend):
        # Original Quality so login is preferred
        html = unescape(self.request(a_extend['url']).text)
        # "?=" 	lookahead assertion: matches without consuming
        url = re.search(r'(?!href=")https://www.deviantart.com/download/.+?(?=")', html).group()
        return url

    def undownloadable_artwork_url(self, a_extend, ext, retry):
        w = a_extend['extended']['originalFile']['width']
        h = a_extend['extended']['originalFile']['height']
        base_url = a_extend['media']['baseUri']
        try:
            token = next(item for item in a_extend['media']['token'])
        except KeyError:
            pass
        try:
            pretty_name = a_extend['media']['prettyName']
        except KeyError:
            base_url = next(item for item in a_extend['media']['types'] if item['t'] == 'gif')
            base_url = base_url["b"]
            return base_url + '?token=' + token
        image_parameter = next(item for item in a_extend['media']['types'] if item['t'] == 'fullview')

        if retry == 0:
            # Highest Quality (Doesn't work on new uploads)
            url = base_url + f'/v1/fill/w_{w},h_{h},q_100/' + pretty_name + ext
            pat0_url = re.sub('/f/', '/intermediary/f/', url)
            return pat0_url

        elif retry == 1:
            # vanilla url with image parameters removed (Second Highest) (Sometime works, Sometime doesn't)
            try:
                pat1_url = base_url + '?token=' + token
            except UnboundLocalError:
                pat1_url = base_url
            return pat1_url

        elif retry == 2:
            # Trying highest quality with token (Highest quality but usually fails if retry#0 fails)
            url = base_url + f'/v1/fill/w_{w},h_{h},q_100/' + pretty_name + ext
            url = re.sub('/f/', '/intermediary/f/', url)
            pat2_url = url + '?token=' + token
            return pat2_url

        elif retry == 3:
            # Just changing the Quality with default height and width (Will work most of the time)
            w = image_parameter['w']
            h = image_parameter['h']
            image_parameter = f'v1/fill/w_{w},h_{h},q_100/{pretty_name}-fullview' + ext
            pat3_url = base_url + f'/{image_parameter}' + '?token=' + token
            return pat3_url

        elif retry == 4:
            # Vanilla fullView url with intermediary regexed (least quality)
            w = image_parameter['w']
            h = image_parameter['h']
            image_parameter = f'v1/fill/w_{w},h_{h},q_75/{pretty_name}-fullview' + ext
            url = base_url + f'/{image_parameter}' + '?token=' + token
            pat4_url = re.sub(r'(?!,)(q_\d+)', 'q_100', re.sub('/f/', '/intermediary/f/', url))
            return pat4_url

        else:
            # Trying without intermediary with token and image parameters (sometimes work least quality)
            url = base_url + f'/v1/fill/w_{w},h_{h},q_100/' + pretty_name + ext
            pat5_url = url + '?token=' + token
            return pat5_url

    def find_download_url(self, a_extend, ext, retry):
        if (a_extend['isDownloadable']) and self.is_user_logged_in:
            try:
                return self.downloadable_artwork_url(a_extend)
            except requests.exceptions.HTTPError:
                print("Banned, Will retry in 5 minutes -_-")
                time.sleep(300)
                self.find_download_url(a_extend, ext, retry)
            except AttributeError:
                return self.undownloadable_artwork_url(a_extend, ext, retry)
        else:
            return self.undownloadable_artwork_url(a_extend, ext, retry)

    def download_image(self, save_dir, artwork, check_existing):
        # Copy these to other download classes later
        current_info = {
                    'id': artwork['deviationId'],
                    'isDownloaded': True
                     }

        # Checks if images are already downloaded
        if check_existing:
            if gen.check_existing_images(self.existing_images, artwork['deviationId']):
                print(f"Title: {artwork['title']}, Link: {artwork['url']} is already present.")
                image_counter.val += 1
                successful_download_dict.append(current_info)
                return

        #  new shit added to deviantArt, I have no way to bypass this as of now, so the only solution is login
        if 'premiumFolderData' in artwork:
            if not artwork['premiumFolderData']['hasAccess']:
                print(f"Don't have watching access for image Title: {artwork['title']}, Link: {artwork['url']},"
                      f"\nPlease watch the artist and then login to re-download these images.")
                image_counter.val += 1
                return

        artwork_extended_fetch = self.extended_fetch_artwork(artwork)
        title = gen.make_windows_legal(artwork_extended_fetch['title'])
        ext = gen.ext_finder(artwork_extended_fetch['media']['baseUri'])

        # Image_counter.increments() ads +1 to the class member "val" and returns val after the increment
        print(f"Currently Downloading: {title} ({str(image_counter.increment())}/{str(image_counter.max)})")
        retry = 0
        if artwork_extended_fetch['isDownloadable'] and self.is_user_logged_in:
            url = self.find_download_url(artwork_extended_fetch, ext, retry)
            r_stream = self.request(url, stream=True)
        else:
            while retry <= 5:
                    try:
                        url = self.find_download_url(artwork_extended_fetch, ext, retry)
                        r_stream = self.request_without_cookies(url, stream=True)
                        break
                    except requests.exceptions.HTTPError:
                        retry += 1
            # If my shitty url finder fails -_-
            if retry > 5:
                image_counter.val += 1
                return

        path_with_name = os.path.join(save_dir, title + f"_by_{self.artist_id}" + ext)
        img_number = random.randint(0, 1000)
        if os.path.exists(path_with_name):
            path_with_name = os.path.join(save_dir, title + f"_by_{self.artist_id}_{img_number}" + ext)
        with open(path_with_name, "wb") as file:
            try:
                for chunk in r_stream:
                    file.write(chunk)
            except Exception as e:
                print(f"{title}")
                print(f"Error {e}")

        successful_download_dict.append(current_info)

    def save_artwork(self):
        save_dir = self.arguments.save_location
        starting_time = time.time()
        artworks = self.artist_artworks_list()
        if self.cookies_verifier(artworks) and self.is_user_logged_in:
            self.save_cookies()
            self.save_artwork()

        # CHecks if the download folder already exists
        if os.path.exists(os.path.join(save_dir, f'{self.artist_id}_deviantart', 'successful_download.json')):
            self.existing_images = json_to_dict(os.path.join(save_dir, f"{self.artist_id}_deviantart"), 'successful_download.json')
            save_dir = os.path.join(save_dir, f"{self.artist_id}_deviantart")
            backup = True
        else:
            save_dir = gen.make_directory(save_dir, self.artist_id + '_deviantart')
            backup = False

        gen.save_dir_global.update(save_dir)

        # THIS WAS REFERENCE FROM GENEREAL IMAGE COUNTER SO THAT WE CAN KEEP TRACK
        # OF IMAGE COUNTS FROM THE GUI WINDOW
        image_counter.max = len(artworks)
        # Deviant ART bans you easily that's why one less thread
        if self.arguments.threads <= 1:
            threads = cpu_count() * 1
        else:
            threads = cpu_count() * (self.arguments.threads - 1)
        pool = ThreadPool(threads)
        pool.map(partial(self.download_image, save_dir, check_existing=backup), artworks)
        pool.close()
        pool.join()
        print(f'Time to Download: {time.strftime("%H:%M:%S", time.gmtime(int(time.time() - starting_time)))}')
