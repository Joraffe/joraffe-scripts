#! /usr/bin/env humblepy
import argparse
import csv

from decimal import getcontext
from decimal import localcontext
from decimal import Decimal
from libraries.aetycoon.prettydata import prettify

parser = argparse.ArgumentParser()
parser.add_argument(
  '-c',
  '--csvfile',
  help='The csv file containing information about the splits from the SOTB')
args = parser.parse_args()

base_splits = {
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
      }
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
      }
    ]
  }
}

cyoc_splits = {
  'class': 'paypalgivingfund',
  'name': 'Chose your own charity',
  'secondary_id': 'cyoc',
  'sibling_split': Decimal('0.0'),
}

base_humbletip = {
  'class': 'humblebundle',
  'name': 'Humble Tip',
  'sibling_split': Decimal('0.20'),
}

partner_splits = {
  'class': 'partner',
  'name': 'Partner',
  'sibling_split': Decimal('0.0'),
  'partner_split': Decimal('0.15'),
}

partner_ajusted_splits = [
  # 'partner_split' for Devs/Pubs:
  Decimal('0.60'),
  # 'partner_split' for Charity:
  Decimal('0.10'),
  # 'partner_split' for Humble:
  Decimal('0.15'),
]


def add_partner_splits(splits):
  # TO DO -- Needs some work
  pass


def add_split_information(payee_info, base_splits, identifier):
  getcontext().prec = 8
  base_order_index = base_splits[identifier]['order']
  for payee_type_index in range(len(base_order_index)):
    subsplits = base_order_index[payee_type_index]['subsplit']
    csv_payee_info = payee_info[payee_type_index]
    num_payees = len(payee_info[payee_type_index])
    for payee_info_index in range(num_payees):
      if len(payee_info) == 1:
        del subsplits
        break
      else:
        subsplits.append(
          {
            'class': csv_payee_info[payee_info_index]['payee'],
            'name': csv_payee_info[payee_info_index]['human-name'],
            'secondary_id': csv_payee_info[payee_info_index]['secondary_id']
          }
        )
    raw_sibling_splits = []
    for sibling_split in range(num_payees):
      raw_sibling_splits.append(Decimal('1.0') / Decimal(num_payees))
    sibling_index = 0
    adjusted_sibling_splits = sibling_splits_add_to_one(raw_sibling_splits)
    for subsplit in subsplits:
      subsplit['sibling_split'] = adjusted_sibling_splits[sibling_index]
      if subsplit['secondary_id'] == '0':
        del subsplit['secondary_id']
      sibling_index += 1
  return base_splits[identifier]


def sibling_splits_add_to_one(sibling_splits):
  list_of_sibling_splits = sibling_splits
  sum_of_sibling_splits = Decimal('0.0')
  for sibling_split in list_of_sibling_splits:
    with localcontext() as ctx2:
      ctx2.prec = 10
      sum_of_sibling_splits += sibling_split
  diff = Decimal('1.0') - sum_of_sibling_splits
  if diff == Decimal('0.0'):
    return list_of_sibling_splits
  else:
    diff_count = abs(int(diff / Decimal('1.0E-9')))
    diff_adjust = abs(diff / Decimal(diff_count))
    sibling_split_index = 0
    for sibling_split in range(diff_count):
      if diff < 0.0:
        list_of_sibling_splits[sibling_split_index] -= diff_adjust
      elif diff > 0.0:
        list_of_sibling_splits[sibling_split_index] += diff_adjust
      sibling_split_index += 1
  return list_of_sibling_splits


def extract_payee_info(csvinfo):
  payee_info = [
    # partner_info
    [],
    # charity_info
    [],
  ]
  for payee in csvinfo:
    if payee['partner-name'] == '':
      continue
    else:
      payee_info[0].append(
        {
          'human-name': payee['partner-name'],
          'payee': payee['partner-payee'],
          'secondary_id': payee['partner-secondary-id'],
          'mpa-bool': payee['mpa-bool'],
        }
      )
    if payee['charity-name'] == '':
      continue
    else:
      payee_info[1].append(
        {
          'human-name': payee['charity-name'],
          'payee': payee['charity-payee'],
          'secondary_id': payee['charity-secondary-id'],
        }
      )
  return payee_info


if __name__ == '__main__':
  initial_csvinfo = []
  mpa_csvinfo = []
  splits = base_splits.copy()

  with open(args.csvfile) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      if row['mpa-bool'] == '0':
        initial_csvinfo.append(row)
        mpa_csvinfo.append(row)
      elif row['mpa-bool'] == '1':
        mpa_csvinfo.append(row)

  # Extract and add initial splits
  initial_payee_info = extract_payee_info(initial_csvinfo)
  splits['initial'] = add_split_information(initial_payee_info, splits, 'initial')
  splits['initial']['order'].append(base_humbletip)

  # Extract and add mpa splits
  mpa_payee_info = extract_payee_info(mpa_csvinfo)
  splits['mpa'] = add_split_information(mpa_payee_info, splits, 'mpa')
  splits['mpa']['order'].append(base_humbletip)

  # Add CYOC if needed
  if initial_csvinfo[0]['cyoc-bool'] == '1':
    splits['initial']['order'][1]['subsplit'].append(cyoc_splits)
    splits['mpa']['order'][1]['subsplit'].append(cyoc_splits)

  # Add Bundle Partner Splits if needed (TO DO)
  # if initial_csvinfo[0]['bundle-partners-bool'] == '1':
  #  add_partner_splits(splits)

  # Delete mpa splits if not needed
  if splits['initial'] == splits['mpa']:
    del splits['mpa']

  print ''.join(prettify(splits))
