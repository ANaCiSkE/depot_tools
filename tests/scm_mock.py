# Copyright (c) 2024 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import threading

from typing import Dict, List, Optional
from unittest import mock
import unittest

# This is to be able to import scm from the root of the repo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scm


def GIT(test: unittest.TestCase,
        config: Optional[Dict[str, List[str]]] = None,
        branchref: Optional[str] = None):
    """Installs fakes/mocks for scm.GIT so that:

      * Initial git config (local scope) is set to `config`.
      * GetBranch will just return a fake branchname starting with the value of
        branchref.
      * git_new_branch.create_new_branch will be mocked to update the value
        returned by GetBranch.

    NOTE: The dependency on git_new_branch.create_new_branch seems pretty
    circular - this functionality should probably move to scm.GIT?
    """
    # TODO - remove `config` - have callers just directly call SetConfig with
    # whatever config state they need.
    # TODO - add `system_config` - this will be configuration which exists at
    # the 'system installation' level and is immutable.

    if config:
        config = {
            scm.canonicalize_git_config_key(k): v
            for k, v in config.items()
        }

    _branchref = [branchref or 'refs/heads/main']

    global_lock = threading.Lock()
    global_state = {}

    def _newBranch(branchref):
        _branchref[0] = branchref

    patches: List[mock._patch] = [
        mock.patch('scm.GIT._new_config_state',
                   side_effect=lambda _: scm.GitConfigStateTest(
                       global_lock, global_state, local_state=config)),
        mock.patch('scm.GIT.GetBranchRef', side_effect=lambda _: _branchref[0]),
        mock.patch('git_new_branch.create_new_branch', side_effect=_newBranch)
    ]

    for p in patches:
        p.start()
        test.addCleanup(p.stop)

    test.addCleanup(scm.GIT.drop_config_cache)
