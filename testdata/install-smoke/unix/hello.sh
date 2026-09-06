#!/bin/sh

printf 'Name: '
IFS= read -r name
printf 'Hello, %s!\n' "$name"
printf 'Press Enter to exit: '
IFS= read -r ignored
