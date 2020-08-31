# -*- coding: utf-8 -*-
# Copyright: (c) 2020, XLAB Steampunk <steampunk@xlab.si>
#
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

import argparse
import sys

from . import utils


class ArgParser(argparse.ArgumentParser):
    """
    Argument parser that displays help on error
    """

    def error(self, message):
        sys.stderr.write("error: {}\n".format(message))
        self.print_help()
        sys.exit(2)


def create_argument_parser():
    parser = ArgParser(
        description="Module argument spec generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-m", "--marker", type=str, default="# AUTOMATIC MODULE ARGUMENTS",
        help="Marker that informs the tool where to insert the code",
    )
    parser.add_argument(
        "-d", "--diff", action="store_true",
        help="Report changes made to module",
    )
    parser.add_argument(
        "-r", "--dry-run", action="store_true",
        help="Only perform update simulation",
    )
    parser.add_argument(
        "-l", "--line-length", type=int, default=79,
        help="Limit the generated code's width",
    )
    parser.add_argument(
        "module", nargs="+", help="Module to update argument spec in",
    )
    return parser


def main():
    args = create_argument_parser().parse_args()

    changed = False
    for m in args.module:
        try:
            changed = utils.process_module(
                m, args.marker, args.diff, args.dry_run, args.line_length,
            ) or changed
        except utils.ParseError as e:
            print("Error processing {}: {}".format(m, e), file=sys.stderr)
            return 2

    return int(changed)
