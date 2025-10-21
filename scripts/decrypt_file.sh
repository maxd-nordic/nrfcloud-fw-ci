#!/usr/bin/env bash

OUTFILE="${1%.gpg}"

gpg --decrypt --output "$OUTFILE" "$1"
