#!/usr/bin/env python3
# acceptchanges3: process trackchanges.sty commands.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Based on accept.py version 0.2 (2006-05-31).
# Copyright (C) 2006 Felix Salfner (salfner@informatik.hu-berlin.de).
# The original was licensed under GPL-2.0-or-later.
#
# Modified in 2026 by Dan Shim and TeXCleaner contributors: converted to
# Python 3, replaced the line-oriented parser with recursive parsing for
# multiline/nested commands, and added reject and UTF-8-safe batch behavior.
# This modified version is distributed under GPL-3.0-or-later, as permitted
# by the original license's "or any later version" clause.
# It is distributed without warranty; see the repository LICENSE file.

"""Accept or reject trackchanges.sty commands in a LaTeX document."""

from optparse import OptionParser
import re
import sys


COMMAND_RE = re.compile(r"\\(annote|note|add|remove|change)(?![A-Za-z@])")


def _is_escaped(text, position):
    slashes = 0
    position -= 1
    while position >= 0 and text[position] == "\\":
        slashes += 1
        position -= 1
    return slashes % 2 == 1


def find_matching_brace(text, start):
    if start < 0 or start >= len(text) or text[start] != "{":
        return -1
    depth = 1
    position = start + 1
    while position < len(text):
        char = text[position]
        if char == "%" and not _is_escaped(text, position):
            newline = text.find("\n", position)
            position = len(text) if newline == -1 else newline + 1
            continue
        if char in "{}" and not _is_escaped(text, position):
            depth += 1 if char == "{" else -1
            if depth == 0:
                return position
        position += 1
    return -1


def _find_optional_end(text, start):
    if start >= len(text) or text[start] != "[":
        return start
    position = start + 1
    while position < len(text):
        if text[position] == "]" and not _is_escaped(text, position):
            return position + 1
        position += 1
    return -1


def _parse_command(text, match):
    position = match.end()
    while position < len(text) and text[position].isspace():
        position += 1
    optional_end = _find_optional_end(text, position)
    if optional_end == -1:
        return None
    position = optional_end
    while position < len(text) and text[position].isspace():
        position += 1

    first_start = position
    first_end = find_matching_brace(text, first_start)
    if first_end == -1:
        return None
    args = [(first_start, first_end)]
    if match.group(1) in {"annote", "change"}:
        second_start = first_end + 1
        while second_start < len(text) and text[second_start].isspace():
            second_start += 1
        second_end = find_matching_brace(text, second_start)
        if second_end == -1:
            return None
        args.append((second_start, second_end))
    return match.group(1), args, first_start, args[-1][1] + 1


def _interactive_change():
    while True:
        answer = input("Accept change, Reject change or Ignore? [A|r|i] ").lower()
        if answer in {"a", "r", "i"}:
            return answer


def _interactive_note():
    while True:
        answer = input("Erase annotation? [Y|n] ").lower()
        if answer in {"", "y", "n"}:
            return "y" if answer in {"", "y"} else "n"


def clean_content(content, *, process_changes, process_notes, reject_changes, interactive=False):
    def clean(text):
        result = []
        position = 0
        while position < len(text):
            if text[position] == "%" and not _is_escaped(text, position):
                newline = text.find("\n", position)
                end = len(text) if newline == -1 else newline + 1
                result.append(text[position:end])
                position = end
                continue

            match = COMMAND_RE.match(text, position) if text[position] == "\\" else None
            if match is None:
                result.append(text[position])
                position += 1
                continue

            parsed = _parse_command(text, match)
            if parsed is None:
                result.append(match.group(0))
                position = match.end()
                continue

            command, args, first_start, end = parsed
            arguments = [clean(text[start + 1:finish]) for start, finish in args]

            if command in {"annote", "note"} and process_notes:
                answer = _interactive_note() if interactive else "y"
                if command == "annote" and answer == "n":
                    result.append(text[position:end])
                elif command == "annote":
                    result.append(arguments[0])
                elif answer == "n":
                    result.append(text[position:end])
                # A note is omitted when annotations are being removed.
            elif command in {"add", "remove", "change"} and process_changes:
                answer = _interactive_change() if interactive else ("r" if reject_changes else "a")
                if answer == "i":
                    result.append(text[position:end])
                elif command == "add":
                    result.append(arguments[0] if answer == "a" else "")
                elif command == "remove":
                    result.append("" if answer == "a" else arguments[0])
                else:
                    result.append(arguments[1] if answer == "a" else arguments[0])
            else:
                result.append(text[position:first_start + 1] + "}".join(arguments) + "}")
            position = end
        return "".join(result)

    return clean(content)


def build_parser():
    parser = OptionParser()
    parser.add_option("", "--warranty", action="store_true", dest="warranty")
    parser.add_option("", "--conditions", action="store_true", dest="conditions")
    parser.add_option("", "--infile", dest="infile", default="-")
    parser.add_option("", "--outfile", dest="outfile", default="-")
    parser.add_option("-n", "--notes", action="store_true", dest="notes")
    parser.add_option("-c", "--changes", action="store_true", dest="changes")
    parser.add_option("-r", "--reject", action="store_true", dest="reject")
    parser.add_option("-i", "--interactive", action="store_true", dest="interactive")
    return parser


def main(argv=None):
    parser = build_parser()
    options, remaining = parser.parse_args(argv)
    if remaining:
        parser.error(f"argument not recognized: {remaining[0]}")
    if options.warranty:
        print("This program is distributed without warranty.", file=sys.stderr)
        return 0
    if options.conditions:
        print("This program is free software under the GPL.", file=sys.stderr)
        return 0

    infile = sys.stdin if options.infile == "-" else open(options.infile, encoding="utf-8")
    outfile = sys.stdout if options.outfile == "-" else open(options.outfile, "w", encoding="utf-8")
    try:
        content = infile.read()
        cleaned = clean_content(
            content,
            process_changes=bool(options.changes),
            process_notes=bool(options.notes),
            reject_changes=bool(options.reject),
            interactive=bool(options.interactive),
        )
        outfile.write(cleaned)
    except (OSError, UnicodeError) as error:
        print(f"Unable to clean file: {error}", file=sys.stderr)
        return 1
    finally:
        if infile is not sys.stdin:
            infile.close()
        if outfile is not sys.stdout:
            outfile.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
