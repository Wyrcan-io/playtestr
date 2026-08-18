#!/usr/bin/env node

const chunk = 'OUTPUT-FLOOD-'.repeat(64);
setInterval(() => process.stdout.write(chunk), 1);
