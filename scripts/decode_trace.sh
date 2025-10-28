#!/usr/bin/env bash

BINFILE=/tmp/"$(basename $1)"
PCAPNGFILE=${1%.gpg}.pcapng

rm -rf $BINFILE || true

gpg --decrypt --output "$BINFILE" "$1"
nrfutil trace lte --input-file "$BINFILE" --output-pcapng "$PCAPNGFILE"
