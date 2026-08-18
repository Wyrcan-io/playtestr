process.stdin.setRawMode?.(true);
process.stdin.resume();
const size = () => `${process.stdout.columns ?? 0}x${process.stdout.rows ?? 0}`;
console.log(`SIZE ${size()}`);
process.stdin.on('data', () => console.log(`SIZE ${size()}`));
