process.stdout.write('SIGNAL READY\nIntentional SIGTERM is scheduled.\n');
setTimeout(() => process.kill(process.pid, 'SIGTERM'), 100);
