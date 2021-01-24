import requests
import time
import random
import os
import re
from html import unescape
from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count
from src.utils import general as gen
from src.utils.txtDatabaseHandling import json_to_dict, dict_to_json
from src.utils.general import image_counter, successful_download_dict, print_Queue, Request
import queue

# General Global REQUEST Instance
_request = Request(backoff_factor=0.5)

# Clear Global Request Instance
# This is the instance that will be called when you need to access something without cookies.
_clear_request = Request(backoff_factor=0.5)


class DeviantArtImage:

    # Contains all the properties related to deviantArt Images that are useful for this core
    # Also contains all the functions related except to this core images

    def __init__(self, artwork, isLoggedin, artist_id):
        self.artwork = artwork
        self.image_id = artwork['deviationId']
        self.artist_id = artist_id  # str.lower(artwork['author']['username'])
        self.image_name = gen.make_windows_legal(artwork['title'])
        self.image_url = artwork['url']
        self.extended_artwork = None
        self.downloadable_image_link = None
        self.ext = gen.ext_finder(artwork['media']['baseUri'])
        # self.extended_artwork = None
        self.image_download_links = queue.Queue(maxsize=0)

        # Image access bools
        self.isDownloadable = artwork['isDownloadable']
        self.isWatchOnly = True if 'premiumFolderData' in artwork else False
        self.hasWatchOnlyAccess = artwork['premiumFolderData']['hasAccess'] if self.isWatchOnly else False
        self.isUserLoggedIn = isLoggedin

    def extended_fetch_artwork(self, artwork):
        url = 'https://www.deviantart.com/_napi/shared_api/deviation/extended_fetch?'
        params = {
            'deviationid': artwork['deviationId'],
            'username': self.artist_id,
            'type': 'art'
        }
        extended_fetch = _request.get(url, headers={'user-agent': gen.random_useragent()}, params=params).json()
        print_Queue.put("extended_artwork fetch function delay")
        time.sleep(10)
        return extended_fetch['deviation']['extended']

    def get_downloadable_image_url(self):
        # # Original Quality so login is preferred
        # html = _request.get(self.image_url).text
        # # "?=" 	lookahead assertion: matches without consuming
        # with open('test.html', 'w') as file:
        #     file.writelines(html)
        # url = re.search(r'(?!href=")https://www.deviantart.com/download/.+?(?=")', html).group()
        # return url
        return self.extended_artwork['download']['url']

    def get_undownloadable_image_url(self):

        w_orig = self.extended_artwork['originalFile']['width']
        h_orig = self.extended_artwork['originalFile']['height']
        base_url = self.artwork['media']['baseUri']

        try:
            token = self.artwork['media']['token'][0]
        except KeyError:
            token = None

        # This to my knowledge only happens if either the image is reaaaaly old or it's a gif
        try:
            pretty_name = self.artwork['media']['prettyName']
        except KeyError:
            return

        image_parameter = next(item for item in self.artwork['media']['types'] if item['t'] == 'fullview')

        w_base = image_parameter['w']
        h_base = image_parameter['h']

        baseURL_intermediary = re.sub('/f/', '/intermediary/f/', base_url)

        # Highest Quality (Doesn't work on new uploads)

        # this turn -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png
        # to        -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/intermediary/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png/v1/fill/w_{w},h_{h},q_100/<preetyName>.ext

        pat0_url = baseURL_intermediary + f'/v1/fill/w_{w_orig},h_{h_orig},q_100/{pretty_name}' + self.ext
        self.image_download_links.put(pat0_url)

        self.image_download_links.put(base_url)

        if token is not None:
            # this turn -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png
            # to        -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png?token=tokenVal

            pat1_url = base_url + '?token=' + token
            self.image_download_links.put(pat1_url)

            # this turn -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png
            # to        -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/intermediary/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png/v1/fill/w_{w},h_{h},q_100/<preetyName>.ext?token=tokenVAL

            pat2_url = baseURL_intermediary + f'/v1/fill/w_{w_orig},h_{h_orig},q_100/{pretty_name}' + self.ext
            pat2_url = pat2_url + '?token=' + token
            self.image_download_links.put(pat2_url)

            # this turn -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png
            # to        -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png/v1/fill/w_{w},h_{h},q_100/<preetyName>-fullview.ext?token=tokenVal

            # Just changing the Quality with default height and width (Will work most of the time)']
            parameter = f'v1/fill/w_{w_base},h_{h_base},q_100/{pretty_name}-fullview' + self.ext
            pat3_url = base_url + f'/{parameter}' + '?token=' + token
            self.image_download_links.put(pat3_url)

            # this turn -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png
            # to        -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png/v1/fill/w_{w},h_{h},q_100/<preetyName>.ext?token=tokenVal

            pat4_url = base_url + f'/v1/fill/w_{w_base},h_{h_base},q_100/{pretty_name}' + self.ext
            pat4_url = pat4_url + '?token=' + token
            self.image_download_links.put(pat4_url)

            # this turn -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png
            # to        -> https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/intermediary/f/b39b78b1-0d8d-4f96-830f-2a58f0c69a5e/deb7ab5-a612a170-d853-4337-a4cc-ecea81463b57.png/v1/fill/w_{w},h_{h},q_100/<preetyName>-fullview.ext?token=tokenVal

            parameter = f'v1/fill/w_{w_base},h_{h_base},q_100/{pretty_name}-fullview' + self.ext
            pat5_url = baseURL_intermediary + f'/{parameter}' + '?token=' + token
            self.image_download_links.put(pat5_url)

    def generate_links(self):
        # Empty the queue in case of recursion
        while self.image_download_links.qsize() is not 0:
            self.image_download_links.get()

        if self.extended_artwork is None:
            self.extended_artwork = self.extended_fetch_artwork(self.artwork)

        # After Everything is done, generate the image links and save them to self.image_download_links queue
        if self.isDownloadable and self.isUserLoggedIn:
            self.downloadable_image_link = self.get_downloadable_image_url()

        self.get_undownloadable_image_url()


class DeviantArtImageDownloader:

    def __init__(self, deviant_image_instance, save_dir, do_image_already_exists, existing_images):
        self._deviant_image = deviant_image_instance
        self.do_image_already_exists = do_image_already_exists
        self.existing_images = existing_images
        self.path_w_image_name = self.generate_path_name(save_dir)
        self.current_info = {
            'id': self._deviant_image.image_id,
            'isDownloaded': True
        }

    def skip_image(self, postfix):
        print_Queue.put(f"ID: {self._deviant_image.image_id}\n"
                        f"Link: {self._deviant_image.image_url} {postfix}\n")
        self.successful_download()

    def successful_download(self):
        print_Queue.put(f"Successfully Downloaded: {self._deviant_image.image_name} "
                        f"({str(image_counter.increment())}/{str(image_counter.max)})")
        successful_download_dict.append(self.current_info)

    def get_downloadable_image_data(self):
        response = None
        try:
            response = _request.get(self._deviant_image.downloadable_image_link)
        except requests.exceptions.HTTPError:
            print_Queue.put("Banned, Will retry in 5 minutes -_-")
            print_Queue.put("get_downloadable_image_data fetch function delay")
            time.sleep(300)
            self.get_downloadable_image_data()
        return response

    def get_undownloadable_image_data(self):
        response = None
        while self._deviant_image.image_download_links.qsize() is not 0:
            try:
                response = _clear_request.get(self._deviant_image.image_download_links.get(),
                                              headers={'user-agent': gen.random_useragent()})
                break
            except requests.exceptions.HTTPError:
                pass
        return response

    def download_image(self):
        response = None

        if self.do_image_already_exists:
            if gen.check_existing_images(self.existing_images, self._deviant_image.image_id):
                self.skip_image("is already present")
                return response

        if self._deviant_image.isWatchOnly and not self._deviant_image.hasWatchOnlyAccess:
            self.skip_image("is a WatchOnly Image. \n"
                            "Please watch the artist and then login to re-download these images.")
            return response

        # Now that we have checked for existing images, we will call the generator function
        self._deviant_image.generate_links()

        if self._deviant_image.isDownloadable and self._deviant_image.isUserLoggedIn:
            response = self.get_downloadable_image_data()
            self.successful_download()
            return response

        # if images are not downloadable then we will call another function
        response = self.get_undownloadable_image_data()
        self.successful_download()
        # Giving a little breathing room to the deviantART API
        return response

    def save_image(self):
        response = self.download_image()
        if response is not None:
            with open(self.path_w_image_name, 'wb') as file:
                file.write(response.content)
            print_Queue.put("save_image fetch function delay")
            time.sleep(15)

    def generate_path_name(self, save_dir):
        path_w_name = os.path.join(save_dir, self._deviant_image.image_name
                                   + f"_by_{self._deviant_image.artist_id}"
                                   + self._deviant_image.ext)

        if os.path.exists(path_w_name):
            path_w_name = os.path.join(save_dir, self._deviant_image.image_name
                                       + f"_by_{self._deviant_image.artist_id}_{random.randint(1, 1000)}"
                                       + self._deviant_image.ext)

        return path_w_name


class DeviantArtCore:
    def __init__(self, arguments):
        self.is_user_logged_in = False
        self.existing_images = None
        self.arguments = arguments
        self.artist_url = self.arguments.url
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
                print_Queue.put("Reloading Existing cookies....")
                json_cookies = json_to_dict('cookies', "cookies_deviant.json")
                if not gen.cookies_expiry_check(json_cookies):
                    _request.add_cookies(json_cookies)
                    self.is_user_logged_in = True

    def cookies_load(self, recursion=False):
        if os.path.exists(os.path.join('cookies', "cookies_deviant.json")):
            if not recursion:
                print_Queue.put("Reloading Existing cookies....")
            json_cookies = json_to_dict('cookies', "cookies_deviant.json")
            if not gen.cookies_expiry_check(json_cookies):
                _request.add_cookies(json_cookies)
            else:
                self.save_cookies()
        else:
            print_Queue.put("Didn't find existing cookies, generating new ones.....")
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

    def artist_artworks_list(self):
        url = 'https://www.deviantart.com/_napi/da-user-profile/api/gallery/contents?'
        artwork_list_dict = []
        offset = 0
        while True:
            print_Queue.put("Getting image links (Don't Panic)")
            params = {
                'username': self.artist_id,
                'offset': str(offset),
                'limit': '24',
                'all_folder': 'true',
                'mode': 'newest'
            }
            json_data = _request.get(url, params=params).json()
            for data in json_data['results']:
                artwork_list_dict.append(data['deviation'])
            if not json_data['hasMore']:
                break
            offset += 24
        return artwork_list_dict

    def extractor(self, save_dir, artwork, check_existing):
        deviant_image = DeviantArtImage(artwork=artwork, isLoggedin=self.is_user_logged_in, artist_id=self.artist_id)
        deviant_image_download = DeviantArtImageDownloader(deviant_image_instance=deviant_image,
                                                           save_dir=save_dir, do_image_already_exists=check_existing,
                                                           existing_images=self.existing_images)
        deviant_image_download.save_image()

    def save_artwork(self):
        save_dir = self.arguments.save_location
        starting_time = time.time()
        artworks = self.artist_artworks_list()

        # CHecks if the download folder already exists
        if os.path.exists(os.path.join(save_dir, f'{self.artist_id}_deviantart', 'successful_download.json')):
            self.existing_images = json_to_dict(os.path.join(save_dir, f"{self.artist_id}_deviantart"),
                                                'successful_download.json')
            save_dir = os.path.join(save_dir, f"{self.artist_id}_deviantart")
            backup = True
        else:
            save_dir = gen.make_directory(save_dir, self.artist_id + '_deviantart')
            backup = False

        gen.save_dir_global.update(save_dir)

        # THIS WAS REFERENCE FROM GENERAL IMAGE COUNTER SO THAT WE CAN KEEP TRACK
        # OF IMAGE COUNTS FROM THE GUI WINDOW
        image_counter.max = len(artworks)
        # Deviant ART bans you easily that's why one less thread
        if self.arguments.threads <= 1:
            threads = cpu_count() * 1
        else:
            threads = cpu_count() * (self.arguments.threads - 1)
        pool = ThreadPool(threads)
        pool.map(partial(self.extractor, save_dir, check_existing=backup), artworks)
        pool.close()
        pool.join()
        print_Queue.put(f'Time to Download: {time.strftime("%H:%M:%S", time.gmtime(int(time.time() - starting_time)))}')
