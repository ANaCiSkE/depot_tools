# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Top-level presubmit script for depot tools.

See http://dev.chromium.org/developers/how-tos/depottools/presubmit-scripts for
details on the presubmit API built into depot_tools.
"""

import fnmatch
import os


def DepotToolsPylint(input_api, output_api):
  """Gather all the pylint logic into one place to make it self-contained."""
  white_list = [
    r'^[^/]*\.py$',
    r'^testing_support/[^/]*\.py$',
    r'^tests/[^/]*\.py$',
    r'^recipe_modules/.*\.py$',  # Allow recursive search in recipe modules.
  ]
  black_list = list(input_api.DEFAULT_BLACK_LIST)
  if os.path.exists('.gitignore'):
    with open('.gitignore') as fh:
      lines = [l.strip() for l in fh.readlines()]
      black_list.extend([fnmatch.translate(l) for l in lines if
                         l and not l.startswith('#')])
  if os.path.exists('.git/info/exclude'):
    with open('.git/info/exclude') as fh:
      lines = [l.strip() for l in fh.readlines()]
      black_list.extend([fnmatch.translate(l) for l in lines if
                         l and not l.startswith('#')])
  disabled_warnings = [
    'R0401',  # Cyclic import
    'W0613',  # Unused argument
  ]
  return input_api.canned_checks.GetPylint(
      input_api,
      output_api,
      white_list=white_list,
      black_list=black_list,
      disabled_warnings=disabled_warnings)


def CommonChecks(input_api, output_api, tests_to_black_list):
  results = []
  results.extend(input_api.canned_checks.CheckOwners(input_api, output_api))
  # TODO(maruel): Make sure at least one file is modified first.
  # TODO(maruel): If only tests are modified, only run them.
  tests = DepotToolsPylint(input_api, output_api)
  unit_tests = input_api.canned_checks.GetUnitTestsInDirectory(
      input_api,
      output_api,
      'tests',
      whitelist=[r'.*test\.py$'],
      blacklist=tests_to_black_list)
  if not input_api.platform.startswith(('cygwin', 'win32')):
    tests.extend(unit_tests)
  else:
    print('Warning: not running unit tests on Windows')

  # Validate CIPD manifests.
  root = input_api.PresubmitLocalPath()
  rel_file = lambda rel: input_api.os_path.join(root, rel)
  for path in (
      ('cipd_manifest.txt',),
      ('bootstrap', 'win', 'manifest.txt'),
      ('bootstrap', 'win', 'manifest_bleeding_edge.txt'),
      ):
    tests.append(input_api.canned_checks.CheckCIPDManifest(
        input_api, output_api, path=rel_file(input_api.os_path.join(*path))))
  tests.append(input_api.canned_checks.CheckCIPDManifest(
      input_api, output_api, content='\n'.join([
        '$VerifiedPlatform linux-386 linux-amd64 linux-arm64 linux-armv6l ',
        '$VerifiedPlatform linux-mips64',
        '$VerifiedPlatform linux-ppc64 linux-ppc64le linux-s390x',
        '$VerifiedPlatform mac-amd64',
        '$VerifiedPlatform windows-386 windows-amd64',
        '',
        ('infra/tools/cipd/${platform} '+
         input_api.ReadFile(rel_file('cipd_client_version'))),
      ])))

  results.extend(input_api.RunTests(tests))
  return results


def CheckChangeOnUpload(input_api, output_api):
  # Do not run integration tests on upload since they are way too slow.
  tests_to_black_list = [
      r'^checkout_test\.py$',
      r'^gclient_smoketest\.py$',
      r'^scm_unittest\.py$',
      r'^subprocess2_test\.py$',
    ]
  return CommonChecks(input_api, output_api, tests_to_black_list)


def CheckChangeOnCommit(input_api, output_api):
  output = []
  output.extend(CommonChecks(input_api, output_api, []))
  output.extend(input_api.canned_checks.CheckDoNotSubmit(
      input_api,
      output_api))
  return output
