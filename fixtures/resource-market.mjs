process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
let ore = 0;
let screen = 'market';
const render = message => {
  const body = screen === 'help'
    ? 'HELP / CONTROLS\nMine ore, inspect inventory, then buy the beacon.\n[Escape] Return'
    : screen === 'inventory'
      ? `INVENTORY\nOre: ${ore}\n[Escape] Return`
      : `RESOURCE MARKET\nOre: ${ore}\n[h] Help\n[m] Mine ore\n[b] Buy beacon\n[i] Inventory\n[x] Invalid action`;
  process.stdout.write(`\x1b[2J\x1b[H${body}${message ? `\n${message}` : ''}\n`);
};
process.stdin.on('data', data => {
  for (const key of data) {
    if (key === '\u0003') process.exit(0);
    if (key === '\u001b') { screen = 'market'; render('RETURNED TO MARKET'); continue; }
    if (screen !== 'market') continue;
    if (key === 'h') { screen = 'help'; render(); continue; }
    if (key === 'i') { screen = 'inventory'; render(); continue; }
    if (key === 'm') { ore += 1; render('MINING COMPLETE'); continue; }
    if (key === 'b') {
      if (ore >= 1) process.stdout.write('\x1b[2J\x1b[HBEACON PURCHASED\nMARKET MISSION COMPLETE\n');
      else render('LOCKED: NEED 1 ORE');
      continue;
    }
    if (key === 'x') render('ERROR: INVALID MARKET ACTION');
  }
});
process.stdin.resume();
render();
