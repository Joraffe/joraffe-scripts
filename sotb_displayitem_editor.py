#! /usr/bin/env humblepy
import argparse
import csv
import math
import urllib

from libraries.aetycoon.prettydata import prettify
from libraries.cdn import signurl
from mutagen.mp3 import MP3

parser = argparse.ArgumentParser(
  description='Pulls data from SOTB to generate .py file mass edit/create \
  DisplayItems via Model Importer')
parser.add_argument(
  '-b',
  '--bundle',
  help='The machinename of the bundle that will be using all of the \
  DisplayItems edited by this script. Only applicable if there are \
  rebundled DisplayItems.')
parser.add_argument(
  '-c',
  '--csvfile',
  help='Csv file containing all info on DisplayItems from the SOTB')
parser.add_argument(
  '-e',
  '--export',
  help='Python file with existing DisplayItem info from Model Exporter.')
args = parser.parse_args()

bundle_template = {
  'box-art-human-name': 'name_placeholder',
  'content': {'game': {}},
  'description-text': 'description_placeholder',
  'developers': [{'developer-name': 'dev_placeholder', 'developer-url': 'dev_url'}],
  'human-name': 'name_placeholder',
  'image_extra': {'link': 'pdfs/placholder_preview.pdf', 'overlay': {'size': 'size_placeholder', 'type': 'PDF'}},
  'preview-image': 'images/popups/placeholder_slideout.jpg',
  'publishers': [{'publisher-name': 'pub_placeholder', 'publisher-url': 'pub_url'}],
  'front-page-art': 'images/displayitems/placeholder.png',
  'front-page-subtitle': 'callout_placeholder',
  'soundtrack-listing': [],
  'slideshow-background': 'images/bg/placeholder_background.jpg',
  'unavailable-platforms': {},
  'youtube-link': 'video_placeholder',
}

displayitem_template = {
  'machine_name': 'placeholder',
  'struct': {
    'bundle': bundle_template,
    'default': {},
  }
}


def prepare_displayitem_list(csvinfo, exportedinfo, displayitems):
  exportedinfo_index = 0
  for csv_di in csvinfo:
    if (csv_di['store-bool'] == '0' and
      csv_di['rebundle-bool'] == '0' and
      csv_di['exists-bool'] == '0'):
        displayitems.append(displayitem_template)
    else:
      displayitems.append(exportedinfo[exportedinfo_index])
      exportedinfo_index += 1
  return displayitems


def platform_icon_handler(temp_di, csv_di):
  bundle = temp_di['struct']['bundle']
  plat_icon_template = {
    'windows': '1',
    'mac': '1',
    'linux': '1',
  }
  temp_plats = {
    'windows': csv_di['windows'],
    'mac': csv_di['mac'],
    'linux': csv_di['linux'],
  }
  temp_drm = {
    'steam': csv_di['steam-bool'],
    'download': csv_di['drmfree-bool'],
    'other-key': csv_di['other-key-bool'],
  }
  if csv_di['rebundle-bool'] == '0' and csv_di['store-bool'] == '0':
    for drm in temp_drm:
      if temp_drm[drm] == '1':
        bundle['content']['game'][drm] = [plat for plat in plat_icon_template if temp_plats[plat] == '1']
        bundle['unavailable-platforms'][drm] = [unplat for unplat in plat_icon_template if temp_plats[unplat] == '0']
        if bundle['unavailable-platforms'][drm] == []:
          del bundle['unavailable-platforms'][drm]
    if bundle['unavailable-platforms'] == {}:
      del bundle['unavailable-platforms']
    if csv_di['android-bool'] == '1':
      bundle['content']['mobile'] = {}
      bundle['content']['mobile']['android'] = ['android']
    if csv_di['ps3-bool'] == '1':
      bundle['content']['game']['ps3'] = ['ps3']
    if csv_di['ps4-bool'] == '1':
      bundle['content']['game']['ps4'] = ['ps4']
  elif csv_di['store-bool'] == '1':
    bundle['unavailable-platforms'] = {}
    for drm in temp_drm:
      if temp_drm[drm] == '1':
        bundle['unavailable-platforms'][drm] = [unplat for unplat in plat_icon_template if temp_plats[unplat] == '0']
        if bundle['unavailable-platforms'][drm] == []:
          del bundle['unavailable-platforms'][drm]
    if bundle['unavailable-platforms'] == {}:
      del bundle['unavailable-platforms']
    if csv_di['android-bool'] == '1':
      bundle['content']['mobile'] = {}
      bundle['content']['mobile']['android'] = ['android']
    if csv_di['ps3-bool'] == '1' or csv_di['ps4-bool'] == '1':
      bundle['content'] = {
        'game': {}
      }
    if csv_di['ps3-bool'] == '1':
      bundle['content']['game']['ps3'] = ['ps3']
    if csv_di['ps4-bool'] == '1':
      bundle['content']['game']['ps4'] = ['ps4']
  elif csv_di['rebundle-bool'] == '1' and csv_di['preview-pdf-bool'] == '0':
    rebundle_plats = {'content': {'game': {}}}
    for drm in temp_drm:
      if temp_drm[drm] == '1':
        rebundle_plats['content']['game'][drm] = [plat for plat in plat_icon_template if temp_plats[plat] != '1']
    if csv_di['ps3-bool'] == '1':
      rebundle_plats['content']['game']['ps3'] = ['ps3']
    if csv_di['ps4-bool'] == '1':
      rebundle_plats['content']['game']['ps4'] = ['ps4']
    if csv_di['android-bool'] == '1':
      rebundle_plats['content']['mobile'] = {}
      rebundle_plats['content']['mobile']['android'] = ['android']
    if rebundle_plats['content'] != temp_di['struct']['default']['content']:
      temp_di['struct'][args.bundle] = {}
      temp_di['struct'][args.bundle]['content'] = rebundle_plats['content']


def pretty_filesize(size):
  if (size == 0):
    return '0B'
  size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
  i = int(math.floor(math.log(int(size), 1024)))
  p = math.pow(1024, i)
  s = round(int(size) / p, 2)
  return '%s %s' % (s, size_name[i])


def add_new_displayitem_info(temp_di, csv_di):
  temp_di['machine_name'] = csv_di['machine-name']
  temp_di['struct']['default']['human-name'] = csv_di['human-names']
  bundle = temp_di['struct']['bundle']
  bundle['box-art-human-name'] = csv_di['human-names']
  bundle['front-page-art'] = 'images/displayitems/%s.png' % csv_di['machine-name']

  if csv_di['front-page-subtitle'] != '0':
    bundle['front-page-subtitle'] = csv_di['front-page-subtitle']
  if csv_di['background-image-bool'] == '1':
    bundle['slideshow-background'] = 'images/bg/%s_background.jpg' % csv_di['machine-name']
  if csv_di['slideout-image-bool'] == '1':
    bundle['preview-image'] = 'images/popups/%s_slideout.jpg' % csv_di['machine-name']

  if csv_di['description'] != '0':
    bundle['description-text'] = csv_di['description'].replace('\n', '<br />')

  if csv_di['developer-name'] != '0':
    if csv_di['developer-url'] == '0':
      bundle['developers'] = [{
        'developer-name': csv_di['developer-name']
      }]
    else:
      bundle['developers'] = [{
        'developer-name': csv_di['developer-name'],
        'developer-url': csv_di['developer-url']
      }]
  if csv_di['publisher-name'] != '0':
    if csv_di['publisher-url'] == '0':
      bundle['publishers'] = [{
        'publisher-name': csv_di['publisher-name']
      }]
    else:
      bundle['publishers'] = [{
        'publisher-name': csv_di['publisher-name'],
        'publisher-url': csv_di['publisher-url']
      }]

  platform_icon_handler(temp_di, csv_di)

  if csv_di['youtube-link'] != '0':
    bundle['youtube-link'] = csv_di['youtube-link']

  if csv_di['pdf-preview-bool'] == '1':
    url = signurl('ops/pdfs/%s_preview.pdf' % csv_di['machine-name'])
    metadata = urllib.urlopen(url)
    filesize = metadata.headers['content-length']
    bundle['image_extra'] = {
      'link': 'ops/pdfs/%s_preview.pdf' % csv_di['machine-name'],
      'overlay': {
        'size': pretty_filesize(filesize),
        'type': 'PDF'
       }
    }

  if csv_di['audio-bool'] == '1':
    bundle['soundtrack-hide-tracklist'] = True
    url = signurl('ops/audio/%s_preview.mp3' % csv_di['machine-name'])
    filename, headers = urllib.urlretrieve(url)
    audiofile = MP3(filename)
    bundle['soundtrack-listing'] = [
      {
        'preview-length': str(int(math.ceil(audiofile.info.length))),
        'preview-url': 'ops/audio/%s_preview.mp3' % csv_di['machine-name'],
        'track-name': 'Excerpt',
        'track-number': '1'
      }
    ]

  for key in bundle.keys():
    if bundle[key] == displayitem_template['struct']['bundle'][key]:
      del bundle[key]


def edit_existing_displayitem_info(existing_di, csv_di):
  bundle = existing_di['struct']['bundle']
  platform_icon_handler(existing_di, csv_di)

  if csv_di['rebundle-bool'] == '1':
    struct = existing_di['struct']
    struct[args.bundle]['front-page-art'] = 'images/displayitems/%s_%s.png' % (csv_di['machine-name'], args.bundle)
    if csv_di['background-image-bool'] == '1':
      struct[args.bundle]['slideshow-background'] = 'images/bg/%s_%s_background.jpg' % (csv_di['machine-name'], args.bundle)
    if csv_di['front-page-subtitle'] != '0':
      struct[args.bundle]['front-page-subtitle'] = csv_di['front-page-subtitle']
    if csv_di['description'] != '0':
      struct[args.bundle]['description-text'] = csv_di['description'].replace('\n', '<br />')
    if csv_di['youtube-link'] != existing_di['struct']['default']['youtube-link']:
      struct[args.bundle]['youtube-link'] = csv_di['youtube-link']

  elif csv_di['store-bool'] == '1':
    bundle['box-art-human-name'] = csv_di['human-names']
    bundle['front-page-art'] = 'images/displayitems/%s.png' % csv_di['machine-name']
    if csv_di['front-page-subtitle'] != '0':
      bundle['front-page-subtitle'] = csv_di['front-page-subtitle']
    if csv_di['background-image-bool'] == '1':
      bundle['slideshow-background'] = 'images/bg/%s_background.jpg' % csv_di['machine-name']
    if csv_di['description'] != '0':
      bundle['description-text'] = csv_di['description'].replace('\n', '<br />')
    if csv_di['youtube-link'] != existing_di['struct']['default']['youtube-link']:
      bundle['youtube-link'] = csv_di['youtube-link']

  elif csv_di['exists-bool'] == '1':
    bundle = bundle_template
    add_new_displayitem_info(existing_di, csv_di)


if __name__ == '__main__':
  csvinfo = []
  exportedinfo = []
  displayitems = []

  with open(args.csvfile) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      csvinfo.append(row)

  if args.export:
     with open(args.export) as f:
      exec('exportedinfo = ' + f.read())

  displayitems = prepare_displayitem_list(csvinfo, exportedinfo, displayitems)

  for di, c in zip(displayitems, csvinfo):
    if (c['rebundle-bool'] == '1' or
      c['store-bool'] == '1' or
      c['exists-bool'] == '1'):
        edit_existing_displayitem_info(di, c)
    else:
      add_new_displayitem_info(di, c)

print '['
for di in displayitems:
  print ''.join(prettify(di))
  print ','
print ']'
