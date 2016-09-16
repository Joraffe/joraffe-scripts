#!/usr/bin/env humblepy
import csv

from sotb_displayitem_export import existing_di
from sotb_displayitem import SOTBDisplayItem as SOTBDisplayItem
from sotb_split import SOTBSplit as SOTBSplit
from sotb_subsplit import SOTBSubSplit as SOTBSubSplit


class SOTBInfo(object):
  """
  A container for information from a given SOTB (.CSV file), organized into
  smaller data structures that can be used by the following other classes:
  - SOTBDisplayItem
  - SOTBSplit
  - SOTBContentEvent
  - SOTBDisplayDefinition

  Attributes:
    di_info             : a list of dict that represent each DisplayItem
                          in the bundle
    di_export           : a list of exported DisplayItems from Model Export
    di_objs             : a list of SOTBDisplayItem objects created from
                          info from self.di_info
    splits              : a list of dict that represent each Split
                          in the bundle
    contentevents       : a list of dict that represent each ContentEvent
                          in the bundle
  """
  di_columns = ('machine_name', 'human_name', 'override', 'exists',
    'background_image', 'slideout_image', 'pdf_preview', 'description',
    'audio', 'device', 'drm', 'platform', 'dev_name', 'dev_url', 'callout',
    'pub_name', 'pub_url', 'youtube')

  splits_columns = ('initial', 'mpa', 'payee', 'split_name', 'sib_split',
    'partner_split', 'subsplit_payee', 'subsplit_name', 'subsplit_sid')

  ce_columns = ('tier', 'human_name', 'subproduct', 'android_subproduct',
    'soundtrack-subproduct', 'tpkd', 'coupondefinition', 'mpa_date',
    'one_dollar_min')

  def __init__(self, csvfile):
    """Return a new SOTBInfo object."""
    self.di_info = self.prep_sotb_list(csvfile, self.di_columns)
    self.di_export = existing_di
    self.splits = self.prep_sotb_list(csvfile, self.splits_columns)
    self.contentevents = self.prep_sotb_list(csvfile, self.ce_columns)

  def prep_sotb_list(self, csvfile, columns):
    """Prepare attribute lists based on specific colunms in the .CSV file"""
    temp = []
    with open(csvfile) as c:
      reader = csv.DictReader(c, columns)
      for row in reader:
        temp.append(row)
    del temp[0]
    return temp

  def prep_displayitems(self):
    """
    Prepares a list of SOTBDisplayItem objects with info from self.di_info

    Returns:
      A list of dictionaries representing the actual DisplayItem's to be
      imported via Model Importer
    """
    sotb_di_objs = []
    existing_di_index = 0
    for index, row in enumerate(self.di_info):
      if (row['override'] == 'bundle' and row['exists'] == '0'):
        sotb_di_objs.append(
          SOTBDisplayItem(self.di_info[index])
        )
      else:
        sotb_di_objs.append(
          SOTBDisplayItem.existing_di(
            self.di_info[index], self.di_export[existing_di_index]
          )
        )
        existing_di_index += 1
    for di in sotb_di_objs:
      di.process()
    return sotb_di_objs

    def prep_splits(self):
