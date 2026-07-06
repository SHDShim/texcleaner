#!/usr/bin/python
"""
    pymergechanges: Merge commits made with changes package into text
    Copyright (C) 2018  Y. Cui

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

pymergechanges: Merge commits made with changes package into text

Requires Python version 3; Tested on Python 3.6.6

Supported commands: added, deleted, replaced, highlight
Usage: python pyMergeChanges.py [-arh] <Input File> <Output File>
<Output File> will be overwritten and must be different than <Input File>.
Options:
    -a: accept all added, deleted and replaced
    -r: reject all added, deleted and replaced
    -h: remove all highlights
If no option is given, runs interactively.

Created on Wed Dec  5 20:28:40 2018
Revised on Tue Aug 27 17:51:58 2019

"""

import sys
import re
import codecs

def parse_param(parstr):
    if all(p in parstr for p in ('a', 'r')):
        print('You cannot accept and reject at the same time.')
        sys.exit(1)
    parout = ''
    for par in parstr[1:]:
        if par == 'a':
            print('Accepting all added, deleted and replaced')
            parout += 'a'
        elif par == 'r':
            print('Rejecting all added, deleted and replaced')
            parout += 'r'
        elif par == 'h':
            print('Removing all highlights.')
            parout += 'h'
        else:
            print('Unknown parameter: ' + par)
            sys.exit(1)
    if not parout:
        parout = 'i'
    return parout

def ask1():
    if PARAMS == 'i':
        while True:
            ans = input('[a]ccept or [r]eject or [k]eep or [b]reak ? ').lower()
            if ans == 'a':
                print('Accepted.')
                break
            elif ans == 'r':
                print('Rejected.')
                break
            elif ans == 'k':
                print('Kept.')
                break
            elif ans == 'b':
                print('Alright.')
                break
    elif any(p == 'a' for p in PARAMS):
        print('Accepted.')
        ans = 'a'
    elif any(p == 'r' for p in PARAMS):
        print('Rejected.')
        ans = 'r'
    else:
        ans = 'k'
    return ans

def ask2():
    if PARAMS == 'i':
        while True:
            ans = input('[r]emove or [k]eep or [b]reak ? ').lower()
            if ans == 'r':
                print('Removed.')
                break
            elif ans == 'k':
                print('Kept.')
                break
            elif ans == 'b':
                print('Alright.')
                break
        return ans
    elif any(p == 'h' for p in PARAMS):
        print('Removed.')
        ans = 'r'
    else:
        print('Kept.')
        ans = 'k'
    return ans

def trim_space(text, pos):
    if text[pos-1:pos+1] == '  ':
        text = text[:pos] + text[pos+1:]
    return text

def find_matching_brace(text, start):
    if text[start] != '{':
        return -1
    count = 1
    pos = start + 1
    while pos < len(text) and count > 0:
        if text[pos] == '{':
            count += 1
        elif text[pos] == '}':
            count -= 1
        pos += 1
    if count == 0:
        return pos - 1
    return -1

def get_arg_content(text, brace_start):
    end = find_matching_brace(text, brace_start)
    if end == -1:
        return None, -1
    return text[brace_start + 1:end], end

RE_ADDED = re.compile(r'(\\added)(\[[^\]]*\])?\{')
RE_DELETED = re.compile(r'(\\deleted)(\[[^\]]*\])?\{')
RE_REPLACED = re.compile(r'(\\replaced)(\[[^\]]*\])?\{')
RE_HIGHLIGHT = re.compile(r'(\\highlight)(\[[^\]]*\])?\{')
RE_COMMENT = re.compile(r'(\\comment)(\[[^\]]*\])?\{')

if len(sys.argv) not in [3, 4]:
    print(__doc__)
    sys.exit(1)

if len(sys.argv) == 3:
    print('Running in interactive mode. ')
    INPUTFILE, OUTPUTFILE = sys.argv[1:]
    PARAMS = "i"
if len(sys.argv) == 4:
    PARAMLIST, INPUTFILE, OUTPUTFILE = sys.argv[1:]
    PARAMS = parse_param(PARAMLIST)

if INPUTFILE == OUTPUTFILE:
    print('Input File and Output File must be different.')
    sys.exit(1)

with codecs.open(INPUTFILE, mode='r', encoding='utf8') as fin:
    content = fin.read()

FLAG_FAST_BREAK = False
matchAdded = RE_ADDED.search(content)
matchDeleted = RE_DELETED.search(content)
matchReplaced = RE_REPLACED.search(content)
matchHighlight = RE_HIGHLIGHT.search(content)
matchComment = RE_COMMENT.search(content)
has_commits = matchAdded or matchDeleted or matchReplaced or matchHighlight or matchComment

if not has_commits:
    with codecs.open(OUTPUTFILE, mode='w', encoding='utf8') as fout:
        fout.write(content)
else:
    while matchAdded:
        if FLAG_FAST_BREAK:
            break
        print('\n** add commit ** \n' + matchAdded.group())
        answer = ask1()
        cmd_end = matchAdded.end(0)
        arg_content, brace_end = get_arg_content(content, cmd_end - 1)
        if arg_content is None:
            matchAdded = RE_ADDED.search(content, cmd_end + 1)
            continue
        if answer == 'a':
            content = (content[:matchAdded.start(0)]
                       + arg_content + content[brace_end + 1:])
            content = trim_space(content, matchAdded.start(0) + len(arg_content))
            content = trim_space(content, matchAdded.start(0))
            matchAdded = RE_ADDED.search(content, matchAdded.start(0) + len(arg_content))
        elif answer == 'r':
            content = (content[:matchAdded.start(0)] + content[brace_end + 1:])
            content = trim_space(content, matchAdded.start(0))
            matchAdded = RE_ADDED.search(content, matchAdded.start(0))
        elif answer == 'k':
            matchAdded = RE_ADDED.search(content, brace_end + 1)
        elif answer == 'b':
            FLAG_FAST_BREAK = True
            break

    matchDeleted = RE_DELETED.search(content)
    while matchDeleted:
        if FLAG_FAST_BREAK:
            break
        print('\n** delete commit ** \n' + matchDeleted.group())
        answer = ask1()
        cmd_end = matchDeleted.end(0)
        arg_content, brace_end = get_arg_content(content, cmd_end - 1)
        if arg_content is None:
            matchDeleted = RE_DELETED.search(content, cmd_end + 1)
            continue
        if answer == 'a':
            content = (content[:matchDeleted.start(0)] + content[brace_end + 1:])
            content = trim_space(content, matchDeleted.start(0))
            matchDeleted = RE_DELETED.search(content, matchDeleted.start(0))
        elif answer == 'r':
            content = (content[:matchDeleted.start(0)] + arg_content
                       + content[brace_end + 1:])
            content = trim_space(content, matchDeleted.start(0) + len(arg_content))
            content = trim_space(content, matchDeleted.start(0))
            matchDeleted = RE_DELETED.search(content, matchDeleted.start(0) + len(arg_content))
        elif answer == 'k':
            matchDeleted = RE_DELETED.search(content, brace_end + 1)
        elif answer == 'b':
            FLAG_FAST_BREAK = True
            break

    matchReplaced = RE_REPLACED.search(content)
    while matchReplaced:
        if FLAG_FAST_BREAK:
            break
        print('\n** replace commit ** \n' + matchReplaced.group())
        answer = ask1()
        cmd_end = matchReplaced.end(0)
        arg1_content, brace_end1 = get_arg_content(content, cmd_end - 1)
        if arg1_content is None:
            matchReplaced = RE_REPLACED.search(content, cmd_end + 1)
            continue
        arg2_content, brace_end2 = get_arg_content(content, brace_end1 + 1)
        if arg2_content is None:
            matchReplaced = RE_REPLACED.search(content, brace_end1 + 1)
            continue
        if answer == 'a':
            content = (content[:matchReplaced.start(0)]
                       + arg1_content + content[brace_end2 + 1:])
            content = trim_space(content, matchReplaced.start(0) + len(arg1_content))
            content = trim_space(content, matchReplaced.start(0))
            matchReplaced = RE_REPLACED.search(content, matchReplaced.start(0) + len(arg1_content))
        elif answer == 'r':
            content = (content[:matchReplaced.start(0)]
                       + arg2_content + content[brace_end2 + 1:])
            content = trim_space(content, matchReplaced.start(0) + len(arg2_content))
            content = trim_space(content, matchReplaced.start(0))
            matchReplaced = RE_REPLACED.search(content, matchReplaced.start(0) + len(arg2_content))
        elif answer == 'k':
            matchReplaced = RE_REPLACED.search(content, brace_end2 + 1)
        elif answer == 'b':
            FLAG_FAST_BREAK = True
            break

    matchHighlight = RE_HIGHLIGHT.search(content)
    while matchHighlight:
        if FLAG_FAST_BREAK:
            break
        print('\n** highlight commit ** \n' + matchHighlight.group())
        answer = ask2()
        cmd_end = matchHighlight.end(0)
        arg_content, brace_end = get_arg_content(content, cmd_end - 1)
        if arg_content is None:
            matchHighlight = RE_HIGHLIGHT.search(content, cmd_end + 1)
            continue
        if answer == 'r':
            content = (content[:matchHighlight.start(0)]
                       + arg_content + content[brace_end + 1:])
            content = trim_space(content, matchHighlight.start(0) + len(arg_content))
            content = trim_space(content, matchHighlight.start(0))
            matchHighlight = RE_HIGHLIGHT.search(content, matchHighlight.start(0) + len(arg_content))
        elif answer == 'k':
            matchHighlight = RE_HIGHLIGHT.search(content, brace_end + 1)
        elif answer == 'b':
            FLAG_FAST_BREAK = True
            break

    matchComment = RE_COMMENT.search(content)
    while matchComment:
        if FLAG_FAST_BREAK:
            break
        print('\n** comment commit ** \n' + matchComment.group())
        answer = ask2()
        cmd_end = matchComment.end(0)
        arg_content, brace_end = get_arg_content(content, cmd_end - 1)
        if arg_content is None:
            matchComment = RE_COMMENT.search(content, cmd_end + 1)
            continue
        if answer == 'r':
            content = content[:matchComment.start(0)] + content[brace_end + 1:]
            content = trim_space(content, matchComment.start(0))
            matchComment = RE_COMMENT.search(content, matchComment.start(0))
        elif answer == 'k':
            matchComment = RE_COMMENT.search(content, brace_end + 1)
        elif answer == 'b':
            FLAG_FAST_BREAK = True
            break

    with codecs.open(OUTPUTFILE, mode='w', encoding='utf8') as fout:
        fout.write(content)