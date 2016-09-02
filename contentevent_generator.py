#! /usr/bin/env humblepy
import argparse
import copy
import csv
import os
import re

from datetime import datetime
from decimal import Decimal
from libraries.aetycoon.prettydata import prettify

parser = argparse.ArgumentParser()
parser.add_argument(
  '-c',
  help='The .csv file containing the necessary information from the SOTB \
to generate the Content Events for a given Bundle'
)
parser.add_argument(
  '-b',
  '--bundle',
  help='The name of the file to write the content events to'
)
args = parser.parse_args()

PLACEHOLDER_DECIMAL_NUM = 0
PLACEHOLDER_DATETIME = datetime(1968, 1, 8, 11, 0)

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

ce_types = {
  'free': {
    'identifier': 'free',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'requires-min-price': {
      'US': [
        Decimal('0.00'),
        'USD',
      ]
    }
  },
  'initial': {
    'identifier': 'initial',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'subheader': '',
    'display-section-identifiers': [
      'core_tier',
    ],
    'warning-locked': 'Warning: You must pay at least $1.00 to receive content!'
  },
  'bt1': {
    'identifier': 'bt1',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'requires-min-price': {
      'US': [
        Decimal('1'),
        'USD',
      ]
    }
  },
  'bta1': {
    'identifier': 'bta1',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'requires-bta': True,
    'subheader': '',
    'display-section-identifiers': [
      'bta_tier',
    ],
    'warning-locked': 'Warning: You will not receive the beat-the-average content! Add just <%= money_difference %> more to unlock!'
  },
  'mpa_initial': {
    'identifier': 'mpa_initial',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'start-dt': PLACEHOLDER_DATETIME,
    'display-section-identifiers': [
      'core_tier',
    ]
  },
  'mpa_bta': {
    'identifier': 'mpa_bta',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'start-dt': PLACEHOLDER_DATETIME,
    'requires-bta': True,
    'display-section-identifiers': [
      'bta_tier',
    ]
  },
  'mpa_fixed': {
    'identifier': 'mpa_fixed',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'start-dt': PLACEHOLDER_DATETIME,
    'requires-min-price': {
      'US': [
        Decimal(PLACEHOLDER_DECIMAL_NUM),
        'USD',
      ]
    },
    'display-section-identifiers': [
      'btX_tier'
    ]
  },
  'fixed': {
    'identifier': 'fixed',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'requires-min-price': {
      'US': [
        Decimal(PLACEHOLDER_DECIMAL_NUM),
        'USD',
      ]
    },
    'subheader': '',
    'header': '',
    'display-section-identifiers': [
      'btX_tier'
    ],
    'warning-locked': 'Warning: You will not receive the $X content! Add just <%= money_difference %> more to unlock!'
  },
  'average-plus': {
    'identifier': 'average-plus',
    'subproduct-machine-names': [],
    'tpkd-machine-names': [],
    'coupon-definition-machine-names': [],
    'requires-average-plus': Decimal(PLACEHOLDER_DECIMAL_NUM),
    'subheader': '',
    'display-section-identifiers': [
      'btaplus_tier',
    ],
    'warning-locked': 'Warning: You will not receive the beat-the-average-plus content! Add just <%= money_difference %> more to unlock!'
  }
}


def find_highest_priced_tier(csv_info, highest_tier):
  """
  This helper function finds the highest priced content event. Really only used
  to determine how to format the highest priced content event 'subheader'
  """
  sotb_ce = []
  highest_tier_price = 0
  identifier_regex = r'(\D+)(\d+)'
  for row in csv_info:
    if row['tier'] not in sotb_ce and row['tier'] != '':
      sotb_ce.append(row['tier'])
  for ce in sotb_ce:
    try:
      match = re.search(identifier_regex, ce)
      price = int(match.group(2))
      if price > highest_tier_price:
        highest_tier_price = price
        highest_tier = match.group()
      elif match.group(1) == 'average-plus':
        highest_tier = match.group()
    except AttributeError:
      continue
  return highest_tier


def format_datetime(datetime, datetime_string):
  """
  This helper function takes the date from the SOTB and translates it to
  proper datetime format. Used for MPA start-dt mostly.

  Args:
    datetime (datetime obj): The PLACEHOLDER_DATETIME of a given content event
    datetime_string   (str): The String from the SOTB that denotes the MPA date

  Returns:
    A datetime object with updated year, month, day, and hour attributes based
    on the SOTB

  Example:
    >> PLACEHOLDER_DATETIME = datetime(1968, 1, 8, 11, 0)
    >> format_datetime(PLACEHOLDER_DATETIME, '7/5/16 at 11')
    >> PLACEHOLDER_DATETIME
       datetime.datetime(2016, 7, 5, 11, 0)
  """
  try:
    date_info = re.search(r'(\d+)/(\d+)/(\d+) at (\d+)', datetime_string).groups()
  except AttributeError:
    print "Please check your .csv file 'mpa-date': it must be formatted as:"
    print "[month]/[day]/[year] at [hour]"
    quit()
  return datetime.replace(
    int('20' + date_info[2]), int(date_info[0]),
    int(date_info[1]), int(date_info[3]), 0)


def build_skeleton_content_events(csv_info, content_events):
  """
  This function builds the "skeleton" of the Content Events based on info
  from the SOTB. It has basic information such as the proper identifier
  and 'requires' fields, but does not have the subproducts, tpkds,
  coupondefinitions.

  Args:
    csv_info       (list): A list of DictReader objects with info from the SOTB
    content_events (list): An empty list that will be filled with dictionaries

  Returns:
    This function returns a list of dictionaries that represent the "skeleton"
    of the Content Events of a given bundle
  """
  sotb_ce = []
  identifier_regex = r'(\D+)(\d+)'
  for row in csv_info:
    if row['tier'] not in sotb_ce and row['tier'] != '':
      sotb_ce.append(row['tier'])
  for index, ce in enumerate(sotb_ce):
    try:
      match = re.search(identifier_regex, ce)
      ce_id, price = match.group(1), match.group(2)
      if match.group() == 'bt1':
        content_events.insert(index, copy.deepcopy(ce_types['bt1']))
      elif ce_id == 'bt':
        content_events.insert(index, copy.deepcopy(ce_types['fixed']))
        content_events[index]['identifier'] = match.group()
        content_events[index]['requires-min-price']['US'][0] = Decimal(int(price))
        content_events[index]['header'] = 'Pay ${0} or more'.format(price)
        content_events[index]['display-section-identifiers'][0] = 'bt%s_tier' % price
        content_events[index]['warning-locked'] = 'Warning: You will not receive the ${0} content! Add just <%= money_difference %> more to unlock!'.format(price)
      elif ce_id == 'mpa_bt':
        content_events.insert(index, copy.deepcopy(ce_types['mpa_fixed']))
        content_events[index]['identifier'] = match.group()
        content_events[index]['requires-min-price']['US'][0] = Decimal(int(price))
        content_events[index]['display-section-identifiers'][0] = 'bt%s_tier' % price
        content_events[index]['start-dt'] = format_datetime(PLACEHOLDER_DATETIME, csv_info[0]['mpa-date'])
      elif ce_id == 'average-plus':
        content_events.insert(index, copy.deepcopy(ce_types['average-plus']))
        content_events[index]['identifier'] = match.group()
        content_events[index]['requires-average-plus'] = Decimal(int(price))
    except AttributeError:
      content_events.insert(index, copy.deepcopy(ce_types[ce]))
    if ce in ('mpa_initial', 'mpa_bta'):
      content_events[index]['start-dt'] = format_datetime(PLACEHOLDER_DATETIME, csv_info[0]['mpa-date'])
  return content_events


def add_content_rewards(csv_info, content_events):
  """
  This function adds all of the relevant rewards (subproducts, tpkds,
  coupondefinitions). It also adds extra details that's dependant on the number
  of rewards (like subheader).

  Args:
    csv_info       (list): A list of DictReader objects with info from the SOTB
    content_events (list): The list of "skeleton" content event dictionarites
                           with information from the SOTB

  Returns:
    The completed content events that contains all of the rewards for each tier
  """
  temp_identifiers = []
  reward_type_pairs = [
    ('subproducts', 'subproduct-machine-names'),
    ('android-subproducts', 'subproduct-machine-names'),
    ('soundtrack-subproducts', 'subproduct-machine-names'),
    ('tpkds', 'tpkd-machine-names'),
    ('coupondefinitions', 'coupon-definition-machine-names')
  ]
  for ce in content_events:
    temp_identifiers.append({
        'identifier': ce['identifier'],
        'subproduct-machine-names': [],
        'tpkd-machine-names': [],
        'coupon-definition-machine-names': [],
        'num_items': 0,
        'game-names': []
      }
    )

  for row in csv_info:
    # find the proper tier in temp_identifiers
    tier = {}
    for temp_id in temp_identifiers:
      if temp_id['identifier'] == row['tier']:
        tier = temp_id

    # added relevant rewards
    for csv_reward, reward_type in reward_type_pairs:
      if row[csv_reward] != '0':
        tier[reward_type].append(row[csv_reward])
    if row['game-name'] != '0':
      tier['game-names'].append(row['game-name'])

  # get num of games in the bundle (relevant for 'subheader')
  for temp_id in temp_identifiers:
    temp_id['num_items'] = len(temp_id['game-names'])

  # transfer all rewards from temp to actual content events
  for temp_id, ce in zip(temp_identifiers, content_events):
    ce['subproduct-machine-names'] = temp_id['subproduct-machine-names']
    ce['tpkd-machine-names'] = temp_id['tpkd-machine-names']
    ce['coupon-definition-machine-names'] = temp_id['coupon-definition-machine-names']
    if 'subheader' in ce:
      if ce['identifier'] == 'initial':
        ce['subheader'] = 'Get %s titles!' % temp_id['num_items']
      elif ce['identifier'] == highest_tier:
        ce['subheader'] = 'Get all titles!'
      else:
        ce['subheader'] = 'Get %s more titles!' % temp_id['num_items']
    if ce['identifier'] == 'initial' and len(ce['tpkd-machine-names']) != 0:
      del ce['warning-locked']

  if csv_info[0]['1-dollar-min-bool'] == '1':
    content_events.insert(0, copy.deepcopy(lessthan1_content_event))
  return content_events


def write_pretty_content_events_to_file(content_events, file_name):
  """
  This function writes the content events to a new .py file on the users Desktop

  Args:
    content_events  (list): The content events for the given bundle, formatted
                            according to info from the SOTB. This is a list
                            of dictionaries
    file_name        (str): The name of the .py file created by this function
  """
  output_directory = os.path.expanduser('~/Desktop/')
  with open(os.path.join(output_directory, '%s.py' % file_name), 'wb') as f:
    f.write(''.join(prettify(content_events)))
  print "%s.py created" % file_name


if __name__ == '__main__':
  csv_info = []
  content_events = []
  highest_tier = ''

  with open(args.c) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      csv_info.append(row)

  content_events = build_skeleton_content_events(csv_info, content_events)
  highest_tier = find_highest_priced_tier(csv_info, highest_tier)
  content_events = add_content_rewards(csv_info, content_events)

  write_pretty_content_events_to_file(content_events, args.bundle)
