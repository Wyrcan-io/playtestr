---
title: "Compatibility and evidence"
description: "Understand exactly which Playtestr v0.1.0 downloads were verified and which terminal behavior remains limited."
previous:
  label: "Machine report v1"
  url: "docs/report-v1/"
next:
  label: "Platform evidence"
  url: "docs/platform-evidence/"
---

Stable `v0.1.0` publishes native archives for three exact targets:

| Release target | Native release and public-install evidence |
| --- | --- |
| Linux x86-64 (`amd64`) | Passed |
| Apple silicon macOS (`arm64`) | Passed |
| Windows x86-64 (`amd64`) | Passed |

Support applies to those archives and the documented version 1 contracts. It does not imply support for other architectures, every operating-system version or Linux distribution, every terminal application, or precise complex Unicode cell layout.

Read [Platform support evidence](/playtestr/docs/platform-evidence/) for the commits, native workflows, public archive checks, and the boundaries of operator-run application trials. Read [Terminal compatibility](/playtestr/docs/terminal-compatibility/) for rendered-text behavior, alternate-screen handling, resizing, and known emulator limits.

Playtestr runs trusted target applications with your user permissions. It is not a sandbox. Windows and Unix process-tree cleanup have the documented escape boundaries in the reference pages.
