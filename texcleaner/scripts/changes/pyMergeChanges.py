#!/usr/bin/env python3
# pyMergeChanges: merge commits made with the changes package.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2018 Yvon Cui.
# The original program is licensed under GPL-3.0-or-later.
#
# Modified in 2026 by Dan Shim and TeXCleaner contributors: replaced the
# line-oriented parser with recursive parsing for multiline/nested commands,
# added comment and escaped-brace handling, and improved validation/errors.
# This modified version remains GPL-3.0-or-later and is distributed without
# warranty; see the repository LICENSE file.

"""
Merge commits made with the changes.sty package into plain LaTeX text.

Usage: python pyMergeChanges.py [-arh] <input> <output>
  -a  accept added, deleted, and replaced text
  -r  reject added, deleted, and replaced text
  -h  remove highlights and comments
"""

import codecs
import re
import sys


COMMAND_RE = re.compile(r"\\(added|deleted|replaced|highlight|comment)(?![A-Za-z@])")


def _is_escaped(text, position):
    """Return whether the character at position is preceded by an odd slash count."""
    slashes = 0
    position -= 1
    while position >= 0 and text[position] == "\\":
        slashes += 1
        position -= 1
    return slashes % 2 == 1


def find_matching_brace(text, start):
    """Find a TeX argument's closing brace, respecting escaped braces/comments."""
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
    """Return (command, arguments, first_start, full_end) or None if malformed."""
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
    if match.group(1) == "replaced":
        second_start = first_end + 1
        while second_start < len(text) and text[second_start].isspace():
            second_start += 1
        second_end = find_matching_brace(text, second_start)
        if second_end == -1:
            return None
        args.append((second_start, second_end))
    return match.group(1), args, first_start, args[-1][1] + 1


def _ask_commit():
    while True:
        answer = input("[a]ccept or [r]eject or [k]eep or [b]reak ? ").lower()
        if answer in {"a", "r", "k", "b"}:
            return answer


def _ask_annotation():
    while True:
        answer = input("[r]emove or [k]eep or [b]reak ? ").lower()
        if answer in {"r", "k", "b"}:
            return answer


def clean_content(content, params):
    """Recursively clean changes commands while preserving ordinary LaTeX."""
    interactive = params == "i"
    accept = "a" in params
    reject = "r" in params
    remove_annotations = "h" in params

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
            argument = [clean(text[start + 1:finish]) for start, finish in args]

            if command in {"added", "deleted", "replaced"}:
                answer = _ask_commit() if interactive else ("a" if accept else "r" if reject else "k")
                if answer == "b":
                    result.append(text[position:end])
                elif command == "added":
                    result.append(argument[0] if answer == "a" else "" if answer == "r" else text[position:end])
                elif command == "deleted":
                    result.append("" if answer == "a" else argument[0] if answer == "r" else text[position:end])
                else:
                    result.append(argument[0] if answer == "a" else argument[1] if answer == "r" else text[position:end])
            else:
                answer = _ask_annotation() if interactive else ("r" if remove_annotations else "k")
                if answer == "r":
                    result.append(argument[0] if command == "highlight" else "")
                else:
                    result.append(text[position:first_start + 1] + argument[0] + "}")

            position = end
        return "".join(result)

    return clean(content)


def parse_param(parameter_string):
    if len(parameter_string) < 2 or parameter_string[0] != "-":
        raise ValueError("Options must start with '-'.")
    params = parameter_string[1:]
    if "a" in params and "r" in params:
        raise ValueError("You cannot accept and reject at the same time.")
    unknown = set(params) - {"a", "r", "h"}
    if unknown:
        raise ValueError(f"Unknown parameter: {sorted(unknown)[0]}")
    return params or "i"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 2:
        params, input_file, output_file = "i", argv[0], argv[1]
    elif len(argv) == 3:
        try:
            params = parse_param(argv[0])
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        input_file, output_file = argv[1:]
    else:
        print(__doc__)
        return 1

    if input_file == output_file:
        print("Input File and Output File must be different.", file=sys.stderr)
        return 1

    try:
        with codecs.open(input_file, mode="r", encoding="utf-8") as source:
            content = source.read()
        cleaned = clean_content(content, params)
        with codecs.open(output_file, mode="w", encoding="utf-8") as destination:
            destination.write(cleaned)
    except (OSError, UnicodeError) as error:
        print(f"Unable to clean file: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
