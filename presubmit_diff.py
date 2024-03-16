#!/usr/bin/env python3
# Copyright (c) 2024 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Tool for generating a unified git diff outside of a git workspace.

This is intended as a preprocessor for presubmit_support.py.
"""
from __future__ import annotations

import argparse
import base64
import os
import sys

import gclient_utils
from gerrit_util import CreateHttpConn, ReadHttpResponse
import subprocess2

DEV_NULL = "/dev/null"


def fetch_content(host: str, repo: str, ref: str, file: str) -> str:
    """Fetches the content of a file from Gitiles.

    If the file does not exist at the commit, it returns an empty string.

    Args:
      host: Gerrit host.
      repo: Gerrit repo.
      ref: Gerrit commit.
      file: Path of file to fetch.

    Returns:
        A string containing the content of the file at the commit, or an empty
        string if the file does not exist at the commit.
    """
    conn = CreateHttpConn(f"{host}.googlesource.com",
                          f"{repo}/+show/{ref}/{file}?format=text")
    response = ReadHttpResponse(conn, accept_statuses=[200, 404])
    return base64.b64decode(response.read()).decode("utf-8")


def git_diff(src: str | None, dest: str | None) -> str:
    """Returns the result of `git diff --no-index` between two paths.

    If a path is not specified, the diff is against /dev/null. At least one of
    src or dest must be specified.

    Args:
      src: Source path.
      dest: Destination path.

    Returns:
        A string containing the git diff.

    Raises:
        ValueError: If neither src nor dest are specified.
    """
    if not src and not dest:
        raise ValueError("Must specify either src or dest.")
    return subprocess2.capture(
        ["git", "diff", "--no-index", "--", src or DEV_NULL, dest
         or DEV_NULL]).decode("utf-8")


def create_diffs(host: str, repo: str, ref: str, root: str,
                 files: list[str]) -> dict[str, str]:
    """Calculates diffs of files in a directory against a commit.

    Args:
      host: Gerrit host.
      repo: Gerrit repo.
      ref: Gerrit commit.
      root: Path of local directory containing modified files.
      files: List of file paths relative to root.

    Returns:
        A dict mapping file paths to diffs.
    """
    diffs = {}
    with gclient_utils.temporary_directory() as tmp_root:
        # TODO(gavinmak): Parallelize fetching content.
        for file in files:
            new_file = os.path.join(root, file)
            if not os.path.exists(new_file):
                new_file = None

            old_file = None
            old_content = fetch_content(host, repo, ref, file)
            if old_content:
                old_file = os.path.join(tmp_root, file)
                os.makedirs(os.path.dirname(old_file), exist_ok=True)
                with open(old_file, "w") as f:
                    f.write(old_content)

            diff = git_diff(old_file, new_file)
            if not diff:
                diffs[file] = ""
                continue

            # Adjust paths in the diff header so they're relative to the root.
            header, body = diff.split("@@", maxsplit=1)
            header = header.replace(root.rstrip("/"), "")
            header = header.replace(tmp_root.rstrip("/"), "")
            diffs[file] = header + "@@" + body

    return diffs


def main(argv):
    parser = argparse.ArgumentParser(
        usage="%(prog)s [options] <files...>",
        description="Makes a unified git diff against a Gerrit commit.",
    )
    parser.add_argument("--output", help="File to write the diff to.")
    parser.add_argument("--host", required=True, help="Gerrit host.")
    parser.add_argument("--repo", required=True, help="Gerrit repo.")
    parser.add_argument("--ref",
                        required=True,
                        help="Gerrit ref to diff against.")
    parser.add_argument("--root",
                        required=True,
                        help="Folder containing modified files.")
    parser.add_argument(
        "files",
        nargs="+",
        help="List of changed files. Paths are relative to the repo root.",
    )
    options = parser.parse_args(argv)

    diffs = create_diffs(options.host, options.repo, options.ref, options.root,
                         options.files)

    unified_diff = "\n".join([d for d in diffs.values() if d])
    if options.output:
        with open(options.output, "w") as f:
            f.write(unified_diff)
    else:
        print(unified_diff)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
