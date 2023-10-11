#!/usr/bin/env python3
# Copyright (c) 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import multiprocessing
import os
import os.path
import io
import sys
import unittest
import contextlib
from unittest import mock

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import autoninja
from testing_support import trial_dir


def write(filename, content):
    """Writes the content of a file and create the directories as needed."""
    filename = os.path.abspath(filename)
    dirname = os.path.dirname(filename)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    with open(filename, 'w') as f:
        f.write(content)


class AutoninjaTest(trial_dir.TestCase):
    def setUp(self):
        super(AutoninjaTest, self).setUp()
        self.previous_dir = os.getcwd()
        os.chdir(self.root_dir)

    def tearDown(self):
        os.chdir(self.previous_dir)
        super(AutoninjaTest, self).tearDown()

    def test_autoninja(self):
        autoninja.main([])

    def test_autoninja_goma(self):
        with mock.patch(
                'subprocess.call',
                return_value=0) as mock_call, mock.patch.dict(
                    os.environ,
                    {"GOMA_DIR": os.path.join(self.root_dir, 'goma_dir')}):
            out_dir = os.path.join('out', 'dir')
            write(os.path.join(out_dir, 'args.gn'), 'use_goma=true')
            write(
                os.path.join(
                    'goma_dir', 'gomacc.exe'
                    if sys.platform.startswith('win') else 'gomacc'), 'content')
            args = autoninja.main(['autoninja.py', '-C', out_dir])
            mock_call.assert_called_once()

        self.assertIn('-j', args)
        parallel_j = int(args[args.index('-j') + 1])
        self.assertGreater(parallel_j, multiprocessing.cpu_count() * 2)
        self.assertIn(os.path.join(autoninja.SCRIPT_DIR, 'ninja.py'), args)

    def test_autoninja_reclient(self):
        out_dir = os.path.join('out', 'dir')
        write(os.path.join(out_dir, 'args.gn'), 'use_remoteexec=true')
        write(os.path.join('buildtools', 'reclient_cfgs', 'reproxy.cfg'),
              'RBE_v=2')
        write(os.path.join('buildtools', 'reclient', 'version.txt'), '0.0')

        args = autoninja.main(['autoninja.py', '-C', out_dir])

        self.assertIn('-j', args)
        parallel_j = int(args[args.index('-j') + 1])
        self.assertGreater(parallel_j, multiprocessing.cpu_count() * 2)
        self.assertIn(os.path.join(autoninja.SCRIPT_DIR, 'ninja_reclient.py'),
                      args)

    def test_gn_lines(self):
        out_dir = os.path.join('out', 'dir')
        # Make sure nested import directives work. This is based on the
        # reclient test.
        write(os.path.join(out_dir, 'args.gn'), 'import("//out/common.gni")')
        write(os.path.join('out', 'common.gni'), 'import("common_2.gni")')
        write(os.path.join('out', 'common_2.gni'), 'use_remoteexec=true')

        lines = list(
            autoninja._gn_lines(out_dir, os.path.join(out_dir, 'args.gn')))

        # The test will only pass if both imports work and
        # 'use_remoteexec=true' is seen.
        self.assertListEqual(lines, [
            'use_remoteexec=true',
        ])

    @mock.patch('sys.platform', 'win32')
    def test_print_cmd_windows(self):
        args = [
            'C:\\Program Files\\Python 3\\bin\\python3.exe', 'ninja.py', '-C',
            'out\\direc tory\\',
            '../../base/types/expected_macros_unittest.cc^', '-j', '140'
        ]
        with contextlib.redirect_stderr(io.StringIO()) as f:
            autoninja._print_cmd(args)
            self.assertEqual(
                f.getvalue(),
                '"C:\\Program Files\\Python 3\\bin\\python3.exe" ninja.py -C ' +
                '"out\\direc tory\\" ' +
                '../../base/types/expected_macros_unittest.cc^^ -j 140\n')

    @mock.patch('sys.platform', 'linux')
    def test_print_cmd_linux(self):
        args = [
            '/home/user name/bin/python3', 'ninja.py', '-C', 'out/direc tory/',
            '../../base/types/expected_macros_unittest.cc^', '-j', '140'
        ]
        with contextlib.redirect_stderr(io.StringIO()) as f:
            autoninja._print_cmd(args)
            self.assertEqual(
                f.getvalue(),
                "'/home/user name/bin/python3' ninja.py -C 'out/direc tory/' " +
                "'../../base/types/expected_macros_unittest.cc^' -j 140\n")


if __name__ == '__main__':
    unittest.main()
