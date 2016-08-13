#! /usr/bin/env python

import argparse
import openpyxl
import os

parser = argparse.ArgumentParser()
parser.add_argument(
    '-e',
    '--excelfile',
    help='The excelfile containing the keys'),
parser.add_argument(
    '-d',
    '--directory',
    help='The directory that contains all of the excel files containing keys.',
)
parser.add_argument(
    '-s',
    '--sheet',
    help='The sheet in the excelfile that contains the keys',
)
parser.add_argument(
    '-c',
    '--column',
    default=0,
    help='The column in the excelfile that contains the keys',
)
args = parser.parse_args()


def multiple_excel_files(directory):
    # TO DO
    pass


def single_excel_file(excelfile):
    filename_with_ext = os.path.basename(excelfile)
    filename = os.path.splitext(filename_with_ext)[0]
    wb = openpyxl.load_workbook(args.excelfile)
    if args.sheet:
        sheet = wb.get_sheet_by_name(args.sheet)
    else:
        sheet = wb.active
    with open('%s.txt' % (filename), 'w') as f:
        for cell in sheet.columns[int(args.column)]:
            f.write(str(cell.value))
            f.write('\n')


if __name__ == '__main__':
    # TO DO
    # if args.directory:
        # multiple_excel_files(args.directory)
    if args.excelfile:
        single_excel_file(args.excelfile)
