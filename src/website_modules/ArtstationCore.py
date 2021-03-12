import requests
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
from src.utils.txtDatabaseHandling import json_to_dict
from src.utils.general import image_counter, successful_download_dict, print_Queue, Request


class ArtstationCore:
    def __init__(self, arguments):
        self.request = Request(backoff_factor=0.3)
        self.arguments = arguments
        self.artist_url = self.arguments.url
        if self.artist_url[-1] != '/':
            self.artist_url += '/'
        self.artist_id = re.search(r"(?<=.com/).[a-zA-Z0-9-_]*", self.artist_url).group()

    def artist_artworks_list(self):
        url = f'https://www.artstation.com/users/{self.artist_id}/projects.json?'
        page_count = 1
        image_count = 0
        artwork_list = []
        while True:
            print_Queue.put("Getting Image Links (Don't Panic)")
            params = {
                'page': page_count
            }

            res = self.request.get(url, params=params).json()
            total_count = res['total_count']
            image_count += len(res['data'])
            for data in res['data']:
                artwork_list.append(data)
            page_count += 1
            if total_count == image_count:
                break
        return artwork_list

    def extended_artwork_fetch(self, artwork):
        hash_id = artwork['hash_id']
        url = f"https://www.artstation.com/projects/{hash_id}.json"
        res = self.request.get(url).json()
        return res

    def find_download_url(self, extended_artwork_fetch):
        url_list = []
        assets_length = len(extended_artwork_fetch['assets'])
        loop_var = 0
        while loop_var < assets_length:
            if extended_artwork_fetch['assets'][loop_var]['asset_type'] == 'image':
                url = extended_artwork_fetch['assets'][loop_var]['image_url']
                url_list.append(url)
            loop_var += 1
        return url_list

    def ext_finder(self, url):
        ext = re.search(r'.\w+(?=\?)', url).group()
        return ext

    def download_artwork(self, save_dir, url, title):
        ext = self.ext_finder(url)
        # Image_counter.increments() ads +1 to the class member "val" and returns val after the increment
        print_Queue.put(f"Currently Downloading: {title} ({str(image_counter.increment())}/{str(image_counter.max)})")
        _4k_url = re.sub(r"large", "4k", url)
        # 4k Check
        try:
            r_stream = self.request.get(_4k_url, stream=True)
        except requests.exceptions.HTTPError:
            r_stream = self.request.get(url, stream=True)
        path_with_name = os.path.join(save_dir, title + f"_by_{self.artist_id}" + ext)
        img_number = random.randint(0, 1000)
        if os.path.exists(path_with_name):
            path_with_name = os.path.join(save_dir, title + f"_by_{self.artist_id}_{img_number}" + ext)
        with open(path_with_name, "wb") as file:
            try:
                for chunk in r_stream:
                    file.write(chunk)
            except Exception as e:
                print_Queue.put(f"{title}")
                print_Queue.put(f"Error {e}")

    def multi_assets_download(self, save_dir, artwork, check_existing):
        # Already downloaded images Check
        current_info = {
            'id': artwork['hash_id'],
            'isDownloaded': True
        }

        if check_existing:
            if gen.check_existing_images(self.existing_images, artwork['hash_id']):
                image_counter.val += 1
                successful_download_dict.append(current_info)
                print_Queue.put(f"Title: {artwork['title']}, Link: {artwork['permalink']} is already present.")
                return

        artwork_extended_fetch = self.extended_artwork_fetch(artwork)
        title = gen.make_windows_legal(artwork_extended_fetch['title'])
        url_list = self.find_download_url(artwork_extended_fetch)
        image_counter.max = image_counter.max + len(url_list) - 1
        for url in url_list:
            self.download_artwork(save_dir=save_dir, url=url, title=title)
        successful_download_dict.append(current_info)

    def save_artwork(self):
        save_dir = self.arguments.save_location
        starting_time = time.time()
        # Checks if the download folder already exists
        if os.path.exists(os.path.join(save_dir, f'{self.artist_id}_artstation', 'successful_download.json')):
            self.existing_images = json_to_dict(os.path.join(save_dir, f"{self.artist_id}_artstation"),
                                                'successful_download.json')
            save_dir = os.path.join(save_dir, f"{self.artist_id}_artstation")
            backup = True
        else:
            save_dir = gen.make_directory(save_dir, self.artist_id + '_artstation')
            backup = False

        gen.save_dir_global.update(save_dir)

        artworks = self.artist_artworks_list()
        image_counter.max = len(artworks)
        threads = cpu_count() * self.arguments.threads
        pool = ThreadPool(threads)
        pool.map(partial(self.multi_assets_download, save_dir, check_existing=backup), artworks)
        pool.close()
        pool.join()
        print_Queue.put(f'Time to Download: {time.strftime("%H:%M:%S", time.gmtime(int(time.time() - starting_time)))}')
