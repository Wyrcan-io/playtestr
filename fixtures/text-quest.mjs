process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
let keyOwned = false;
let buffer = '';
const render = message => process.stdout.write(`\x1b[2J\x1b[HTEXT QUEST\n${message}\nCommand:\n> `);
const command = value => {
  if (value === 'look') render('ROOM: ARCHIVE\nA brass key rests beside a locked north door.');
  else if (value === 'take key') { keyOwned = true; render('ITEM ACQUIRED: BRASS KEY'); }
  else if (value === 'inventory') render(`INVENTORY: ${keyOwned ? 'BRASS KEY' : 'EMPTY'}`);
  else if (value === 'north' || value === 'open door') {
    if (keyOwned) render('DOOR OPEN\nTEXT QUEST COMPLETE');
    else render('LOCKED: YOU NEED THE BRASS KEY');
  } else render('UNKNOWN COMMAND. TRY LOOK, TAKE KEY, INVENTORY, OR NORTH.');
};
process.stdin.on('data', data => {
  if (data.includes('\u0003')) process.exit(0);
  buffer += data;
  const parts = buffer.split(/[\r\n]/u);
  buffer = parts.pop() ?? '';
  for (const part of parts) if (part.trim()) command(part.trim().toLowerCase());
});
process.stdin.resume();
render('Type LOOK to inspect the room.');
