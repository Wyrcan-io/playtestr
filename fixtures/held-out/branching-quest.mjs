process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
let map = false;
let key = false;
let shrine = false;
function render(message = '') {
  const options = shrine ? '[w] Whisper to the shrine\n[d] Open the north door\n[i] Inventory' : key ? '[d] Open the north door\n[s] Search the side room\n[i] Inventory' : map ? '[k] Take the archive key\n[s] Search the side room\n[i] Inventory' : '[m] Read the room map\n[s] Search the side room';
  process.stdout.write(`\x1b[2J\x1b[HBRANCHING QUEST\n${options}${message ? `\n${message}` : ''}\n`);
}
process.stdin.on('data', data => { for (const action of data) {
  if (action === '\u0003') process.exit(0);
  if (action === 'm') { map = true; render('MAP REVEALS AN ARCHIVE KEY'); continue; }
  if (action === 'k' && map) { key = true; render('ITEM ACQUIRED: ARCHIVE KEY'); continue; }
  if (action === 's') { shrine = true; render('HIDDEN SHRINE FOUND'); continue; }
  if (action === 'w' && shrine) { render('SECRET WHISPER ANSWERED\nBONUS ENDING'); continue; }
  if (action === 'd') { if (key) render('NORTH DOOR OPEN\nQUEST COMPLETE'); else render('LOCKED: NEED ARCHIVE KEY'); continue; }
  if (action === 'i') { render(`INVENTORY: ${key ? 'ARCHIVE KEY' : 'EMPTY'}`); continue; }
} });
process.stdin.resume();
render();
