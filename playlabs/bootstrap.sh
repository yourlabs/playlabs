#!/bin/sh -x
if which python3; then
    if ! which python; then
        ln -sfn $(which python3) /usr/bin/python
    fi
    exit 0
fi

if which apt; then
    apt update -y
    apt install -y python3
elif which pacman; then
    pacman -Sy --noconfirm
    pacman -S --noconfirm python
fi
