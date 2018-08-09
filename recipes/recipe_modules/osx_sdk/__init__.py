# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

DEPS = [
    'recipe_engine/cipd',
    'recipe_engine/context',
    'recipe_engine/json',
    'recipe_engine/path',
    'recipe_engine/platform',
    'recipe_engine/step',
]

from recipe_engine.recipe_api import Property
from recipe_engine.config import ConfigGroup, Single

PROPERTIES = {
  '$depot_tools/osx_sdk': Property(
    help='Properties specifically for the infra osx_sdk module.',
    param_name='sdk_properties',
    kind=ConfigGroup(
      # XCode build version number. Internally maps to an XCode build id like
      # '9c40b'. See api.py for known versions.
      sdk_version=Single(str),

      # The CIPD toolchain tool package and version
      toolchain_pkg=Single(str),
      toolchain_ver=Single(str),
    ), default={
      'sdk_version': '9c40b',

      'toolchain_pkg': 'infra/tools/mac_toolchain/${platform}',
      'toolchain_ver': 'git_revision:796d2b92cff93fc2059623ce0a66284373ceea0a',
    },
  )
}
