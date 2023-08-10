#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from typing import Dict, Union


class ValidationResult(object):
  """Base class for validation issues."""
  def __init__(self, message: str, fatal: bool, **tags: Dict[str, str]):
    self._fatal = fatal
    self._message = message
    self._tags = tags

  def __str__(self) -> str:
    prefix = "ERROR" if self._fatal else "[non-fatal]"
    return f"{prefix} - {self._message}"

  def __repr__(self) -> str:
    return str(self)

  def is_fatal(self) -> bool:
    return self._fatal

  def get_tag(self, tag: str) -> Union[str, None]:
    return self._tags.get(tag)

  def get_all_tags(self) -> Dict[str, str]:
    return dict(self._tags)

  def get_message(self):
    return self._message


class ValidationError(ValidationResult):
  """Fatal validation issue. Presubmit should fail."""
  def __init__(self, message: str, **tags: Dict[str, str]):
    super().__init__(message=message, fatal=True, **tags)


class ValidationWarning(ValidationResult):
  """Non-fatal validation issue. Presubmit should pass."""
  def __init__(self, message: str, **tags: Dict[str, str]):
    super().__init__(message=message, fatal=False, **tags)
