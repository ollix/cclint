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
import sys

import colorama

_FILE_STREAM_INITIAL_LINE_INDENT = 6
_SYS_STDERR = sys.stderr

# The patterns to identify warning messages from cpplint's output. Each pattern
# contains a pair of attributes, the first represets the string that should
# matched to the beginning of the cpplint's output, while the second is the
# separator and text behind which will be printed on the screen.
_WARNING_PATTERNS = (('Skipping input', ':'),
                     ('Ignoring', ';'))


class FileStream(codecs.StreamReaderWriter):
    """The stream that intercepts and formats ccplint's output."""

    def Init(self):
        self.previous_file_has_error = False
        self.processed_files = 0
        self.total_error_counts = 0

    def PrepareForProcessingFile(self, filename):
        self.filename = filename
        self.error_counts = 0

        if (filename):
            sys.stderr = self

    def PrintFilename(self, line_indent, state, state_color, message=None):
        current_file_has_error = (state == '✗')
        if self.processed_files == 0 or \
           (self.previous_file_has_error and not current_file_has_error):
            print('')

        print(colorama.Fore.RESET + ' ' * line_indent +
              state_color + state + ' ' + colorama.Fore.RESET +
              colorama.Style.NORMAL + self.filename)
        if (message):
            print(' ' * line_indent +
                  colorama.Fore.CYAN + colorama.Style.DIM +
                  '  // {:}'.format(message) + colorama.Style.RESET_ALL)

        self.processed_files += 1
        self.previous_file_has_error = current_file_has_error

    def write(self, data):
        # Restores the output stream temporarily so interpreter trackback
        # can be displayed as usually.
        sys.stderr = _SYS_STDERR
        line_indent = _FILE_STREAM_INITIAL_LINE_INDENT

        # Exits when done processing a file.
        if data.startswith('Done'):
            if self.error_counts == 0:
                self.PrintFilename(line_indent, '✓', colorama.Fore.GREEN)
            sys.stderr = self
            return

        # Exits when receiving a warning message.
        for beginning_match, seprator in _WARNING_PATTERNS:
            if data.startswith(beginning_match):
                message = data.split(seprator, 1)[1].strip()
                message = message[0].lower() + message[1:]
                self.PrintFilename(line_indent, '⚠', colorama.Fore.YELLOW,
                                   message)
                sys.stderr = self
                return

        # Found an error. Increments the `error_counts`.
        self.error_counts += 1
        self.total_error_counts += 1

        if self.error_counts == 1:
            if self.processed_files > 0:
                print('')
            self.PrintFilename(line_indent, '✗', colorama.Fore.RED)
        filename, line_number, description = data.split(':', 2)
        line_indent += 2

        print(' ' * line_indent +
              colorama.Fore.YELLOW + '#' + line_number +
              colorama.Fore.WHITE + ': ' +
              colorama.Style.DIM + description.strip() +
              colorama.Style.RESET_ALL)

        # Reindirects the output stream to this instance so we can keep
        # intercepting the messages from Google's cpplint.
        sys.stderr = self
