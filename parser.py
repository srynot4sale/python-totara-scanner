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
        self.original = None
        self.original = file(self.path, 'r')


    def get_source(self):
        if not self.original:
            self.load()

        if not self.source:
            try:
                self.source = parser.parse(
                    self.original.read(),
                    lexer=lexer,
                    tracking=True
                )
            except SyntaxError as (errno, strerror):
                print 'Ignoring %s due to advanced syntax' % self.path
                print errno
                print strerror
                return None

        return self.source


class locate:

    type = ''
    results = {}

    def locate(self, files):
        for fileobj in files:
            source = fileobj.get_source()
            if not source:
                continue

            self.deep_scan('-', source, [])

        return self.results


    def deep_scan(self, name, item, depth):

        # Make a copy of the depth list
        depth = list(depth)

        # If generic, rebuild item
        if hasattr(item, 'generic'):
            item = item.generic(with_lineno=True)

        # Get item's python type
        oftype = type(item).__name__

        if oftype == 'dict' and 'name' in item:
            depth.append('%s (%s)' % (name, item['name']))
        elif name not in ['-', 'nodes']:
            depth.append(name)

        # Only scan tuples
        if oftype == 'tuple':
            self.check(name, oftype, item, depth)

        # Recurse into each item
        if oftype == 'tuple':
            for child in item[1:]:
                self.deep_scan(item[0], child, depth)

        if oftype == 'list':
            for child in item:
                self.deep_scan('-', child, depth)

        elif oftype in ['dict']:
            for child in item:
                # Skip unneeded nodes
                if child in ['lineno', 'name']:
                    continue

                # Skip empty params
                if child == 'params' and item[child] == []:
                    continue

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
            print ''
            print name
            print data
            print depth
            print ''

        # Generate depth string for easier searching
        strdepth = ',' + ','.join(depth) + ','

        # Check if we are inside a if or ternary expression
        incheck = (',If,expr,' in strdepth or ',TernaryOp,expr,' in strdepth)

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
                        # Maybe just check if If, Expr is inside depth?
                        if incheck:
                            result = {}
                            result['type'] = 'check'
                            result['lineno'] = data[1]['lineno']
                            result['depth'] = list(depth)
                            result['variable'] = vname
                            self.results['check'].append(result)

        # Look for checks
        vname = self.get_var_name(data)
        if vname and incheck:
            if vname in self.vars:
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
        if data[0] == 'ObjectProperty' and isinstance(data[1]['name'], str) and 'name' in data[1]['node'][1]:
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
                    display_depth(check['depth'])
                )
#                break

    return calls


def display_depth(depth):
    return ' -> '.join(depth)


class locate_global_vars(locate):

    type = 'call'
    name = None
    vars = []


    def __init__(self, vars):
        self.name = vars
        self.results['globals'] = []
        self.results['usage'] = []


    def check(self, name, oftype, data, depth):
        if oftype != 'tuple':
            return False

        # DEBUGGING
        if data[1]['lineno'] in DEBUG:
            print ''
            print 'name: %s' % name
            print 'data: %s' % str(data)
            print 'depth: %s' % depth
            print ''

        # Generate depth string for easier searching
        strdepth = ',' + ','.join(depth) + ','

        # Check if we are inside a if or ternary expression
        incheck = (',If,expr,' in strdepth or ',TernaryOp,expr,' in strdepth)

        # Look for globals
        if data[0] == 'Variable' and depth[-1] == 'Global' and data[1]['name'] in self.name:
            result = {}
            result['type'] = 'global variable'
            result['lineno'] = data[1]['lineno']
            result['depth'] = list(depth[0:-1])
            if not len(result['depth']):
                result['depth'] = ['global scope']

            result['variable'] = data[1]['name']
            self.results['globals'].append(result)
            return


        # Look for uses of globals
        if data[0] == 'Variable' and depth[-1] != 'Global' and data[1]['name'] in self.name:
            result = {}
            result['type'] = 'variable usage'
            result['lineno'] = data[1]['lineno']
            result['depth'] = list(depth)
            if not len(result['depth']):
                result['depth'] = ['global scope']

            result['variable'] = data[1]['name']
            self.results['usage'].append(result)
            return


    def get_var_name(self, data):
        """
        Check to see if a node is a variable or object property,
        and if it is return a string representation of it's name
        """
        if data[0] == 'ObjectProperty' and isinstance(data[1]['name'], str) and 'name' in data[1]['node'][1]:
            vname = data[1]['node'][1]['name']+'['
            vname += data[1]['name']+']'
        elif data[0] == 'Variable':
            vname = data[1]['name']
        else:
            vname = False

        return vname


def parse_results2(results):
    globals = results['globals']
    usage = results['usage']
    badcalls = []

    def get_scope(depth):
        # Get scope
        scope = ''
        for d in depth:
            if d.startswith('Function (') or d.startswith('Method ('):
                scope = d
        return scope


    for use in usage:
        found = False

        # Get scope
        scope = get_scope(use['depth'])

        # Ignore global scope
        if scope == '':
            continue

        i = -1
        for glo in globals:
            i += 1

            # Check if in same function / method scope
            if scope != '' and scope not in glo['depth']:
                continue

            # If in the global scope
            if scope == '' and get_scope(glo['depth']) != '':
                continue

            # Check this is the same variable and the check is after the call
            if glo['variable'] == use['variable'] and glo['lineno'] < use['lineno']:
#                print 'OK usage on line #%d in %s' % (
#                    use['lineno'],
#                    display_depth(use['depth'])
#                )
                found = True
                break

        if not found:
            badcalls.append(use)

    return badcalls
