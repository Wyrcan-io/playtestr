process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
let chargedAt;
const render = message => process.stdout.write(`\x1b[2J\x1b[HTIMING GATE\n${message}\n[c] Charge\n[f] Fire\n[r] Reset\n`);
process.stdin.on('data', data => {
  for (const key of data) {
    if (key === '\u0003') process.exit(0);
    if (key === 'r') { chargedAt = undefined; render('RESET COMPLETE'); continue; }
    if (key === 'c') { chargedAt = Date.now(); render('CHARGING: WAIT BEFORE FIRING'); continue; }
    if (key === 'f') {
      if (!chargedAt) { render('ERROR: CHARGE FIRST'); continue; }
      const elapsed = Date.now() - chargedAt;
      if (elapsed < 200) render(`TOO EARLY: ${elapsed}ms`);
      else if (elapsed > 1200) render(`TOO LATE: ${elapsed}ms`);
      else render(`PERFECT TIMING: ${elapsed}ms\nGATE TRIAL COMPLETE`);
    }
  }
});
process.stdin.resume();
render('CHARGE THEN FIRE IN THE TIMING WINDOW');
