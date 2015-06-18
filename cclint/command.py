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

import codecs
import exceptions
import getopt
import os
import sys
import time

import colorama
import cpplint

import cclint.file_stream


_SYS_STDERR = sys.stderr

def execute_from_command_line():
    start_time = time.time()
    update_cpplint_usage()
    colorama.init()
    filenames = cpplint.ParseArguments(sys.argv[1:])

    print(colorama.Fore.CYAN + colorama.Style.BRIGHT +
          '\n=== CCLINT ===' +
          colorama.Fore.RESET + colorama.Style.RESET_ALL)

    # Initializes the stream for intercepting cpplint's messages and displaying
    # which with customized style.
    stream = cclint.file_stream.FileStream(sys.stderr,
                                           codecs.getreader('utf8'),
                                           codecs.getwriter('utf8'),
                                           'replace')
    stream.Init()
    cpplint_state = cpplint._CppLintState()
    cpplint_state.ResetErrorCounts()
    for filename in filenames:
        stream.PrepareForProcessingFile(filename)
        cpplint.ProcessFile(filename, cpplint_state.verbose_level)
    sys.stderr = _SYS_STDERR

    # Prints the succeeded messages.
    print(colorama.Fore.GREEN + colorama.Style.BRIGHT +
          '\n** LINT SUCCEEDED **' + colorama.Style.RESET_ALL +
          colorama.Fore.WHITE + colorama.Style.DIM +
          ' ({0:.3f} seconds)\n\n'.format(time.time() - start_time) +
          colorama.Fore.RESET + colorama.Style.RESET_ALL)
    # Shows how many errors found.
    total_error_counts = stream.total_error_counts
    if total_error_counts:
        print(colorama.Fore.RED +
              'Total errors found: {0:d}'.format(total_error_counts))
    print(colorama.Fore.RESET + 'Done.\n')
    sys.exit(total_error_counts > 0)

def update_cpplint_usage():
    """Update the usage text defined cpplint"""
    usage = cpplint._USAGE
    usage = usage.replace('cpplint.py', 'cclint')
    usage = usage.replace('                   ', '               ')
    cpplint._USAGE = usage
