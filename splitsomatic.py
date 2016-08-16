#! /usr/bin/env humblepy
import argparse
import csv

from decimal import getcontext
from decimal import Decimal
from libraries.aetycoon.prettydata import prettify

parser = argparse.ArgumentParser()
parser.add_argument(
  '-c',
  '--csvfile',
  help='The csv file containing information about the splits from the SOTB')
args = parser.parse_args()

template_splits = {
  'initial': {
    'order': [
      {
        'class': 'developers',
        'name': 'Developers',
        'sibling_split': Decimal('0.65'),
        'subsplit': [],
      },
      {
        'class': 'charity',
        'name': 'Charity',
        'sibling_split': Decimal('0.15'),
        'subsplit': [],
      },
      {
        'class': 'humblebundle',
        'name': 'Humble Tip',
        'sibling_split': Decimal('0.20'),
      },
    ]
  },
  'mpa': {
    'order': [
      {
        'class': 'developers',
        'name': 'Developers',
        'sibling_split': Decimal('0.65'),
        'subsplit': [],
      },
      {
        'class': 'charity',
        'name': 'Charity',
        'sibling_split': Decimal('0.15'),
        'subsplit': [],
      },
      {
        'class': 'humblebundle',
        'name': 'Humble Tip',
        'sibling_split': Decimal('0.20'),
      },
    ]
  },
}

cyoc_subsplit = {
  'class': 'paypalgivingfund',
  'name': 'Chose your own charity',
  'secondary_id': 'cyoc',
  'sibling_split': Decimal('0.0'),
}

partner_splits = {
  'class': 'partner',
  'name': 'Partner',
  'sibling_split': Decimal('0.0'),
  'partner_split': Decimal('0.15'),
}


def add_partner_splits(splits):
  splits['initial']['order'].append(partner_splits)
  splits['initial']['order'][0]['partner_split'] = Decimal('0.60')
  splits['initial']['order'][1]['partner_split'] = Decimal('0.10')
  splits['initial']['order'][2]['partner_split'] = Decimal('0.15')
  if 'mpa' in splits:
    splits['mpa']['order'].append(partner_splits)
    splits['mpa']['order'][0]['partner_split'] = Decimal('0.60')
    splits['mpa']['order'][1]['partner_split'] = Decimal('0.10')
    splits['mpa']['order'][2]['partner_split'] = Decimal('0.15')


def polish_subsplits(subsplits):
  '''
  Polishes the subsplits for Devs/Charity to remove extraneous 'secondary_id'
  and to have the sum of the Decimal value equal to exactly 1.
  For example:
  Decimal(0.333333333)                      Decimal(0.333333334)
  Decimal(0.333333333)          -->         Decimal(0.333333333)
  Decimal(0.333333333)                      Decimal(0.333333333)
  '''
  getcontext().prec = 10
  sum_sibling_splits = Decimal('0.0')
  for subsplit in subsplits:
    if subsplit['secondary_id'] is '0':
        del subsplit['secondary_id']
    sum_sibling_splits += subsplit['sibling_split']
  diff = Decimal('1.0') - sum_sibling_splits
  subsplits[0]['sibling_split'] += diff
  return subsplits


def add_subsplits(csvinfo, splits, identifier):
  '''
  Extracts the payment information for a Bundle from the .CSV file
  that has been exported from a given SOTB and generates the subsplits
  for both Devs/Pubs and Charities involved.

  Takes a .CSV file (csvinfo) and a splits template (empty subsplit list)
  and returns splits with an unpolished/raw subsplit list.
  '''
  dev_subsplits = []
  charity_subsplits = []
  for item in csvinfo:
    if item['partner-name'] is not '':
      dev_subsplits.append(
        {
          'class': item['partner-payee'],
          'name': item['partner-name'],
          'secondary_id': item['partner-secondary-id'],
        }
      )
    if item['charity-name'] is not '' and item['charity-secondary-id'] is not 'cyoc':
      charity_subsplits.append(
        {
          'class': item['charity-name'],
          'name': item['charity-payee'],
          'secondary_id': item['charity-secondary-id'],
        }
      )
  getcontext().prec = 9
  for dev in dev_subsplits:
    dev['sibling_split'] = Decimal('1.0') / Decimal(len(dev_subsplits))
  for charity in charity_subsplits:
    charity['sibling_split'] = Decimal('1.0') / Decimal(len(charity_subsplits))

  # Polish subsplits: remove extraneous 'secondary_id' & sibling_splits add to 1
  dev_subsplits = polish_subsplits(dev_subsplits)
  charity_subsplits = polish_subsplits(charity_subsplits)

  # Add CYOC to charities subsplits if needed
  if csvinfo[0]['cyoc-bool'] is '1':
    charity_subsplits.append(cyoc_subsplit)

  devs = splits[identifier]['order'][0]
  charities = splits[identifier]['order'][1]

  # If there is only 1 dev/pub or charity, subsplits no longer needed
  if len(dev_subsplits) is 1:
    del devs['subsplit']
    devs['class'] = dev_subsplits[0]['class']
    devs['name'] = dev_subsplits[0]['name']
  else:
    devs['subsplit'] = dev_subsplits
  if len(charity_subsplits) is 1:
    del charities['subsplit']
    charities['class'] = charity_subsplits[0]['class']
    charities['name'] = charity_subsplits[0]['name']
  else:
    charities['subsplit'] = charity_subsplits
  return splits


if __name__ == '__main__':
  initial_csvinfo = []
  mpa_csvinfo = []
  splits = template_splits.copy()

  with open(args.csvfile) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      if row['mpa-bool'] is '0':
        initial_csvinfo.append(row)
        mpa_csvinfo.append(row)
      elif row['mpa-bool'] is '1':
        mpa_csvinfo.append(row)

  # Extract and add initial splits
  splits = add_subsplits(initial_csvinfo, splits, 'initial')
  # Extract and add mpa splits, if needed
  if len(initial_csvinfo) is not len(mpa_csvinfo):
    splits = add_subsplits(mpa_csvinfo, splits, 'mpa')
  else:
      del splits['mpa']

  # Add Bundle Partner Splits if needed (TO DO)
  if initial_csvinfo[0]['bundle-partners-bool'] is '1':
    add_partner_splits(splits)

  print ''.join(prettify(splits))
