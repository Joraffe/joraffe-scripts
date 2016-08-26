#! /usr/bin/env python

import argparse
import openpyxl
import os

parser = argparse.ArgumentParser()
parser.add_argument(
  '-e',
  '--excelfile',
  help='The excelfile containing the keys',
)
parser.add_argument(
  '-d',
  '--directory',
  help='The directory that contains all of the excel files containing keys.',
)
parser.add_argument(
  '--sheet',
  help='The sheet in the excelfile that contains the keys (if not the initial \
  active sheet upon opening the excelfile).',
)
parser.add_argument(
  '--column',
  default=0,
  help='The column in the excelfile that contains the keys. Default is the \
  first column, but can specify otherwise.',
)
args = parser.parse_args()


def multiple_excel_files(directory):
  '''
  This function applies single_excel_file() to a whole directory and prints
  status messages to the user about the progress.

  This function takes a single parameter: a directory containing all of the
  .xlsx files to be converted to simple .txt files.
  '''
  for dir_name, subdir_list, file_list in os.walk(directory):
    full_dir_name = os.path.abspath(directory)
    if not full_dir_name.endswith('/'):
      full_dir_name += '/'
    print "Making .txt files of all .xlsx files in %s:" % dir_name
    for file_name in file_list:
      single_excel_file(full_dir_name + file_name)
      print "%s.txt created in directory: %s" % (file_name, dir_name)


def single_excel_file(excelfile):
  '''
  This function essentially converts a .xlsx file containing a single column of
  many keys (i.e. 300,000) into a .txt file with each key on a newline for
  compatability with Humble Bundle's TPKD Importer.

  This function takes a single paramete: a .xlsx file and writes a new .txt
  file in the current directory.
  '''
  filename_with_ext = os.path.basename(excelfile)
  filename = os.path.splitext(filename_with_ext)[0]
  wb = openpyxl.load_workbook(excelfile)
  if args.sheet:
    sheet = wb.get_sheet_by_name(args.sheet)
  else:
    sheet = wb.active
  with open('%s.txt' % (filename), 'w') as f:
    for cell in sheet.columns[int(args.column)]:
      f.write(str(cell.value))
      f.write('\n')


if __name__ == '__main__':
  if args.directory:
    multiple_excel_files(args.directory)
  elif args.excelfile:
    single_excel_file(args.excelfile)
