@echo off
:: Copyright 2023 The Chromium Authors
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.
setlocal

echo "Error: 'autosiso' is deprecated and will be removed soon."
echo ""
echo "You can just run 'autoninja' instead, which will delegate either to Ninja"
echo "or to Siso based on the value of the 'use_siso' GN arg in your output folder."

exit /b 1
