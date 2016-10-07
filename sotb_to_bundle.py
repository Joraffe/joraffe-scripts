#!/usr/bin/env humblepy
import argparse
import csv
import math
import os
import unidecode
import urllib

from libraries.aetycoon.prettydata import prettify
from libraries.cdn import signurl
from mutagen.mp3 import MP3


# A list of all info on DisplayItems from the SOTB
# Each item in the list = a row on the SOTB
def sotb(csvfile):
  sotb_info = []
  with open(csvfile) as c:
    reader = csv.DictReader(c)
    for row in reader:
      sotb_info.append(row)
  return sotb_info


def di(row, existing_di=None):
  # Helper functions:
  # image_extra(), no_unicode(),override(),
  # partners(), platform_icons(), soundtrack_listing()
  def image_extra(machine_name):
    def pretty_filesize(size):
      if (size == 0):
        return '0B'
      size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB',)
      i = int(math.floor(math.log(int(size), 1024)))
      p = math.pow(1024, i)
      s = round(int(size) / p, 2)
      return '%s %s' % (s, size_name[i])

    path = 'ops/pdfs/%s_preview.pdf' % machine_name
    url = signurl(path)
    metadata = urllib.urlopen(url)
    filesize = metadata.headers['content-length']

    def pdf_preview():
      return {
        'link': path,
        'overlay': {
          'size': pretty_filesize(filesize),
          'type': 'PDF'
        }
      }
    return pdf_preview

  def no_unicode(text):
    return unidecode.unidecode(unicode(text, encoding='utf-8'))

  def override(path):
    if row['override'] != 'bundle':
      return path + '_' + row['override']
    else:
      return path

  def partners(partner_type):
    def my_partners():
      return [
        {
          partner_type + '-name': row[partner_type + '_name'],
          partner_type + '-url': row[partner_type + '_url']
        }
      ]
    return my_partners

  def platform_icons(type_icons):
    PLAT_ICONS = {
      'game': {
        'steam': ['windows', 'mac', 'linux'],
        'download': ['windows', 'mac', 'linux'],
        'other-key': ['windows', 'mac', 'linux'],
        'uplay': ['windows', 'mac', 'linux'],
        'origin': ['windows', 'mac', 'linux'],
        'wiiu': ['wiiu'],
        '3DS': ['3DS'],
        'ps3': ['ps3'],
        'ps4': ['ps4'],
        'xboxone': ['xboxone']
      },
      'mobile': {
        'android': ['android'],
        'iOS': ['iOS']
      }
    }
    devices = row['device'].split('+')
    drms = row['drm'].split('+')
    plats = row['platform'].split('+')

    def platformer():
      if type_icons == 'content':
        temp_icons = {}
        for device in devices:
          temp_icons[device] = {}
          for drm in drms:
            if drm in PLAT_ICONS[device]:
              temp_icons[device][drm] = []
              for plat in plats:
                if plat in PLAT_ICONS[device][drm]:
                  temp_icons[device][drm].append(plat)
        return temp_icons
      else:
        temp_unavailable = {}
        for device in devices:
          for drm in drms:
            if drm in PLAT_ICONS[device]:
              temp_unavailable[drm] = []
              for plat in PLAT_ICONS[device][drm]:
                if plat not in plats and plat != 'android':
                  temp_unavailable[drm].append(plat)
        return temp_unavailable

    return platformer

  def soundtrack_listing(machine_name):
    def soundtrack_lister():
      mp3_path = 'ops/audio/%s_preview.mp3' % machine_name
      url = signurl(mp3_path)
      filename, headers = urllib.urlretrieve(url)
      audiofile = MP3(filename)
      di[row['override']]['soundtrack-hide-tracklist'] = True
      return [
        {
          'preview-length': str(int(math.ceil(audiofile.info.length))),
          'preview-url': mp3_path,
          'track-name': 'Excerpt',
          'track-number': '1'
        }
      ]
    return soundtrack_lister

  # Data structure to hold logic & formatted value for each DisplayItem key
  process = {
    'box-art-human-name': {
      'logic': row['override'] == 'bundle',
      'value': no_unicode(row['human_name'])
    },
    'content': {
      'logic': row['device'] != '0',
      'value': platform_icons('content')
    },
    'description-text': {
      'logic': row['description'] != '0',
      'value': no_unicode(row['description'])
    },
    'developers': {
      'logic': '0' != row['developer_name'] != '0' and row['developer_url'] != '0',
      'value': partners('developer')
    },
    'front-page-art': {
      'logic': True,
      'value': override('images/displayitems/%s' % row['machine_name']) + '.png'
    },
    'front-page-subtitle': {
      'logic': row['callout'] != '0',
      'value': no_unicode(row['callout'])
    },
    'image_extra': {
      'logic': row['pdf_preview'] != '0',
      'value': image_extra(row['machine_name'])
    },
    'preview-image': {
      'logic': row['slideout_image'] != '0',
      'value': 'images/popups/%s_slideout.jpg' % row['machine_name']
    },
    'publishers': {
      'logic': row['publisher_name'] != '0' and row['publisher_url'] != '0',
      'value': partners('publisher')
    },
    'soundtrack-listing': {
      'logic': row['audio'] != '0',
      'value': soundtrack_listing(row['machine_name'])
    },
    'unavailable-platforms': {
      'logic': row['platform'] not in ('0',
                                      'windows+mac+linux',
                                      'windows+mac+linux+android'),
      'value': platform_icons('unavailable')
    },
    'youtube-link': {
      'logic': row['youtube'] != '0',
      'value': row['youtube']
    }
  }

  # Processes DisplayItem and returns it
  def process_di():
    if existing_di is None:
      di = {
        'machine_name': row['machine_name'],
        'struct': {
          'default': {},
          row['override']: {}
        }
      }
      di['struct']['default']['human-name'] = di.get('human-name', no_unicode(row['human_name']))
    else:
      di = existing_di
      del di['exported_at']
      di['struct'][row['override']] = di.get(row['override'], {})
    for key in process:
      needed = process[key]['logic']
      value = process[key]['value']
      if needed:
        if callable(value):
          di['struct'][row['override']][key] = di.get(key, value())
        else:
          di['struct'][row['override']][key] = di.get(key, value)
    return di

  return process_di()


# Function to write file to Desktop
def write_pretty_file(content, filename):
  output_directory = os.path.expanduser('~/Desktop/')
  with open(os.path.join(output_directory, '%s.py' % filename), 'wb') as f:
    if isinstance(content, dict):
      f.write(''.join(prettify(content)))
    elif isinstance(content, list):
      f.write('[\n')
      for c in content:
        f.write(''.join(prettify(c)))
        f.write('\n,\n')
      f.write(']')
  print "%s.py has been created" % filename

# Arguments for the script
parser = argparse.ArgumentParser()
parser.add_argument(
  '-b',
  '--bundle',
  help='The machinename of the bundle that will be using all of the \
  DisplayItems edited by this script. This is also the name of the .py \
  file created.',
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


if __name__ == '__main__':
  sotb = sotb(args.csvfile)
  existing_di = []
  displayitems = []

  if args.export:
    with open(args.export) as f:
      exec('existing_di = ' + f.read())

  edi_index = 0
  for row in sotb:
    if row['exists'] == '0':
      displayitems.append(di(row))
    else:
      displayitems.append(di(row, existing_di[edi_index]))
      edi_index += 1

  write_pretty_file(displayitems, args.bundle)
