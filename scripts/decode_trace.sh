#!/usr/bin/env bash

# Check if any input files provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1.gpg> [file2.gpg] [file3.gpg] ..."
    exit 1
fi

# Process each input file
for input_file in "$@"; do
    echo "Processing: $input_file"

    BINFILE=${input_file%.gpg}
    PCAPNGFILE=${input_file%.gpg}.pcapng

    rm -rf "$BINFILE" || true

    gpg --decrypt --output "$BINFILE" "$input_file"
    nrfutil trace lte --input-file "$BINFILE" --output-pcapng "$PCAPNGFILE" && rm -rf "$BINFILE" || true

    echo "Completed: $PCAPNGFILE"
    echo "---"
done
