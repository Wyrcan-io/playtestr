process.stdin.setRawMode?.(true);
process.stdin.setEncoding('utf8');
let route = '';
const render = () => process.stdout.write(`\x1b[2J\x1b[HROUTE ${route || '-'}\n`);
process.stdin.on('data', data => {
  for (const key of data) {
    route = `${route}${key}`.slice(-3);
    if (route === 'aab') process.stdout.write('\x1b[2J\x1b[HSECRET SPEEDRUN DOOR\n');
    else render();
  }
});
process.stdin.resume();
render();
