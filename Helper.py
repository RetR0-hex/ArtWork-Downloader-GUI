import re
import os
from src.utils import general as gen
from src.utils.general import print_Queue
from src.website_modules.ArtstationCore import ArtstationCore
from src.website_modules.DeviantArtCore import DeviantArtCore
from src.website_modules.PixivCore import PixivCore


def main_function(arguments):

    gen.intro()

    # getting root dir
    root_dir = os.path.dirname(os.path.abspath(__file__))

    match = re.search(r"(?!www.)(\w+)(?=.com|.net)", arguments.url).group()

    if match == 'artstation':
        api = ArtstationCore(arguments)
        api.save_artwork()

    elif match == 'deviantart':
        api = DeviantArtCore(arguments)
        api.save_artwork()

    elif match == 'pixiv':
        api = PixivCore(arguments)
        api.save_artwork()

    else:
        print_Queue.put("Please enter a valid ArtStation, Deviantart or Pixiv artist link.")
        exit(0)
