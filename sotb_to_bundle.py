#!/usr/bin/env humblepy
import argparse
import csv
import math
import os
import re
import unidecode
import urllib

from datetime import datetime
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

  def desc_process(text):
    mc_match = re.search(r'(\D+:\s)(.*)\s(.*),\s(\d+)(.*)', text)
    if mc_match:
      text = "<p>Get 10% off one month of a Humble Monthly subscription!</p><p>NOTE: Expires on " + mc_match.group(2) + ' ' + mc_match.group(3) + ', ' + mc_match.group(4) + " at 10:00am Pacific. Eligible for new subscribers. Payment will be applied&nbsp;on&nbsp;the first payment for new subscribers.</p>"
    if 'android' in row['device'].split('+'):
      text += "<br /><br /><span style='text-decoration: underline;'>Size</span>: XX MB<br /><span style='text-decoration: underline;'>Requires Android</span>: XX and up<br /><br />Check out all the system requirements&nbsp;<a href='' target='_blank' rel='nofollow'>here</a>."
    return no_unicode(text)

  def override(path):
    if row['override'] != 'bundle':
      return path + '_' + row['override']
    else:
      return path

  def partners(partner_type):
    def my_partners():
      if row[partner_type + '_name'] == '0' and row[partner_type + '_url'] == '0':
        return []
      else:
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
      'value': desc_process(row['description'])
    },
    'developers': {
      'logic': True,
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
      'logic': True,
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

    # delete empty publishers if not needed
    if len(di['struct'][row['override']]['developers']) == 0 and 'developers' not in di['struct']['default']:
      del di['struct'][row['override']]['developers']
    if len(di['struct'][row['override']]['publishers']) == 0 and 'publishers' not in di['struct']['default']:
      del di['struct'][row['override']]['publishers']

    return di

  return process_di()


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
      if row['payee'] == supersplit['class'] and row[override] != '0' and row['subsplit_payee'] != '0':
        subsplits.append(subsplit_gen(row))

    if len(subsplits) != 0:
      list_charities = [sub['name'] for sub in subsplits]
      return subsplit_siblingsplits(subsplits)
    else:
      return []

  def process_splits(splits):
    for override in splits:
      if override == 'mpa' and sotb_info[0]['mpa_date'] == '0':
        continue
      splits[override]['order'] = supersplits(sotb_info)

    if splits['mpa'] == {'order': []}:
      del splits['mpa']

    for override in splits:

      for split in splits[override]['order']:
        split['subsplit'] = subsplits(split, override)
        if len(split['subsplit']) == 0:
          del split['subsplit']

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

  return process_splits(template)


def ce(sotb_info):
  ce_list = []
  lessthan1_content_event = {
    'identifier': 'lessthan1',
    'subproduct-machine-names': [
      'lessthan1',
    ],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'requires-min-price': {
      'US': [
        Decimal('0.01'),
        'USD',
      ]
    },
    'requires-max-price': {
      'US': [
        Decimal('1'),
        'USD',
      ]
    }
  }

  def find_highest_priced_tier(content_events):
    def ce_ranker(content_event):
      rank = 0
      if 'requires-bta' in content_event:
        rank += 2
      if 'requires-min-price' in content_event:
        rank += int(content_event['requires-min-price']['US'][0])
      if 'requires-average-plus' in content_event:
        rank += int(content_event['requires-min-price']['US'][0]) + 2
      if 'start-dt' in content_event:
        rank -= 5
      return (content_event, rank)

    def compare_ce_rank(ce1, ce2):
      if ce1[1] > ce2[1]:
        return ce1
      else:
        return ce2

    ce_ranks = []
    for ce in content_events:
      ce_ranks.append(ce_ranker(ce))

    highest_ce_rank = reduce(compare_ce_rank, ce_ranks)
    return highest_ce_rank[0]['identifier']

  def ce_generator(tier):
    # Helper method to format warning-locked
    def warn_formatter(match_obj, tier):
      if match_obj:
        if match_obj.group(1) == 'bta':
          return 'Warning: You will not receive the beat-the-average content! Add just<%= money_difference %> more to unlock!'
        elif match_obj.group(1) == 'average-plus':
          return 'Warning: You will not receive the beat-the-average-plus content! Add just<%= money_difference %> more to unlock!'
        elif match_obj.group(1) in ('bt', 'mpa_bt'):
          return 'Warning: You will not receive the %s content! Add just<%%= money_difference %%> more to unlock!' % ('$' + match_obj.group(2))
        else:
          return ''
      elif tier == 'initial' and sotb_info[0]['one_dollar_min'] != '0':
        return 'Warning: You must pay at least $1.00 to receive content!'
      else:
        return ''

    # Helper method to format display-section-identifiers
    def dsi_formatter(tier):
      if tier == 'initial':
        return 'core_tier'
      else:
        return tier + '_tier'

    # Create regular expressions to filter what type of ce
    id_match = re.search(r'(\D+)(\d+)', tier)
    if id_match:
      ce_id, price = id_match.group(1), id_match.group(2)

    if tier == 'mpa_':
      tier = 'mpa'

    # Initialize a templated ce with common keys/values
    ce_template = {
      'identifier': tier,
      'subproduct-machine-names': [],
      'tpkd-machine-names': [],
      'coupon-definition-machine-names': []
    }

    # Add display-section-identifiers if needed
    if tier != 'bt1':
      ce_template['display-section-identifiers'] = [dsi_formatter(tier)]
      ce_template['subheader'] = ''
      ce_template['warning-locked'] = warn_formatter(id_match, tier)

    # Add proper requires method based on re
    if id_match:
      if ce_id in ('bt', 'mpa_bt'):
        ce_template['requires-min-price'] = {
            'US': [
                Decimal(price),
                'USD'
            ]
        }
      if ce_id == 'average-plus':
        ce_template['requires-average-plus'] = {
            'US': [
                Decimal(price),
                'USD'
            ]
        }
      if ce_id == 'bta':
        ce_template['requires-bta'] = True
      if ce_id == 'free':
        ce_template['requires-min-price'] = {
            'US': [
                Decimal('0.00'),
                'USD'
            ]
        }
    mpa_match = re.search(r'(mpa)(.*)', tier)

    # This re used to see if it's an mpa item or not
    if mpa_match:
      ce_template['start-dt'] = datetime.strptime(sotb_info[0]['mpa_date'], '%m/%d/%y at %I')

    # Output the altered ce_template
    return ce_template

  def ce_rewards(row, content_event):
    reward_type_pairs = [
      ('subproducts', 'subproduct-machine-names'),
      ('android_subproducts', 'subproduct-machine-names'),
      ('soundtrack_subproducts', 'subproduct-machine-names'),
      ('tpkds', 'tpkd-machine-names'),
      ('coupondefinitions', 'coupon-definition-machine-names')
    ]
    for sotb_reward, reward_type in reward_type_pairs:
      if row[sotb_reward] != '0':
        for reward in row[sotb_reward].split('\n'):
          content_event[reward_type].append(reward)

  def process_ce(content_events):
    # Helper method to find a tier's corresponding ce
    def find_ce(tier):
      for ce in content_events:
        if ce['identifier'] == tier:
          return ce

    def num_games(tier):
      num = 0
      for row in sotb_info:
        if row['tier'] == tier:
          num += 1
      return num

    tier_list = []
    # collect unique tiers from sotb
    for row in sotb_info:
      if row['tier'] not in ('', '0') and row['tier'] not in tier_list:
        tier_list.append(row['tier'])

    # generate ce skeletons for each tier
    for tier in tier_list:
      content_events.append(ce_generator(tier))

    # Add the proper rewards for each ce
    for row in sotb_info:
      if row['tier'] != '':
        ce_rewards(row, find_ce(row['tier']))

    # Add finishing touches to ce
    for ce in content_events:
      if 'subheader' in ce:
        if ce['identifier'] == 'initial':
          ce['subheader'] = 'Get %s titles!' % num_games(ce['identifier'])
        elif ce['identifier'] == find_highest_priced_tier(content_events):
          ce['subheader'] = 'Get all titles!'
        else:
          ce['subheader'] = 'Get %s more titles!' % num_games(ce['identifier'])

    if sotb_info[0]['one_dollar_min'] == '1':
      content_events.insert(0, lessthan1_content_event)

    return content_events

  return process_ce(ce_list)


# Function to write file to Desktop
def write_pretty_file(content, filename):
  output_directory = os.path.expanduser('~/Desktop/')
  with open(os.path.join(output_directory, '%s.py' % filename), 'wb') as f:
    f.write(''.join(prettify(content)))
  print "%s.py has been created" % filename

# Arguments for the script
parser = argparse.ArgumentParser()
parser.add_argument(
  'csvfile',
  help='path to csv file containing all info on DisplayItems from the SOTB',
  type=str
)
parser.add_argument(
  'bundle',
  help='the machinename of the bundle. Used for DisplayItem overrides and \
  output file names',
  type=str
)
parser.add_argument(
  '-di',
  '--displayitems',
  help='flag to indicate if you want DisplayItems to be made',
  action='store_true'
)
parser.add_argument(
  '-s',
  '--splits',
  help='flag to indicate if you want Splits to be made',
  action='store_true'
)
parser.add_argument(
  '-ce',
  '--contentevents',
  help='flag to indicate if you want Content Events to be made',
  action='store_true'
)
parser.add_argument(
  '-e',
  '--export',
  help='path to python file with existing DisplayItem info from model \
        exporter. Only to be used if -d flag is on',
  type=str
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
  if args.displayitems:
    edi_index = 0
    for row in sotb:
      if row['machine_name'] != '':
        if row['exists'] == '0':
          output_di.append(di(row))
        else:
          output_di.append(di(row, existing_di[edi_index]))
          edi_index += 1
    write_pretty_file(output_di, args.bundle + '_displayitems')

  # Prepare Splits
  if args.splits:
    bundle_splits = splits(sotb)
    write_pretty_file(bundle_splits, args.bundle + '_splits')

  if args.contentevents:
    bundle_ce = ce(sotb)
    write_pretty_file(bundle_ce, args.bundle + '_contentevents')
