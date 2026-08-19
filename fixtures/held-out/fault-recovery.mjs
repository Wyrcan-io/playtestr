process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
let faulted = false;
let recovered = false;
function render(message = '') {
  const options = faulted ? '[r] Retry and return to console\n[q] Quit' : recovered ? '[c] Continue the repaired trial\n[f] Pull the unstable lever' : '[f] Pull the unstable lever\n[c] Continue trial';
  process.stdout.write(`\x1b[2J\x1b[HFAULT RECOVERY TRIAL\n${options}${message ? `\n${message}` : ''}\n`);
}
process.stdin.on('data', data => { for (const key of data) {
  if (key === '\u0003') process.exit(0);
  if (key === 'f' && !faulted) { faulted = true; render('ERROR: LEVER FAILED\nCONTROLS LOCKED'); continue; }
  if (key === 'r' && faulted) { faulted = false; recovered = true; render('RECOVERY SUCCESS: CONSOLE RESUMED'); continue; }
  if (key === 'c') { if (recovered) render('REPAIR VERIFIED\nTRAINING COMPLETE'); else render('LOCKED: NEED RECOVERY CHECK'); continue; }
} });
process.stdin.resume();
render();
