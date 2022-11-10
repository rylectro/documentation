#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import glob
from collections import OrderedDict
import logging
import sys
from pathlib import Path


class Formatter(logging.Formatter):
    def format(self, record):
        reset = "\x1b[0m"
        color = {
            logging.INFO: 32,
            logging.WARNING: 33,
            logging.ERROR: 31,
            logging.FATAL: 31,
            logging.DEBUG: 36
        }.get(record.levelno, 0)
        self._style._fmt = f"\x1b[{color}m%(levelname)s:{reset} %(message)s"
        return super().format(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# log colored streams
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(Formatter())
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

# log only debug messages to file in ci
if os.getenv("CI_COMMIT_REF_NAME"):
    file_handler = logging.FileHandler('format_link.debug.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
    logger.addHandler(file_handler)


class Node:
    # TODO: cleanup interactions and instance variables
    __slots__ = ['name', 'children', 'parent', 'lines', 'modified_lines', 'start_line', 'end_line', 'start', 'end',
                 'ignore', 'is_closing_shortcode']

    def __init__(self, name, ignore=False):
        self.name = name
        self.children = []
        self.parent = None
        self.lines = []
        self.modified_lines = []
        self.start_line = 0
        self.end_line = 0
        self.start = 0
        self.end = 0
        self.ignore = ignore
        self.is_closing_shortcode = False

    def add(self, child):
        child.parent = self
        self.children.append(child)

    def push_line(self, line):
        self.lines.append(line)

    def pop_line(self):
        return self.lines.pop()

    def __repr__(self):
        return repr(f"<{self.name}>")

    def __eq__(self, other):
        return self.name == other.name


def parse_file(file):
    """
    Goes through a file and parses it into different sections. Those sections are a list of lines and are put within an Array.
    The first item of the Array is the main section, all other item if any are sub sections, a.k.a tabs within the page.

    :param file: file to break down into sections.
    :return root: Root node from parsing
    """
    root = Node("root")
    current_node = root

    open_tag_regex = r"{{[<|%]\s+([A-Za-z0-9-_]+)(.*)\s*[%|>]}}"
    closed_tag_regex = r"{{[<|%]\s+/([A-Za-z0-9-_]+)(.*)\s*[%|>]}}"
    ignore_shortcodes = ('code-block', )

    with open(file, 'r', encoding='utf-8') as f:
        new_line_number = 0
        for line_number, line in enumerate(f):

            # store the current line in the current node
            current_node.push_line(line)
            new_node = None

            # is this an opening triple backtick code block
            tickmatches = list(re.finditer("^\s*```", line, re.MULTILINE))
            if tickmatches and current_node.name != "```":
                current_node.start = 0
                new_node = Node("```", True)

            # find new open shortcode tags and create a node
            if not current_node.ignore:
                matches = re.finditer(open_tag_regex, line, re.MULTILINE)
                for matchNum, match in enumerate(matches, start=1):
                    tag_name, current_node.start, current_node.end = match.group(1), match.start(0), match.end()
                    new_node = Node(tag_name, tag_name in ignore_shortcodes)

            # if we entered a new node lets set it as the current
            if new_node:
                current_node.add(new_node)
                current_node = new_node
                current_node.push_line(line)
                current_node.start_line = new_line_number
                new_line_number = 0

            # is this a closing triple backtick code block
            if current_node.name == "```" and tickmatches and not new_node:
                current_node.is_closing_shortcode = True
                current_node.end = 0
                current_node.end_line = current_node.start_line + 1
                new_line_number = current_node.end_line
                current_node = current_node.parent
                current_node.push_line(line)

            # check for closing node and return up the chain to the parent node for next iteration
            matches = re.finditer(closed_tag_regex, line, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                tag_name, current_node.end = match.group(1), match.end(0)
                if tag_name == current_node.name and current_node.parent:
                    current_node.is_closing_shortcode = True
                    # if we closed on the same line we don't want to add the line again and end_line is the same
                    is_same_line = new_line_number == 0
                    current_node.end_line = current_node.start_line if is_same_line else current_node.start_line + 1
                    new_line_number = current_node.end_line
                    current_node = current_node.parent
                    if not is_same_line:
                        current_node.push_line(line)

            new_line_number += 1

    # any node that is false still is a one liner
    adjust_one_liner_shortcodes(root)

    if not root.lines:
        raise ValueError

    return root


def adjust_one_liner_shortcodes(node):
    """
    As we can't find a closing tag for a one liner everything becomes nested under this shortcode
    which isn't accurate. So lets readjust once we know
    @param node: node
    """
    for i, n in enumerate(node.children):
        if not n.is_closing_shortcode:
            n.end_line = n.start_line
            # take nodes children and put it adjacent to node
            r, node.children[i].children[:] = n.children[:], []
            node.children += r
            for d in r:
                # adjust child line offsets
                d.start_line = d.start_line + n.start_line
                d.end_line = d.end_line + n.start_line
                # re-parent
                d.parent = node
            # move lines of text to parent
            foo, node.children[i].lines = n.lines[1:], n.lines[0:1]
            node.lines += foo
        adjust_one_liner_shortcodes(n)


def process_nodes(node):
    """
    TODO: this function is way too big
    Takes the parsed node structure and processes the link formatting we desire throughout each node.
    @param node: node
    """
    if node.ignore or not node.is_closing_shortcode:
        # ignored nodes we still need to return its original text or its removed
        node.modified_lines = node.lines
    else:
        content = ''.join(node.lines)

        # extract footer reference links
        refs = {}
        ref_nums = []
        matches = re.finditer(r"^\s*\[(\d*?)\]: (\S*)", content, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            ref_num, ref_link = int(match.group(1)), match.group(2)
            # alert on duplicate reference numbers
            if ref_num in ref_nums:
                logger.warning(f'{node} has duplicated reference index numbers (Skipping Format):\n\t[{ref_num}]: {ref_link}\n\t[{ref_num}]: {refs[ref_num]}')
                raise SystemExit
            else:
                refs[ref_num] = ref_link
                ref_nums.append(ref_num)
        all_references = OrderedDict(sorted(refs.items()))

        # if we have [foo][1] in a section but no footer links its referencing
        # it's likely the user put the footer link in the root of the document
        # TODO: as well as this warning we should attempt to source the link from the root of document
        if not all_references and re.search(r"\[.*?\]\[(?![#?])(\S*?)\]", content) is not None:
            matches = re.finditer(r"\[.*?\]\[(?![#?])(\S*?)\]", content, re.MULTILINE)
            logger.warning(f"{node} has no footer links but references them:\n" + "\n".join([f"\t{match.group(0)}" for match in matches]))

        # remove footer reference links
        # content = re.sub(r"^\s*\[(\d*?)\]: (\S*)", "", content, 0, re.MULTILINE)
        start_line, end_line = 0, 0
        for ln, line in enumerate(node.lines):
            if re.search(r"^\s*\[(\d*?)\]: (\S*)", line):
                if start_line:
                    end_line = ln + 1
                else:
                    start_line = ln

        # inline existing reference links
        for reference_index, reference_val in all_references.items():
            current_link = f'][{reference_index}]'
            content = content.replace(current_link, f']({reference_val})')

        # extract all inlined links it can find and try and maintain their number if we can so there is less of a diff
        all_references_flipped = {}
        for x, y in all_references.items():
            if y not in all_references_flipped.keys():
                all_references_flipped[y] = x
        refs = {}
        matches = re.finditer(r"\[.*?\]\((?![#?])(\S*?)\)", content, re.MULTILINE)
        for match in matches:
            inline_ref_link = match.group(1)
            inline_ref_num = all_references_flipped.get(inline_ref_link, None)
            if inline_ref_num:
                refs[inline_ref_num] = inline_ref_link
        inline_refs = OrderedDict(sorted(refs.items()))

        # re-order numbers where needed
        #for index, val in inline_refs.items():
        from itertools import groupby
        from operator import itemgetter
        data = inline_refs.keys()
        new = {}
        for k, g in groupby(enumerate(data), lambda ix : ix[0] - ix[1]):
            #print(list(map(itemgetter(1), g)))
            #print(list(g))
            for x in g:
                new[x[0] + 1] = inline_refs[x[1]]
        #print(new)
        inline_refs = OrderedDict(sorted(new.items()))


        # create reference footer section again
        for reference_index, reference_val in inline_refs.items():
            link_to_reference = '](' + str(reference_val) + ')'
            # i is incremented by one in order to start references indexes at 1
            content = content.replace(link_to_reference, '][' + str(reference_index) + ']')

        # assign completed content changes
        # splitlines splits on other weird characters that are sometimes copied and pasted in md files, lets remove
        # https://docs.python.org/3/library/stdtypes.html#str.splitlines
        # TODO: better way to do this?
        cleaned_content = content.replace("\u2029", "") # Paragraph Separator
        cleaned_content = cleaned_content.replace("\u2028", "") # Line Separator
        cleaned_content = cleaned_content.replace("\x85", "") # Next Line (C1 Control Code)
        cleaned_content = cleaned_content.replace("\x1e", "") # Record Separator
        cleaned_content = cleaned_content.replace("\x1d", "") # Group Separator
        cleaned_content = cleaned_content.replace("\x1c", "") # File Separator
        cleaned_content = cleaned_content.replace("\x0c", "") # Form Feed
        cleaned_content = cleaned_content.replace("\x0b", "") # Line Tabulation
        node.modified_lines = cleaned_content.splitlines(keepends=True)

        if not start_line:
            start_line = len(node.modified_lines) - 1 if node.parent else len(node.modified_lines)
            end_line = start_line
        if end_line == 0:
            end_line = start_line + 1
        node.modified_lines[start_line:end_line] = [f"[{i}]: {link}\n" for i, link in inline_refs.items()]

    # process children
    for child in node.children:
        process_nodes(child)


def assemble_nodes(node):
    """
    Takes a node and assembles the text contents of itself and children nodes into a final string
    This allows us to modify each node individually and inject it into the parent.
    we process in reverse so that we don't introduce offsets
    @param node: node
    @return: list of strings
    """
    output = [] + node.modified_lines
    for child in reversed(node.children):
        child_output = assemble_nodes(child)
        if child.start_line == child.end_line:
            # single line shortcode
            line = output[child.start_line]
            if child.is_closing_shortcode:
                if child_output:
                    output[child.start_line] = line[:child.start] + child_output + line[child.end:]
                else:
                    # lets just use the full line for now
                    # TODO: rebuild from char start to char end like above for interspersed shortcode amongst text
                    #       e.g something like line[:child.start] + line[child.end:] should work but doesn't
                    output[child.start_line] = line
            else:
                #output[child.start_line] = line[child.start:child.end]
                output[child.start_line] = line

        else:
            # multi line shortcode
            output[child.start_line:child.end_line + 1] = child_output
    return output


def init_args():
    """
    Sets up argument parsing and returns the arguments
    :return: argparse values
    """
    parser = argparse.ArgumentParser(description='Format links in markdown file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f', '--file', action='store', default=None, dest='source', help='File to format link in reference')
    group.add_argument('-d', '--directory', action='store', default=None, dest='source', help='Directory to format link in reference for all markdown file')
    args = parser.parse_args()
    return args


def format_link_file(*args):
    """
    Kept for legacy usage in other scripts
    Takes a filepath and parses/processes and returns the string text
    @param args: filepath, (we don't care about other args passed from legacy scripts)
    @return: string of changed file
    """
    if len(args) == 0:
        raise ValueError("Filepath is required argument")
    filepath = args[0]
    # parse the file shortcode hierarchy
    root = parse_file(filepath)
    # process each node text contents, each node will store original and modified content
    process_nodes(root)
    # reassemble the file with the changes we have made
    contents_list = assemble_nodes(root)
    reassembled_file = ''.join(contents_list)
    return reassembled_file


def main():
    """
    Entry point taking args and processing directory of files or file
    and responsible for writing the new contents back out to filesystem
    """
    options = init_args()
    if options.source:
        source_path = Path(options.source)
        files = [source_path] if source_path.is_file() else glob.iglob(str(source_path / '**/*.md'), recursive=True)
        if not list(files):
            logger.warning('No files found to process')
        for filepath in files:
            logger.info(f'Formating file {filepath}')
            final_text = format_link_file(filepath)
            # overwrite the original file with our changes
            with open(filepath, 'w') as final_file:
                final_file.write(final_text)


if __name__ == '__main__':
    main()

