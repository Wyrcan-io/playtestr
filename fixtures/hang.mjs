process.stdin.setRawMode?.(true);
process.stdin.resume();
console.log('HANG READY');
setInterval(() => {}, 60_000);
