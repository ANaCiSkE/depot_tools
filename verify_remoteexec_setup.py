#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""This script runs some basic verification checks to see if your
machine and output directory are setup correctly to use remote
execution in your chrome build."""

import argparse
import os
import re
import sys

import gclient_paths
import reclient_helper
import subprocess2


def main(out_dir):
    reclient_bin_dir = reclient_helper.find_reclient_bin_dir()
    if reclient_bin_dir is None:
        print(
            "ERROR: Could not find reclient binaries, if you are a googler " +
            "make sure to set `\"download_remoteexec_cfgs\":True` " +
            "in the \"custom_vars\" dict in `.gclient` and run `gclient sync`")
        return 1

    gn_args_path = os.path.join(out_dir, 'args.gn')
    if not os.path.exists(gn_args_path):
        print("ERROR: %s does not exist, make sure to run `gn gen -C %s`" %
              (gn_args_path, out_dir))
        return 1
    use_remoteexec = False
    with open(gn_args_path) as f:
        for line in f:
            line_without_comment = line.split('#')[0]
            if re.search(r'(^|\s)use_remoteexec\s*=\s*true($|\s)',
                         line_without_comment):
                use_remoteexec = True
    if not use_remoteexec:
        print(
            "Error: `use_remoteexec=true` not found in args.gn, " +
            "make sure to add `use_remoteexec=true` as a line directly into " +
            "the `args.gn` file. " +
            "Gn imports and conditionals are currently are not evaluated.")
        return 1

    cfg_file = subprocess2.check_output(
        ["gn", "args", "--short", "--list=rbe_py_cfg_file", "-C", out_dir],
        text=True)
    if "rbe_py_cfg_file = \"" not in cfg_file:
        print("ERROR: rewrapper cfg file not found. This could indicate " +
              "a problem with the `.gni` files in your build.")
    cfg_file = cfg_file[len("rbe_py_cfg_file = \""):-2]
    with reclient_helper.build_context(['', '-C', out_dir],
                                       'verify_remoteexec_setup') as ret_code:
        if ret_code:
            return ret_code
        try:
            reclient_helper.run([
                os.path.join(reclient_bin_dir,
                             'rewrapper' + gclient_paths.GetExeSuffix()),
                "--cfg=" + os.path.abspath(os.path.join(out_dir, cfg_file)),
                "--labels=type=tool", "--exec_strategy=remote", "--", "echo",
                "Hello World"
            ])
        except KeyboardInterrupt:
            return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ninja_out",
                        "-C",
                        required=True,
                        help="ninja out directory with `use_remoteexec=true`")
    args = parser.parse_args()
    sys.exit(main(args.ninja_out))
