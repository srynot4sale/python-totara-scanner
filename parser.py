#!/usr/bin/env python

#record if statements

# Totara Test Script
#
# Test the results of all get_records() are checked
#
# Usage: php2json.py < input.php > output.json

from phply.phplex import lexer
from phply.phpparse import parser

import simplejson

files = []

class parsed_file:

    path = ''
    original = ''
    source = None

    def __init__(self, path):
        self.path = path


    def load(self):
        self.original = file(self.path, 'r')


    def get_source(self):

        if not self.original:
            self.load()

        if not self.source:
            self.source = parser.parse(
                self.original.read(),
                lexer=lexer,
                tracking=True
            )

        return self.source


class locate:
    type = ''
    results = {}

#    exclude = ['dict']
    inter = ['list', 'tuple', 'dict']
    track = ['Function', 'If', 'Assignment', 'Method', 'FunctionCall', 'TernaryOp', 'ObjectProperty']
    count = 0

    def deep_scan(self, name, item, depth):

        depth = list(depth)
        debug = 0

        self.count += 1

        if hasattr(item, 'generic'):
            item = item.generic(with_lineno=True)

        oftype = type(item).__name__

        if debug:
            print ''
            print name
            print 'Type: %s' % oftype

        # Excluded items
        if oftype == 'tuple':
#            print ''
#            print '%s (%s) at depth (%d)' % (name, oftype, len(depth))
#            print item

            self.check(name, oftype, item, depth)

            if item[0] in self.track:
                if item[0] in ['Function', 'Method', 'FunctionCall']:
                    depth.append('%s (%s)' % (item[0], item[1]['name']))
                else:
                    depth.append(item[0])


        if self.count > 10:
            pass
            #return

        if oftype in self.inter:
            if oftype in ['list', 'tuple']:
                for child in item:
                    self.deep_scan('-', child, depth)
            else:
                for child in item:
                    self.deep_scan(child, item[child], depth)


class locate_checked_calls(locate):

    type = 'call'
    name = None
    vars = []

    def __init__(self, function):
        self.name = function
        self.results['assignment'] = []
        self.results['check'] = []


    def locate(self, files):
        for fileobj in files:
            self.deep_scan('file', fileobj.get_source(), [])

        return self.results


    def check(self, name, oftype, data, depth):
        if oftype != 'tuple':
            return False

        # Look for calls
        if data[0] == 'Assignment':
            if 'expr' in data[1] and type(data[1]['expr']).__name__ == 'tuple':
                if data[1]['expr'][0] == 'FunctionCall':
                    if data[1]['expr'][1]['name'] in self.name:
                        result = {}
                        result['type'] = 'assignment'
                        result['lineno'] = data[1]['lineno']
                        result['depth'] = list(depth)

                        # Generate variable name
                        if data[1]['node'][0] == 'ObjectProperty':
                            vname = data[1]['node'][1]['name']+'['
                            vname += data[1]['node'][1]['node'][1]['name']+']'
                        else:
                            vname = data[1]['node'][1]['name']

                        result['variable'] = vname
                        self.results['assignment'].append(result)
                        self.vars.append(result['variable'])

        # Look for checks
        if data[0] == 'ObjectProperty' and ('If' in depth or 'TernaryOp' in depth):
            # Generate name
            vname = data[1]['name']+'['+data[1]['node'][1]['name']+']'
            if vname in self.vars:
                result = {}
                result['type'] = 'check'
                result['lineno'] = data[1]['lineno']
                result['depth'] = list(depth)
                result['variable'] = vname
                self.results['check'].append(result)


        if data[0] == 'Variable' and ('If' in depth or 'TernaryOp' in depth) and 'ObjectProperty' not in depth:
            if data[1]['name'] in self.vars:
                result = {}
                result['type'] = 'check'
                result['lineno'] = data[1]['lineno']
                result['depth'] = list(depth)
                result['variable'] = data[1]['name']
                self.results['check'].append(result)


def export(items):
    result = []
    if items:
       for item in items:
           if hasattr(item, 'generic'):
               item = item.generic(with_lineno=True)
           result.append(item)
    return result


def get_json():
    sourcefile = parsed_file('test.php')
    sourcefile.original = input
    simplejson.dump(export(sourcefile.get_source()), output, indent=2)
    output.write('\n')


def parse_results(results):
    calls = {}
    for result in results['assignment']:
        # Get latest function call
        f = ''
        for d in result['depth']:
            if d.startswith('Function (') or d.startswith('Method ('):
                f = d

        search = (result['variable'], f)
        calls[search] = result

    for result in results['check']:
        # Get latest function call
        f = ''
        for d in result['depth']:
            if d.startswith('Function (') or d.startswith('Method ('):
                f = d
        search = (result['variable'], f)

        if search in calls:
            del calls[search]
            print 'OK call on line #%d in %s' % (
                result['lineno'],
                repr(result['depth'])
            )

    return calls
