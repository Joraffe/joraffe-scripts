#! /usr/bin/env humblepy
import argparse
import csv

from decimal import Decimal
from libraries.aetycoon.prettydata import prettify

parser = argparse.ArgumentParser(
  description='This script automates Pricing Updates for Store Products.'
)
parser.add_argument(
  '-c',
  '--csvfile',
  help='Csv file containing the list of Product machinenames  \
  and their respective new pricing.'),
parser.add_argument(
  '-e',
  '--export',
  help='Exported Python file containing the relevant Products \
  and their pricing dictionaries.'),
args = parser.parse_args()

if __name__ == '__main__':
  csvinfo = []
  products = []
  list_of_prices = {
    'AU': 'USD',
    'EUROPE_EURO': 'EUR',
    'EUROPE_GBP': 'GBP',
    'NZ': 'USD',
    'US': 'USD',
  }

  with open(args.csvfile) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      csvinfo.append(row)

  with open(args.export) as f:
    exec('products = ' + f.read())

  for p, c in zip(products, csvinfo):
    price = p['pricing']
    for price_type in list_of_prices:
      if c[price_type] != 'N/A':
        if price[price_type][0] != c[price_type]:
          price[price_type] = [
            Decimal(c[price_type]),
            list_of_prices[price_type]
          ]
      else:
         continue

print '['
for p in products:
  print ''.join(prettify(p))
  print ','
print ']'
