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

DEBUG = []

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

    scan = ['list', 'tuple', 'dict']

    def locate(self, files):
        for fileobj in files:
            self.deep_scan('file', fileobj.get_source(), [])

        return self.results


    def deep_scan(self, name, item, depth):

        # Make a copy of the depth list
        depth = list(depth)

        # If generic, rebuild item
        if hasattr(item, 'generic'):
            item = item.generic(with_lineno=True)

        # Get item's python type
        oftype = type(item).__name__

        # Only scan tuples
        if oftype == 'tuple':
            self.check(name, oftype, item, depth)

            # Append current node to depth tree (with details for some types)
            if item[0] in ['Class', 'Function', 'Method', 'FunctionCall']:
                depth.append('%s (%s)' % (item[0], item[1]['name']))
            else:
                depth.append(item[0])

        elif oftype == 'dict':
            depth.append(item.keys()[0])

        # Recurse into each item
        if oftype in self.scan:
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


    def check(self, name, oftype, data, depth):
        if oftype != 'tuple':
            return False

        # DEBUGGING
        if data[1]['lineno'] in DEBUG:
            print name
            print data
            print depth
            print ''

        # Look for calls
        if data[0] == 'Assignment':
            if 'expr' in data[1] and type(data[1]['expr']).__name__ == 'tuple':
                if data[1]['expr'][0] == 'FunctionCall':
                    if data[1]['expr'][1]['name'] in self.name:
                        result = {}
                        result['type'] = 'assignment'
                        result['lineno'] = data[1]['lineno']
                        result['depth'] = list(depth)

                        # Get variable name
                        vname = self.get_var_name(data[1]['node'])
                        if vname:
                            result['variable'] = vname
                            self.results['assignment'].append(result)
                            self.vars.append(result['variable'])

                        # Check to see if this inside a unary op
                        if depth[len(depth)-4:] == ['If', 'node', 'UnaryOp', 'expr']:
                            result = {}
                            result['type'] = 'check'
                            result['lineno'] = data[1]['lineno']
                            result['depth'] = list(depth)
                            result['variable'] = vname
                            self.results['check'].append(result)

        # Look for checks
        vname = self.get_var_name(data)
        if vname and name == 'expr' and depth[len(depth)-2:] != ['Foreach', 'node']:
            if 1:#vname in self.vars:
                result = {}
                result['type'] = 'check'
                result['lineno'] = data[1]['lineno']
                result['depth'] = list(depth)
                result['variable'] = vname
                self.results['check'].append(result)


    def get_var_name(self, data):
        """
        Check to see if a node is a variable or object property,
        and if it is return a string representation of it's name
        """
        if data[0] == 'ObjectProperty':
            vname = data[1]['node'][1]['name']+'['
            vname += data[1]['name']+']'
        elif data[0] == 'Variable':
            vname = data[1]['name']
        else:
            vname = False

        return vname


def parse_results(results):
    calls = results['assignment']

    def get_scope(depth):
        # Get scope
        scope = ''
        for d in depth:
            if d.startswith('Function (') or d.startswith('Method ('):
                scope = d
        return scope


    for check in results['check']:
        # Get scope
        scope = get_scope(check['depth'])

        i = -1
        for call in calls:
            i += 1

            # Check if in same function / method scope
            if scope != '' and scope not in call['depth']:
                continue

            # If in the global scope
            if scope == '' and get_scope(call['depth']) != '':
                continue

            # Check this is the same variable and the check is after the call
            if check['variable'] == call['variable'] and call['lineno'] <= check['lineno']:
                del calls[i]
                print 'OK call on line #%d in %s' % (
                    check['lineno'],
                    repr(check['depth'])
                )
#                break

    return calls
