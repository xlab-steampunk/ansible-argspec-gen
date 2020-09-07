# -*- coding: utf-8 -*-
# Copyright: (c) 2020, XLAB Steampunk <steampunk@xlab.si>
#
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

import collections
import difflib
import re
import shutil
import sys
import textwrap

from ansible.module_utils.common import validation
from ansible.plugins.loader import fragment_loader
from ansible.utils import plugin_docs

import black


class ParseError(Exception):
    """ Exception indicating parse error. """


def get_module_docs(module):
    return plugin_docs.get_docstring(module, fragment_loader)[0]


def to_code(var_name, var_data, line_length):
    source = "{} = {}".format(var_name, repr(var_data))
    mode = black.Mode(
        target_versions={black.TargetVersion.PY27}, line_length=line_length,
    )
    return black.format_str(source, mode=mode)


def update_module(old_lines, marker, params, line_length):
    # Copy prefix
    for cur_line in range(len(old_lines)):
        if old_lines[cur_line].strip() == marker:
            indent = old_lines[cur_line].find("#")
            new_lines = old_lines[:cur_line + 1]  # Include marker
            break
    else:
        raise ParseError("Module does not contain a marker pair.")

    # Insert module parameters
    for k, v in params.items():
        code = to_code(k, v, line_length - indent)
        new_lines.extend(
            textwrap.indent(code, " " * indent).splitlines(keepends=True),
        )

    # Skip over to the second marker occurence
    for cur_line in range(cur_line + 1, len(old_lines)):
        if old_lines[cur_line].strip() == marker:
            break
    else:
        raise ParseError("Module does not contain a marker pair.")

    # Copy the rest of the file
    new_lines.extend(old_lines[cur_line:])

    return new_lines


def option_to_spec(option):
    DESC_KEYS = (
        "aliases", "choices", "default", "elements", "required", "type",
    )
    argspec_opt = {
        name: option[name] for name in DESC_KEYS if name in option
    }
    if "suboptions" in option:
        argspec_opt["options"] = options_to_spec(option["suboptions"])
        if any(
                "default" in o or "fallback" in o
                for o in argspec_opt["options"].values()
        ):
            argspec_opt["apply_defaults"] = True
    return argspec_opt


def options_to_spec(options):
    return {n: option_to_spec(o) for n, o in sorted(options.items())}


def options_to_required_if(options):
    # Currently, we do not recurse into suboptions because required_if is not
    # that powerfull.

    # Sample requirement:
    #   requirements[("state", "present")] == ["opt1", "opt2"]
    requirements = collections.defaultdict(list)

    # Match things like "required if I(state) is C(present)"
    pattern = re.compile(r"[Rr]equired if I\(([^\)]+)\) is C\(([^\)]+)\)")

    for name, data in options.items():
        for desc in data["description"]:
            match = pattern.search(desc)
            if not match:
                continue

            # Convert extracted value to the right type.
            typ = options[match[1]].get("type", "str")
            val = getattr(validation, "check_type_" + typ)(match[2])
            requirements[(match[1], val)].append(name)

    # Convert
    #   {
    #       ("state", "present"): ["opt1", "opt2"],
    #       ("n",     "v"      ): ["r"           ],
    #   }
    # to
    #   [
    #       ("n"    , "v"      , ("r",          )),
    #       ("state", "present", ("opt1", "opt2")),
    #   ]
    return [(n, v, tuple(r)) for (n, v), r in sorted(requirements.items())]


def options_to_mutually_exclusive(options):
    # Currently, we do not recurse into suboptions because mutually_exclusive
    # is not that powerfull.

    # Sample requirement:
    #   restrictions == {("opt1", "opt2", "opt3"), ("opt1", "opt4")}
    restrictions = set()

    # Pattern for option parsing
    pattern = re.compile(r"I\(([^\)]+)\)")

    for name, data in options.items():
        for desc in data["description"]:
            # Match things like
            #   "mutually exclusive with I(opt1), I(opt2), and I(opt3)"
            mut_pos = desc.find("utually exclusive with")  # We left out Mm ;)
            if mut_pos < 0:
                # No match
                continue

            restrictions.add(
                tuple(sorted(pattern.findall(desc, mut_pos + 23) + [name])),
            )

    return sorted(restrictions)


def load_parameters(path):
    docs = get_module_docs(path)
    params = dict(
        argument_spec=options_to_spec(docs["options"]),
        required_if=options_to_required_if(docs["options"]),
        mutually_exclusive=options_to_mutually_exclusive(docs["options"]),
    )
    return {k: v for k, v in params.items() if v}


def process_module(path, marker, show_diff, dry_run, line_length):
    params = load_parameters(path)
    with open(path, "r") as fd:
        old_lines = fd.readlines()
    new_lines = update_module(old_lines, marker, params, line_length)

    if show_diff:
        sys.stdout.writelines(difflib.unified_diff(
            old_lines, new_lines, fromfile=path + ".old", tofile=path + ".new",
        ))

    changed = old_lines != new_lines
    if not dry_run and changed:
        with open(path, "w") as fd:
            fd.writelines(new_lines)

    return changed
