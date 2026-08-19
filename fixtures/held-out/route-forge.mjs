process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
let ember = false;
let blade = false;
function render(message = '') {
  const options = blade ? '[o] Open the forge gate\n[v] View inventory\n[t] Polish blade' : ember ? '[b] Forge the ember blade\n[t] Inspect anvil\n[v] View inventory' : '[e] Collect an ember\n[t] Inspect anvil';
  process.stdout.write(`\x1b[2J\x1b[HROUTE FORGE\n${options}${message ? `\n${message}` : ''}\n`);
}
process.stdin.on('data', data => { for (const key of data) {
  if (key === '\u0003') process.exit(0);
  if (key === 'e') { ember = true; render('RESOURCE ACQUIRED\nEMBER: 1'); continue; }
  if (key === 'b' && ember) { blade = true; render('ITEM FORGED: EMBER BLADE'); continue; }
  if (key === 'o') { if (blade) render('FORGE GATE OPEN\nTRIAL COMPLETE'); else render('LOCKED: NEED EMBER BLADE'); continue; }
  if (key === 'v') { render(`INVENTORY: ${blade ? 'EMBER BLADE' : ember ? 'EMBER' : 'EMPTY'}`); continue; }
  if (key === 't') render('ANVIL INSPECTION COMPLETE');
} });
process.stdin.resume();
render();
