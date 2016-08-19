#! /usr/bin/env humblepy
import argparse
import csv
import os

from decimal import getcontext
from decimal import Decimal
from libraries.aetycoon.prettydata import prettify

parser = argparse.ArgumentParser()
parser.add_argument(
  '-c',
  '--csvfile',
  help='The csv file containing information about the splits from the SOTB',
)
parser.add_argument(
  '-b',
  '--bundle',
  help='The name of the file to write the splits to',
)
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

partner_split_list = [
    Decimal('0.60'),
    Decimal('0.10'),
    Decimal('0.15'),
]


def add_partner_splits(splits):
  """
  This function adds partner_splits to each type of split (Dev/Pub, Charity,
  Humble) as well as adds a 4th split specifically for Partners.

  Args:
    splits (dict): The splits of a given bundle (without partner splits info)
  """
  for identifier in splits:
    for payee_type in enumerate(splits[identifier]['order']):
      payee_type[1]['partner_split'] = partner_split_list[payee_type[0]]
    splits[identifier]['order'].append(partner_splits)


def polish_subsplits(subsplits):
  """
  This helper function polishes the subsplits for Devs/Charity to remove
  extraneous 'secondary_id' and to have the sum of the Decimal value equal
  to exactly 1.

  Args:
    subsplits (list): A list of "raw" splits (dictionaries) generated by
                      add_subsplits()

  Returns:
    This function returns the a "polished" version of the subsplits it takes
    as a parameter

  Example:
    ex_sibling_splits = [
      Decimal(0.333333333),
      Decimal(0.333333333),
      Decimal(0.333333333)
    ]
    >> polish_subsplits(subsplits)
    ex_sibling_splits = [
      Decimal(0.333333334),
      Decimal(0.333333333),
      Decimal(0.333333333)
    ]
  """
  getcontext().prec = 10
  sum_sibling_splits = Decimal('0.0')
  for subsplit in subsplits:
    if subsplit['secondary_id'] != '0':
        del subsplit['secondary_id']
    sum_sibling_splits += subsplit['sibling_split']
  diff = Decimal('1.0') - sum_sibling_splits
  subsplits[0]['sibling_split'] += diff
  return subsplits


def add_subsplits(csv_info, splits):
  """
  This function extracts the payment information for a Bundle from the .CSV
  file that has been exported from a given SOTB and generates the subsplits
  for both Devs/Pubs and Charities involved.

  Args:
    csv_info   (dict): A dictionary of lists of DictReader objects with info
                       from the SOTB. The dictionary has 'initial' and 'mpa'
    splits     (dict): The "base" version of the splits. Usually a deepcopy of
                       template_splits

  Returns:
    This function returns splits with "raw" subsplits added based off of info
    from the SOTB
  """
  temp_subsplits = {
    'initial': {
      'dev_subsplits': [],
      'charity_subsplits': [],
    },
    'mpa': {
      'dev_subsplits': [],
      'charity_subsplits': [],
    }
  }
  for identifier in temp_subsplits:
    dev_subsplits = temp_subsplits[identifier]['dev_subsplits']
    charity_subsplits = temp_subsplits[identifier]['charity_subsplits']

    # Extract payee info from SOTB
    for row in csv_info[identifier]:
        if row['partner-name'] != '':
          dev_subsplits.append(
            {
              'class': row['partner-payee'],
              'name': row['partner-name'],
              'secondary_id': row['partner-secondary-id'],
            }
          )
        if row['charity-name'] != '' and row['charity-secondary-id'] != 'cyoc':
          charity_subsplits.append(
            {
              'class': row['charity-name'],
              'name': row['charity-payee'],
              'secondary_id': row['charity-secondary-id'],
            }
          )

    # Add "raw" sibling_split
    getcontext().prec = 9
    for dev in dev_subsplits:
      dev['sibling_split'] = Decimal('1.0') / Decimal(len(dev_subsplits))
    for charity in charity_subsplits:
      charity['sibling_split'] = Decimal('1.0') / Decimal(len(charity_subsplits))

    # Polish subsplits
    dev_subsplits = polish_subsplits(dev_subsplits)
    charity_subsplits = polish_subsplits(charity_subsplits)

    # Add CYOC if needed
    if csv_info[identifier][0]['cyoc-bool'] == '1':
      charity_subsplits.append(cyoc_subsplit)

    # Delete subsplits if not needed
    devs = splits[identifier]['order'][0]
    charities = splits[identifier]['order'][1]
    if len(dev_subsplits) == 1:
      del devs['subsplit']
      devs['class'] = dev_subsplits[0]['class']
      devs['name'] = dev_subsplits[0]['name']
    else:
      devs['subsplit'] = dev_subsplits
    if len(charity_subsplits) == 1:
      del charities['subsplit']
      charities['class'] = charity_subsplits[0]['class']
      charities['name'] = charity_subsplits[0]['name']
    else:
      charities['subsplit'] = charity_subsplits
  return splits


def write_pretty_splits_to_file(splits, filename):
  """
  This function writes the splits to a new .py file on the users Desktop

  Args:
    splits  (dict): The splits for the given bundle, formatted according to
                    info from the SOTB
    filename (str): The name of the .py file created by this function
  """
  script_directory = os.path.normpath(__file__)
  path_list = script_directory.split(os.sep)
  output_directory = '/%s/%s/Desktop/' % (path_list[1], path_list[2])
  with open(os.path.join(output_directory, '%s.py' % filename), 'wb') as f:
    f.write(''.join(prettify(splits)))
  print "%s.py created" % filename


if __name__ == '__main__':
  csv_info = {
    'initial': [],
    'mpa': [],
  }
  splits = template_splits.copy()

  with open(args.csvfile) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      if row['mpa-bool'] == '0':
        csv_info['initial'].append(row)
        csv_info['mpa'].append(row)
      elif row['mpa-bool'] == '1':
        csv_info['mpa'].append(row)

  # Delete mpa if not needed
  if len(csv_info['initial']) == len(csv_info['mpa']):
    del csv_info['mpa']
    del splits['mpa']

  # Extract and add splits
  splits = add_subsplits(csv_info, splits)

  # Add Bundle Partner Splits if needed
  if csv_info['initial'][0]['bundle-partners-bool'] == '1':
    add_partner_splits(splits)

  # write_pretty_splits_to_file(splits, args.bundle)
