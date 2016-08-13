#! /usr/bin/env humblepy
import argparse

from libraries.cdn import signurl

parser = argparse.ArgumentParser(description='This script generates the signed url version of any download in Highwinds')
parser.add_argument('--path', help='The Highwinds path of the file you want a signed url for.')
parser.add_argument('--pathlist', help='Text file containing the Highwinds path of each file, one per line')
args = parser.parse_args()

if __name__ == '__main__':

    if args.path:
        print
        print "The signed url for " + args.path + " is:"
        print signurl(args.path)
        print
    elif args.pathlist:
        with open(args.pathlist) as f:
            file_paths = f.readlines()
            file_paths = [path.strip() for path in file_paths]
            file_paths = filter(None, file_paths)
            file_paths = set(file_paths)
        for path in file_paths:
            print
            print "The signed url for " + path + " is:"
            print signurl(path)
            print
