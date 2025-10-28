#!/usr/bin/env bash
gpg --trust-model always --recipient 867EA82CBC8DE294214CC9BB1DA902A93597201D --encrypt "$1"
