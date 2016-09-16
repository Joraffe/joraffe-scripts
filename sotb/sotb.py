#!/usr/bin/env humblepy
import argparse
import sotb_filewriter
import sotb_info

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
args = parser.parse_args()

if __name__ == '__main__':
  sotb = sotb_info.SOTBInfo(args.csvfile)
  di_objs = sotb.prep_displayitems()
  sotb_filewriter.write_pretty_file(di_objs, args.bundle)
