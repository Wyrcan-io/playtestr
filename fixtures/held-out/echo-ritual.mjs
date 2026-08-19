process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
const route = ['e', 'c', 'h', 'o'];
const labels = ['Enter echo hall', 'Carry the chime', 'Hum the old note', 'Open the silent wall'];
let progress = 0;
function render(message = '') {
  const expected = route[progress] ?? route[0];
  const label = labels[progress] ?? labels[0];
  process.stdout.write(`\x1b[2J\x1b[HECHO RITUAL\nPUZZLE SEQUENCE STEP: ${progress}\n[${expected}] ${label}\n[a] Ring brass bell\n[z] Leave chalk mark${message ? `\n${message}` : ''}\n`);
}
process.stdin.on('data', data => { for (const key of data) {
  if (key === '\u0003') process.exit(0);
  if (key === route[progress]) progress += 1; else progress = key === route[0] ? 1 : 0;
  if (progress === route.length) { process.stdout.write('\x1b[2J\x1b[HECHO RITUAL\nSECRET CHAMBER UNLOCKED\nBONUS ENDING\n'); progress = 0; }
  else render(key === 'a' || key === 'z' ? 'The sequence resets.' : 'The echo answers.');
} });
process.stdin.resume();
render();
