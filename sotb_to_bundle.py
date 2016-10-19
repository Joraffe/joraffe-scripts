#!/usr/bin/env humblepy
import argparse
import csv
import math
import os
import unidecode
import urllib

from decimal import getcontext
from decimal import Decimal
from libraries.aetycoon.prettydata import prettify
from libraries.cdn import signurl
from mutagen.mp3 import MP3


# Helper function for no unicode problems
def no_unicode(text):
  return unidecode.unidecode(unicode(text, encoding='utf-8'))


# A list of all info on DisplayItems/Splits from the SOTB
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
  # image_extra(),override(),
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
      },
      'video': {
        'rifftrax': ['rifftrax'],
        'video-download': ['hd', 'sd']
      },
      'music': {
        'rifftrax': ['rifftrax'],
        'audio-download': ['mp3', 'flac', 'ogg', 'wav']
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
                                      'windows+mac+linux+android',
                                      'android',
                                      'rifftrax+mp3',
                                      'rifftrax+sd+hd'),
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


def splits(sotb_info):
  template = {
    'initial': {
      'order': []
    },
    'mpa': {
      'order': []
    }
  }

  def supersplits(sotb_info):
    supersplits = []

    def supersplit_gen(row):
      supersplit = {
        'class': row['payee'],
        'name': no_unicode(row['split_name']),
        'sibling_split': Decimal(row['sib_split']),
        'subsplit': []
      }
      if row['invisible_splits'] != '0':
        supersplit['hide_subsplit'] = 'true'
      if row['partner_split'] != '0':
        supersplit['partner_split'] = Decimal(row['partner_split'])
      return supersplit

    for row in sotb_info:
      if row['payee'] != '0':
        supersplit = supersplit_gen(row)
        if supersplit not in supersplits:
          supersplits.append(supersplit)

    return supersplits

  def subsplits(supersplit, override):
    subsplits = []

    # Helper function to generate the "base" of each subsplit
    def subsplit_gen(row):
      subsplit = {
        'class': row['subsplit_payee'],
        'name': no_unicode(row['subsplit_name'])
      }
      if row['subsplit_sid'] != '0':
        subsplit['secondary_id'] = row['subsplit_sid']
      return subsplit

    # Adds the proper 'sibling_split'
    def subsplit_siblingsplits(subsplits):
      # Ensures all 'sibling_split' adds to Decimal('1')
      def add_to_one(subsplits):
        getcontext().prec = 10
        sum_sibling_splits = Decimal('0.0')
        for subsplit in subsplits:
          sum_sibling_splits += subsplit['sibling_split']
        diff = Decimal('1.0') - sum_sibling_splits
        subsplits[0]['sibling_split'] += diff
        return subsplits

      getcontext().prec = 9
      for subsplit in subsplits:
        if subsplit['name'] == 'Choose Your Own Charity':
          subsplit['sibling_split'] = Decimal('0.0')
        elif subsplit['class'] in ('paypalgivingfund', 'tidesdaf') and 'Choose Your Own Charity' in list_charities:
          subsplit['sibling_split'] = Decimal('1.0') / Decimal(len(subsplits) - 1)
        else:
          subsplit['sibling_split'] = Decimal('1.0') / Decimal(len(subsplits))
      return add_to_one(subsplits)

    for row in sotb_info:
      if row['payee'] == supersplit['class'] and row[override] != '0':
        subsplits.append(subsplit_gen(row))

    list_charities = [sub['name'] for sub in subsplits]
    return subsplit_siblingsplits(subsplits)

  def process(splits):
    for override in splits:
      if override == 'mpa' and sotb_info[0]['mpa_date'] == '0':
        continue
      splits[override]['order'] = supersplits(sotb_info)

    if splits['mpa'] == {'order': []}:
      del splits['mpa']

    for override in splits:

      for split in splits[override]['order']:
        split['subsplit'] = subsplits(split, override)

    for override in splits:
      humble_tip = {
        'class': 'humblebundle',
        'name': 'Humble Tip',
        'sibling_split': Decimal('0.20')
      }
      if sotb_info[0]['humble_partners'] != '0':
        humble_tip['partner_split'] = Decimal('0.15')
      splits[override]['order'].append(humble_tip)

      if sotb_info[0]['humble_partners'] != '0':
        splits[override]['order'].append({
          'class': 'partner',
          'name': 'Partner',
          'partner_split': Decimal('0.15'),
          'sibling_split': Decimal('0.0')
        })

    return splits

  return process(template)

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
  '-d',
  '--displayitems',
  help='Flag to indicate if you want DisplayItems to be made (y if yes)'
)
parser.add_argument(
  '-e',
  '--export',
  help='Python file with existing DisplayItem info from Model Exporter. \
        Only to be used if -d flag is on',
)
parser.add_argument(
  '-s',
  '--splits',
  help='Flag to indicate if you want Splits to be made (y if yes)'
)
args = parser.parse_args()


if __name__ == '__main__':
  sotb = sotb(args.csvfile)
  existing_di = []
  output_di = []

  if args.export:
    with open(args.export) as f:
      exec('existing_di = ' + f.read())

  # Prepare DisplayItems
  if args.displayitems == 'y':
    edi_index = 0
    for row in sotb:
      if row['exists'] == '0':
        output_di.append(di(row))
      else:
        output_di.append(di(row, existing_di[edi_index]))
        edi_index += 1
    write_pretty_file(output_di, args.bundle)

  # Prepare Splits
  if args.splits == 'y':
    bundle_splits = splits(sotb)
    write_pretty_file(bundle_splits, args.bundle + '_splits')
