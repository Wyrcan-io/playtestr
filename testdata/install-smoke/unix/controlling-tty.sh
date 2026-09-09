#!/bin/sh

if ! exec 3<>/dev/tty; then
  printf 'unable to open controlling terminal\n' >&2
  exit 1
fi
printf 'controlling terminal ready\n' >&3
IFS= read -r answer <&3
printf 'controlling terminal received: %s\n' "$answer" >&3
