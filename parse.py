#!/usr/bin/env python

# Totara Test Script
#
# Test the results of all get_records() are checked
#
# Usage: php2json.py < input.php > output.json

import parser

files = []

files.append(parser.parsed_file('/home/aaronb/code/dev/totaraparser/test.php'))
#files.append(parser.parsed_file('/home/aaronb/code/dev/totaraparser/totara.php'))

finding = parser.locate_checked_calls(
    [
        'get_records',
        'get_records_sql',
        'get_record',
        'get_record_sql',
        'get_field',
        'get_records_select',
        'get_record_select'
    ]
)

print ''
print 'Checking calls to get_records() and other dml functions'
results = finding.locate(files)
print ''
print 'Calls found: %d' % len(results['assignment'])
print ''

for result in results['assignment']:
    print '%s type on line #%d of %s in %s' % (
        result['type'],
        result['lineno'],
        result['variable'],
        repr(result['depth'])
    )

print ''
calls = parser.parse_results(results)

if len(calls) < 1:
    print ''
    print 'YAY - no faults found'

else:

    print ''
    print 'BOO - found faults!'
    print '%d fault(s) found' % len(calls)
    print ''
    for call in calls:
        result = calls[call]

        print '%s on line #%d in %s' % (
            result['variable'],
            result['lineno'],
            repr(result['depth'])
        )
        print ''
