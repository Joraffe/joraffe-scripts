#! /usr/bin/env humblepy
import argparse
import copy
import csv
import math
import os
import urllib

from libraries.aetycoon.prettydata import prettify
from libraries.cdn import signurl
from mutagen.mp3 import MP3
from unidecode import unidecode

parser = argparse.ArgumentParser(
  description='Pulls data from SOTB to generate .py file mass edit/create \
  DisplayItems via Model Importer',
)
parser.add_argument(
  '-b',
  '--bundle',
  help='The machinename of the bundle that will be using all of the \
  DisplayItems edited by this script. This is also the name of the .py \
  file created with the prettified DisplayItem list.',
)
parser.add_argument(
  '-c',
  '--csvfile',
  help='Csv file containing all info on DisplayItems from the SOTB',
)
parser.add_argument(
  '-e',
  '--export',
  help='Python file with existing DisplayItem info from Model Exporter',
)
args = parser.parse_args()

displayitem_template = {
  'machine_name': 'placeholder',
  'struct': {
    'bundle': {
      'box-art-human-name': 'name_placeholder',
      'content': {
        'game': {}
      },
      'description-text': 'description_placeholder',
      'developers': [
        {
          'developer-name': 'dev_placeholder',
          'developer-url': 'dev_url',
        }
      ],
      'human-name': 'name_placeholder',
      'image_extra': {
        'link': 'pdfs/placholder_preview.pdf',
        'overlay': {
          'size': 'size_placeholder',
          'type': 'PDF',
        }
      },
      'preview-image': 'images/popups/placeholder_slideout.jpg',
      'publishers': [
        {
          'publisher-name': 'pub_placeholder',
          'publisher-url': 'pub_url',
        }
      ],
      'front-page-art': 'images/displayitems/placeholder.png',
      'front-page-subtitle': 'callout_placeholder',
      'soundtrack-listing': [],
      'slideshow-background': 'images/bg/placeholder_background.jpg',
      'unavailable-platforms': {},
      'youtube-link': 'video_placeholder',
    },
    'default': {},
  }
}


def pretty_filesize(size):
  """
  This is a helper function for add_new_displayitem_info() and
  edit_existing_displayitem_info() to transform filesize from an int or long
  to a formatted string with a human readable filesize.

  Args:
    size (int/long): The size of a file in bytes

  Examples:
    >> pretty_filesize(100000000)
    '95.37 MB'
    >> pretty_filesize(20000000000)
    '18.63 GB'
  """
  if (size == 0):
    return '0B'
  size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB',)
  i = int(math.floor(math.log(int(size), 1024)))
  p = math.pow(1024, i)
  s = round(int(size) / p, 2)
  return '%s %s' % (s, size_name[i])


def remove_non_ascii(text):
  """
  This is a helper function for add_new_displayitem_info() and
  edit_existing_displayitem_info() to transform unicode text to their closest
  plain-formatted text equivalent for any text-related fields, most notably:
  - description-text
  - human-name
  - box-art-human-name
  - front-page-subtitle

  Args:
    text (str): A String that may or may not have Unicode (UTF-8) characters

  Returns:
    A String without any Unicode (UTF-8 characters) that the Model Importer
    can process.
  """
  return unidecode(unicode(text, encoding="utf-8"))


def platform_icon_handler(displayitem, csv_info):
  """
  This is a helper function for add_new_displayitem_info() and
  edit_existing_displayitem_info() to handle Platform Icons for
  each DisplayItem. There are 3 cases:
  1) For new DisplayItems (or non-store, non-rebundle DisplayItems)
  2) For DisplayItems that exist in the Humble Store
  3) For DisplayItems that have been bundled before

  Args:
    displayitem    (dict):     A new or an existing DisplayItem dictionary
    csv_info (DictReader):     A single DictReader object from the csv_info
                               list generated from the .csv file form the SOTB
  """
  bundle = displayitem['struct']['bundle']
  temp_plats = {
    'windows': csv_info['windows'],
    'mac': csv_info['mac'],
    'linux': csv_info['linux'],
    'ps3': csv_info['ps3-bool'],
    'ps4': csv_info['ps4-bool'],
  }
  temp_drm = {
    'steam': csv_info['steam-bool'],
    'download': csv_info['drmfree-bool'],
    'other-key': csv_info['other-key-bool'],
    'ps3': csv_info['ps3-bool'],
    'ps4': csv_info['ps4-bool'],
  }
  if csv_info['rebundle-bool'] == '0' and csv_info['store-bool'] == '0' and csv_info['pdf-preview-bool'] == '0':
    for drm in temp_drm:
      if temp_drm[drm] == '1':
        bundle['content']['game'][drm] = [plat for plat in temp_plats if temp_plats[plat] == '1']
        bundle['unavailable-platforms'][drm] = [unplat for unplat in temp_plats if temp_plats[unplat] == '0']
        if bundle['unavailable-platforms'][drm] == []:
          del bundle['unavailable-platforms'][drm]
    if bundle['unavailable-platforms'] == {}:
      del bundle['unavailable-platforms']
    if csv_info['android-bool'] == '1':
      bundle['content']['mobile'] = {}
      bundle['content']['mobile']['android'] = ['android']
    if 'game' in bundle['content']:
      if bundle['content']['game'] == {}:
        del bundle['content']['game']

  elif csv_info['store-bool'] == '1':
    bundle['unavailable-platforms'] = {}
    for drm in temp_drm:
      if temp_drm[drm] == '1':
        bundle['unavailable-platforms'][drm] = [unplat for unplat in temp_plats if temp_plats[unplat] == '0']
        if bundle['unavailable-platforms'][drm] == []:
          del bundle['unavailable-platforms'][drm]
    if bundle['unavailable-platforms'] == {}:
      del bundle['unavailable-platforms']
    if csv_info['android-bool'] == '1':
      bundle['content'] = {}
      bundle['content']['mobile'] = {}
      bundle['content']['mobile']['android'] = ['android']
    if csv_info['ps3-bool'] == '1' or csv_info['ps4-bool'] == '1':
      bundle['content'] = {
        'game': {}
      }
    if 'game' in bundle['content']:
      if bundle['content']['game'] == {}:
        del bundle['content']['game']

  elif csv_info['rebundle-bool'] == '1' and csv_info['pdf-preview-bool'] == '0':
    rebundle_plats = {'content': {'game': {}}}
    for drm in temp_drm:
      if temp_drm[drm] == '1':
        rebundle_plats['content']['game'][drm] = [plat for plat in temp_plats if temp_plats[plat] != '1']
    if csv_info['android-bool'] == '1':
      rebundle_plats['content']['mobile'] = {}
      rebundle_plats['content']['mobile']['android'] = ['android']
    if rebundle_plats['content']['game'] == {}:
      del rebundle_plats['content']['game']
    if rebundle_plats['content'] != displayitem['struct']['default']['content']:
      displayitem['struct'][args.bundle] = {}
      displayitem['struct'][args.bundle]['content'] = rebundle_plats['content']


def prepare_displayitem_list(csv_info, existing_displayitems, displayitems):
  """
  This function prepares a list of DisplayItem dictionaries as a combination
  of templated DisplayItems (deep copies of displayitem_template) and the
  DisplayItems from the list existing_displayitems. It determines what to add
  (new or existing) based on the info from csv_info.

  Args:
    csv_info        (DictReader):     A list of DictReader objects, created from
                                      the .csv file generated from the SOTB
    existing_displayitems (list):     The list of existing DisplayItem dict
                                      imported from the Model Importer (can
                                      be an empty list if there are only new
                                      DisplayItems)
    displayitems          (list):     The ordered/combined list of DisplayItem
                                      dictionaries on which to run
                                      add_new_displayitem_info() and/or
                                      edit_existing_displayitem_info()
  Returns:
    This function returns a prepared list of DisplayItem dictionaries
    (displayitems)
  """
  existing_displayitems_index = 0
  for row in csv_info:
    if (row['store-bool'] == '0' and
      row['rebundle-bool'] == '0' and
      row['exists-bool'] == '0'):
        displayitems.append(copy.deepcopy(displayitem_template))
    else:
      displayitems.append(existing_displayitems[existing_displayitems_index])
      existing_displayitems_index += 1
  return displayitems


def write_pretty_displayitems_to_file(displayitems, filename):
  """
  This function takes in the list of DisplayItems (with all of the information
  from the SOTB applied to each DisplayItem in the list as necessary) and
  writes it to a new Python file for use in the Model Importer. The file is
  created in the Desktop by default.

  Args:
    displayitems (list): The list of DisplayItems (with SOTB info)
    filename      (str): The name of file to be created (for purposes of
                         this script, it will be args.bundle)
  """
  script_directory = os.path.normpath(__file__)
  script_directory_path_list = script_directory.split(os.sep)
  output_directory = '/%s/%s/Desktop/' % (script_directory_path_list[1], script_directory_path_list[2])
  with open(os.path.join(output_directory, '%s.py' % filename), 'wb') as f:
    f.write('[')
    for di in displayitems:
      f.write(''.join(prettify(di)))
      f.write('\n,\n')
    f.write(']')


def add_new_displayitem_info(new_displayitem, csv_info):
  """
  This function extracts all of the relevant DisplayItem information from a
  single item in the list of csv_info (which was created from the .csv file
  from the SOTB) and then adds/replaces the templated information in
  new_displayitem.

  Args:
    new_displayitem (dict): A templated DisplayItem dictionary
    csv_info  (DictReader): A single DictReader object from the csv_info list
                            generated from the .csv file form the SOTB
  """
  new_displayitem['machine_name'] = csv_info['machine-name']
  new_displayitem['struct']['default']['human-name'] = remove_non_ascii(csv_info['human-names'])
  bundle = new_displayitem['struct']['bundle']
  bundle['box-art-human-name'] = remove_non_ascii(csv_info['human-names'])
  bundle['front-page-art'] = 'images/displayitems/%s.png' % csv_info['machine-name']

  if csv_info['front-page-subtitle'] != '0':
    bundle['front-page-subtitle'] = remove_non_ascii(csv_info['front-page-subtitle'])
  if csv_info['background-image-bool'] == '1':
    bundle['slideshow-background'] = 'images/bg/%s_background.jpg' % csv_info['machine-name']
  if csv_info['slideout-image-bool'] == '1':
    bundle['preview-image'] = 'images/popups/%s_slideout.jpg' % csv_info['machine-name']

  if csv_info['description'] != '0':
    bundle['description-text'] = remove_non_ascii(csv_info['description'])

  if csv_info['developer-name'] != '0':
    if csv_info['developer-url'] == '0':
      bundle['developers'] = [{
        'developer-name': csv_info['developer-name']
      }]
    else:
      bundle['developers'] = [{
        'developer-name': csv_info['developer-name'],
        'developer-url': csv_info['developer-url']
      }]
  if csv_info['publisher-name'] != '0':
    if csv_info['publisher-url'] == '0':
      bundle['publishers'] = [{
        'publisher-name': csv_info['publisher-name']
      }]
    else:
      bundle['publishers'] = [{
        'publisher-name': csv_info['publisher-name'],
        'publisher-url': csv_info['publisher-url']
      }]

  platform_icon_handler(new_displayitem, csv_info)

  if csv_info['youtube-link'] != '0':
    bundle['youtube-link'] = csv_info['youtube-link']

  if csv_info['pdf-preview-bool'] == '1':
    url = signurl('ops/pdfs/%s_preview.pdf' % csv_info['machine-name'])
    metadata = urllib.urlopen(url)
    filesize = metadata.headers['content-length']
    bundle['image_extra'] = {
      'link': 'ops/pdfs/%s_preview.pdf' % csv_info['machine-name'],
      'overlay': {
        'size': pretty_filesize(filesize),
        'type': 'PDF'
       }
    }

  if csv_info['audio-bool'] == '1':
    bundle['soundtrack-hide-tracklist'] = True
    url = signurl('ops/audio/%s_preview.mp3' % csv_info['machine-name'])
    filename, headers = urllib.urlretrieve(url)
    audiofile = MP3(filename)
    bundle['soundtrack-listing'] = [
      {
        'preview-length': str(int(math.ceil(audiofile.info.length))),
        'preview-url': 'ops/audio/%s_preview.mp3' % csv_info['machine-name'],
        'track-name': 'Excerpt',
        'track-number': '1'
      }
    ]
  for key in bundle.keys():
    if bundle[key] == displayitem_template['struct']['bundle'][key]:
      del bundle[key]


def edit_existing_displayitem_info(existing_displayitem, csv_info):
  """
  This function extracts all of the relevant DisplayItem information from a
  single item in the list of csv_info (which was created from the .csv file
  from the SOTB) and then adds/replaces existing information in
  existing_displayitem. There are 3 types of existing_displayitem:
  1) DisplayItems from the Humble Store (represented by 'store-bool')
  2) DisplayItems from previous Bundles (represented by 'rebundle-bool')
  3) DisplayItems that exist but don't belong to Humble Store/previous bundles
     (most often a DispalyItem created for only a Humble Widget)

  Args:
    existing_displayitem (dict): An existing DisplayItem dictionary
    csv_info       (DictReader): A single DictReader object from the csv_info
                                 list generated from the .csv file form the SOTB
  """
  bundle = existing_displayitem['struct']['bundle']
  platform_icon_handler(existing_displayitem, csv_info)

  if csv_info['rebundle-bool'] == '1':
    struct = existing_displayitem['struct']
    struct[args.bundle]['front-page-art'] = 'images/displayitems/%s_%s.png' % (csv_info['machine-name'], args.bundle)
    if csv_info['background-image-bool'] == '1':
      struct[args.bundle]['slideshow-background'] = 'images/bg/%s_%s_background.jpg' % (csv_info['machine-name'], args.bundle)
    if csv_info['front-page-subtitle'] != '0':
      struct[args.bundle]['front-page-subtitle'] = remove_non_ascii(csv_info['front-page-subtitle'])
    if csv_info['description'] != '0':
      struct[args.bundle]['description-text'] = remove_non_ascii(csv_info['description'])
    if 'youtube-link' in existing_displayitem['struct']['default']:
      if csv_info['youtube-link'] != existing_displayitem['struct']['default']['youtube-link']:
        struct[args.bundle]['youtube-link'] = csv_info['youtube-link']
    elif 'youtube-link' in existing_displayitem['struct']['bundle']:
      if csv_info['youtube-link'] != existing_displayitem['struct']['bundle']['youtube-link']:
        struct[args.bundle]['youtube-link'] = csv_info['youtube-link']

  elif csv_info['store-bool'] == '1':
    bundle['box-art-human-name'] = remove_non_ascii(csv_info['human-names'])
    bundle['front-page-art'] = 'images/displayitems/%s.png' % csv_info['machine-name']
    if csv_info['front-page-subtitle'] != '0':
      bundle['front-page-subtitle'] = remove_non_ascii(csv_info['front-page-subtitle'])
    if csv_info['background-image-bool'] == '1':
      bundle['slideshow-background'] = 'images/bg/%s_background.jpg' % csv_info['machine-name']
    if csv_info['description'] != '0':
      bundle['description-text'] = remove_non_ascii(csv_info['description'])
    if 'youtube-link' in existing_displayitem['struct']['default']:
      if csv_info['youtube-link'] != existing_displayitem['struct']['default']['youtube-link']:
        bundle['youtube-link'] = csv_info['youtube-link']
    elif 'youtube-link' in existing_displayitem['struct']['storefront']:
        if csv_info['youtube-link'] != existing_displayitem['struct']['storefront']['youtube-link']:
          bundle['youtube-link'] = csv_info['youtube-link']

  elif csv_info['exists-bool'] == '1':
    bundle = copy.deepcopy(displayitem_template['struct']['bundle'])
    add_new_displayitem_info(existing_displayitem, csv_info)


if __name__ == '__main__':
  csv_info = []
  existing_displayitems = []
  displayitems = []

  with open(args.csvfile) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      csv_info.append(row)

  if args.export:
     with open(args.export) as f:
      exec('existing_displayitems = ' + f.read())

  displayitems = prepare_displayitem_list(csv_info, existing_displayitems, displayitems)

  for di, c in zip(displayitems, csv_info):
    if (c['rebundle-bool'] == '1' or
      c['store-bool'] == '1' or
      c['exists-bool'] == '1'):
        edit_existing_displayitem_info(di, c)
    else:
      add_new_displayitem_info(di, c)

  write_pretty_displayitems_to_file(displayitems, args.bundle)
