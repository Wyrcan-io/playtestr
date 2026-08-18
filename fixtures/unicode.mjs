process.stdin.setEncoding('utf8');
process.stdin.setRawMode?.(true);
process.stdin.resume();
console.log('UNICODE READY: λ 漢字 🚀');
process.stdin.on('data', data => {
  if (data.includes('λ')) console.log('UNICODE ACCEPTED: λ');
  if (data.includes('q')) process.exit(0);
});
