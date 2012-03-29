#!/usr/bin/env python

# Totara Test Script
#
# Test the results of all get_records() are checked
#
# Usage: php2json.py < input.php > output.json

import parser
import sys
import fnmatch
import os

files = []

for arg in sys.argv[1:]:
    print arg
    if arg.endswith('.php'):
        files.append(parser.parsed_file(arg))
    else:
        for root, dirnames, filenames in os.walk(arg):
            for filename in fnmatch.filter(filenames, '*.php'):
                print os.path.join(root, filename)
                pf = parser.parsed_file(os.path.join(root, filename))
                files.append(pf)

finding = parser.locate_global_vars(['$DB'])

print ''
#print 'Checking for all global variables'
results = finding.locate(files)
#print ''
#print 'Global calls found: %d' % len(results['globals'])
#print ''

#for result in results['globals']:
#    print '%s type on line #%d of %s in %s' % (
#        result['type'],
#        result['lineno'],
#        result['variable'],
#        parser.display_depth(result['depth'])
#    )
#print ''


print 'Usage found: %d' % len(results['usage'])
#print ''
#
#for result in results['usage']:
#    print '%s type on line #%d of %s in %s' % (
#        result['type'],
#        result['lineno'],
#        result['variable'],
#        parser.display_depth(result['depth'])
#    )
#print ''

#print 'OKed calls:'
#print ''
calls = parser.parse_results2(results)

if len(calls) < 1:
    pass
#    print ''
#    print 'YAY - no faults found'

else:

#    print ''
    print 'BAD - %d fault(s) found!' % len(calls)
    print ''
    for result in calls:

        print '%s on line #%d in %s' % (
            result['variable'],
            result['lineno'],
            parser.display_depth(result['depth'])
        )
