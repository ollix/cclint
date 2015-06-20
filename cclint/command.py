# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Olli Wang. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#    * Neither the name of Olli Wang nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""The cclint command line client.

This script enhances cpplint's capabilities by adding some additional features.
It serves as a superset of cpplint and it does not change any default behavior
of cpplint though it does change the output in a much more readable manner.
Additional features provided by cclint can be accessed through added flags.
"""

from __future__ import print_function
import codecs
import getopt
import glob
import os
import sys
import time

import cpplint

from cclint import file_stream
from cclint import utility


# The long options of cclint that will be passed to `getopt()`.
_CCLINT_GETOPT_LONG_OPTIONS = ['excludedir=', 'expanddir=']
# The additional usage text that will be added to the display usage text.
_CCLINT_USAGE = """
  ---------------------------------------------------------------------------
  Flags added by cclint:

    excludedir=dir
      The directory to prevent all of its content files from processing. This
      flag can be specified multiple times to have more than one exclude
      directories. It is especially useful when combined with the
      '--expanddie=recursive' option.

    expanddir=no|yes|recursive
      Decide how to deal with specified directory arguments. By default the
      value is 'no' which is cpplint's default behavior. If 'yes' is provided,
      then it replaces all directory paths with their content files with
      matched 'extensions'. If 'recursive' is provided, then subdirectories
      are also expanded recursively as well.
"""
# The syntax that will be added to the displayed usage text.
_CCLINT_SYNTAX = "               [--expanddir=no|yes|recursive]"


def parse_arguments():
    """Parses command line arguments.

    Returns:
        A tuple of two values. The first value is a dict of options that used
        by cclint itself, and the second value is a list of filenames passed
        to the command line client.
    """

    # Creates a list of cclint's option names.
    cclint_options = list()
    for signature in _CCLINT_GETOPT_LONG_OPTIONS:
        if signature.endswith('='):
            cclint_options.append(signature[:-1])
        else:
            cclint_options.append(signature)

    # Separates cpplint's and cclint's arguments.
    cclint_args = list()
    cpplint_args = list()
    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            option_name = arg.split('=')[0][2:]
            if option_name in cclint_options:
                cclint_args.append(arg)
                continue
        cpplint_args.append(arg)

    # Parses cclint's arguments.
    options = parse_cclint_arguments(cclint_args)

    # Parses cpplint's arguments and filters passed filenames within the
    # exclude directories.
    filenames = list()
    for filename in cpplint.ParseArguments(cpplint_args):
        if (os.path.isdir(filename) and \
            os.path.relpath(filename) in options['excludedirs']) or \
           (os.path.isfile(filename) and \
            os.path.dirname(filename) in options['excludedirs']):
            continue
        filenames.append(filename)

    return options, filenames

def parse_cclint_arguments(args):
    """Parses arguments defined by cclint.

    Args:
        args: a list of argument strings to be parsed for cclint.

    Returns:
        A dict of parsed cclint arguments.
    """
    try:
        opts = getopt.getopt(args, '', _CCLINT_GETOPT_LONG_OPTIONS)[0]
    except getopt.GetoptError:
        cpplint.PrintUsage('Invalid arguments.')

    options = {'excludedirs': set(), 'expanddir': 'no'}
    for (opt, val) in opts:
        if opt == '--expanddir':
            if val not in ('no', 'yes', 'recursive'):
                cpplint.PrintUsage('The only allowed expanddir formats are '
                                   'no, yes and recursive')
            options['expanddir'] = val
        elif opt == '--excludedir':
            for dirname in glob.iglob(val):
                if os.path.isdir(dirname):
                    options['excludedirs'].add(os.path.relpath(dirname))
    return options

def execute_from_command_line():
    """Executes the cpplint client with added features.

    This function is the entry point of the cclint client.
    """
    start_time = time.time()
    update_cpplint_usage()
    options, cpplint_filenames = parse_arguments()

    # Determines the list of filenames to process.
    if options['expanddir'] == 'no':
        filenames = cpplint_filenames
    else:
        filenames = list()
        recursive = (options['expanddir'] == 'recursive')
        expand_directory = utility.expand_directory

        for filename in cpplint_filenames:
            if os.path.isfile(filename):
                filenames.append(filename)
            elif os.path.isdir(filename):
                expanded_filenames = expand_directory(
                    filename,
                    recursive=recursive,
                    excludedirs=options['excludedirs'])
                filenames.extend(expanded_filenames)

    # Prints the cclint's header message.
    print(utility.get_ansi_code('FOREGROUND_CYAN') +
          utility.get_ansi_code('STYLE_BRIGHT') +
          '\n=== CCLINT ===' +
          utility.get_ansi_code('FOREGROUND_RESET') +
          utility.get_ansi_code('STYLE_RESET_ALL'))

    # Initializes the stream for intercepting and formatting cpplint's output.
    stream = file_stream.FileStream(sys.stderr,
                                    codecs.getreader('utf8'),
                                    codecs.getwriter('utf8'),
                                    'replace')
    cpplint_state = cpplint._CppLintState()  # pylint: disable=protected-access
    cpplint_state.ResetErrorCounts()
    for filename in filenames:
        stream.begin(filename)
        cpplint.ProcessFile(filename, cpplint_state.verbose_level)
        stream.end()

    # Prints the succeeded messages.
    print(utility.get_ansi_code('FOREGROUND_GREEN') +
          utility.get_ansi_code('STYLE_BRIGHT') +
          '\n** LINT SUCCEEDED **' + utility.get_ansi_code('STYLE_RESET_ALL') +
          utility.get_ansi_code('FOREGROUND_WHITE') +
          utility.get_ansi_code('STYLE_DIM') +
          ' ({0:.3f} seconds)\n\n'.format(time.time() - start_time) +
          utility.get_ansi_code('FOREGROUND_RESET') +
          utility.get_ansi_code('STYLE_RESET_ALL'))
    # Shows how many errors are found.
    total_error_counts = stream.total_error_counts
    if total_error_counts:
        print(utility.get_ansi_code('FOREGROUND_RED') +
              'Total errors found: {0:d}'.format(total_error_counts))
    print(utility.get_ansi_code('FOREGROUND_RESET') + 'Done.\n')
    sys.exit(total_error_counts > 0)

def update_cpplint_usage():
    """Update the usage text defined in cpplint."""

    # pylint: disable=protected-access
    cpplint_usage = cpplint._USAGE
    usage_lines = cpplint_usage.split('\n', 4)
    usage_lines.insert(4, _CCLINT_SYNTAX)
    cpplint_usage = '\n'.join(usage_lines)
    cpplint_usage = cpplint_usage.replace('cpplint.py', 'cclint')
    cpplint_usage = cpplint_usage.replace('                   ',
                                          '               ')
    cpplint._USAGE = cpplint_usage + _CCLINT_USAGE
