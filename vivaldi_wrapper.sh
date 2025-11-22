#!/bin/bash
# Wrapper to launch Vivaldi from Flatpak for Playwright
exec /usr/bin/flatpak run --branch=stable --arch=x86_64 --command=vivaldi --file-forwarding com.vivaldi.Vivaldi "$@"
