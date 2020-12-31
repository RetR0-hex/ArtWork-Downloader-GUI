import os
import json


def write_links_to_file_list(locations_to_save ,image_list_obj, artist_name):
    image_list_with_name = []
    for img in image_list_obj:
        temp = str(img.name) + ", " + str(img.src) + "\n"
        image_list_with_name.append(temp)
    # UTF-8 encoding
    file = open(os.path.join(locations_to_save, artist_name + "_image_links.txt"), "w", encoding='utf-8')
    file.writelines(image_list_with_name)
    file.close()


def dict_to_json(_dict, save_dir, file_name):
    file = open(os.path.join(save_dir, file_name), "w", encoding='utf-8')
    json.dump(_dict, file, indent=4)


def json_to_dict(save_dir, file_name):
    file = open(os.path.join(save_dir, file_name), 'r', encoding='utf-8')
    _dict = json.load(file)
    return _dict

