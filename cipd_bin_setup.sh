# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

function cipd_bin_setup {
    local MYPATH="${DEPOT_TOOLS_DIR:-$(dirname "${BASH_SOURCE[0]}")}"
    local ENSURE="$MYPATH/cipd_manifest.txt"
    local ROOT="${DEPOT_TOOLS_CIPD_ROOT_OVERRIDE:-$MYPATH/.cipd_bin}"


    UNAME="${DEPOT_TOOLS_UNAME_S:-$(uname -s | tr '[:upper:]' '[:lower:]')}"
    case $UNAME in
      cygwin*)
        ENSURE="$(cygpath -w $ENSURE)"
        ROOT="$(cygpath -w $ROOT)"
        ;;
    esac

    (
    source "$MYPATH/cipd" ensure \
        -log-level warning \
        -ensure-file "$ENSURE" \
        -root "$ROOT"
    )

    echo $ROOT
}
