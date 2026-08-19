process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
let coil = false;
let charged = false;
function render(message = '') {
  const options = charged ? '[o] Open the relay door\n[v] View inventory\n[x] Touch exposed wiring' : coil ? '[c] Charge the relay coil\n[o] Open the relay door\n[v] View inventory\n[x] Touch exposed wiring' : '[s] Search the storage room\n[o] Open the relay door\n[x] Touch exposed wiring';
  process.stdout.write(`\x1b[2J\x1b[HRELAY VAULT\n${options}${message ? `\n${message}` : ''}\n`);
}
process.stdin.on('data', data => { for (const key of data) {
  if (key === '\u0003') process.exit(0);
  if (key === 's') { coil = true; render('ITEM ACQUIRED: RELAY COIL'); continue; }
  if (key === 'c') { if (!coil) render('LOCKED: NEED RELAY COIL'); else { charged = true; render('ENERGY: 1\nCOIL CHARGED'); } continue; }
  if (key === 'v') { render(`INVENTORY: ${coil ? 'RELAY COIL' : 'EMPTY'}\nENERGY: ${charged ? 1 : 0}`); continue; }
  if (key === 'o') { if (charged) render('RELAY DOOR OPEN\nVAULT MISSION COMPLETE'); else render('LOCKED: DOOR REQUIRES CHARGED COIL'); continue; }
  if (key === 'x') render('ERROR: EXPOSED WIRE CANNOT BE USED');
} });
process.stdin.resume();
render();
