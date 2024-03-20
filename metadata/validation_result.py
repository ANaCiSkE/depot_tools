#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import textwrap
from typing import Dict, List, Union

_CHROMIUM_METADATA_PRESCRIPT = "Third party metadata issue:"
_CHROMIUM_METADATA_POSTSCRIPT = ("Check //third_party/README.chromium.template "
                                 "for details.")


class ValidationResult:
    """Base class for validation issues."""
    def __init__(self, reason: str, fatal: bool, additional: List[str] = []):
        """Constructor for a validation issue.

        Args:
            reason: the root cause of the issue.
            fatal: whether the issue is fatal.
            additional: details that should be included in the
                        validation message, e.g. advice on how to
                        address the issue, or specific problematic
                        values.
        """
        self._reason = reason
        self._fatal = fatal
        self._message = " ".join([reason] + additional)
        self._tags = {}

    def __str__(self) -> str:
        prefix = self.get_severity_prefix()
        return f"{prefix} - {self._message}"

    def __repr__(self) -> str:
        return str(self)

    # PEP 8 recommends implementing all 6 rich comparisons.
    # Here we make use of tuple comparison, and order based on the severity
    # (e.g. fatal comes before non-fatal), then the message.
    def __lt__(self, other) -> bool:
        return (not self._fatal, self._message) < (not other._fatal,
                                                   other._message)

    def __le__(self, other) -> bool:
        return (not self._fatal, self._message) <= (not other._fatal,
                                                    other._message)

    def __gt__(self, other) -> bool:
        return (not self._fatal, self._message) > (not other._fatal,
                                                   other._message)

    def __ge__(self, other) -> bool:
        return (not self._fatal, self._message) >= (not other._fatal,
                                                    other._message)

    def __eq__(self, other) -> bool:
        return (not self._fatal, self._message) == (not other._fatal,
                                                    other._message)

    def __ne__(self, other) -> bool:
        return (not self._fatal, self._message) != (not other._fatal,
                                                    other._message)

    def is_fatal(self) -> bool:
        return self._fatal

    def get_severity_prefix(self):
        if self._fatal:
            return "ERROR"
        return "[non-fatal]"

    def get_reason(self) -> str:
        return self._reason

    def set_tag(self, tag: str, value: str) -> bool:
        self._tags[tag] = value

    def get_tag(self, tag: str) -> Union[str, None]:
        return self._tags.get(tag)

    def get_all_tags(self) -> Dict[str, str]:
        return dict(self._tags)

    def get_message(self,
                    prescript: str = _CHROMIUM_METADATA_PRESCRIPT,
                    postscript: str = _CHROMIUM_METADATA_POSTSCRIPT,
                    width: int = 0) -> str:
        components = [prescript, self._message, postscript]
        message = " ".join(
            [component for component in components if len(component) > 0])

        if width > 0:
            return textwrap.fill(text=message, width=width)

        return message


class ValidationError(ValidationResult):
    """Fatal validation issue. Presubmit should fail."""
    def __init__(self, reason: str, additional: List[str] = []):
        super().__init__(reason=reason, fatal=True, additional=additional)


class ValidationWarning(ValidationResult):
    """Non-fatal validation issue. Presubmit should pass."""
    def __init__(self, reason: str, additional: List[str] = []):
        super().__init__(reason=reason, fatal=False, additional=additional)
