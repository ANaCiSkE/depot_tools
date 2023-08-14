#!/usr/bin/env vpython3
# Copyright (c) 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
from typing import List
import unittest

_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
_ROOT_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))

sys.path.insert(0, _ROOT_DIR)

import metadata.fields.types as field_types
import metadata.fields.known as known_fields
import metadata.validation_result as vr


class FieldValidationTest(unittest.TestCase):
  def _run_field_validation(self,
                            field: field_types.MetadataField,
                            valid_values: List[str],
                            error_values: List[str],
                            warning_values: List[str] = []):
    """Helper to run a field's validation for different values."""
    for value in valid_values:
      self.assertIsNone(field.validate(value))

    for value in error_values:
      self.assertIsInstance(field.validate(value), vr.ValidationError)

    for value in warning_values:
      self.assertIsInstance(field.validate(value), vr.ValidationWarning)

  def test_freeform_text_validation(self):
    # Check validation of a freeform text field that should be on one line.
    self._run_field_validation(
        field=field_types.FreeformTextField("Freeform single", one_liner=True),
        valid_values=["Text on single line", "a", "1"],
        error_values=["", "\n", " "],
    )

    # Check validation of a freeform text field that can span multiple lines.
    self._run_field_validation(
        field=field_types.FreeformTextField("Freeform multi", one_liner=False),
        valid_values=[
            "This is text spanning multiple lines:\n"
            "    * with this point\n"
            "    * and this other point",
            "Text on single line",
            "a",
            "1",
        ],
        error_values=["", "\n", " "],
    )

  def test_yes_no_field_validation(self):
    self._run_field_validation(
        field=field_types.YesNoField("Yes/No test"),
        valid_values=["yes", "no", "No", "YES"],
        error_values=["", "\n", "Probably yes"],
        warning_values=["Yes?", "not"],
    )

  def test_date_validation(self):
    self._run_field_validation(
        field=known_fields.DATE,
        valid_values=["2012-03-04"],
        error_values=["", "\n", "April 3, 2012", "2012/03/04"],
    )


if __name__ == "__main__":
  unittest.main()
