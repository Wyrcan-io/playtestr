// Synthetic ordinary Plop user configuration. All writes use built-in actions.
module.exports = function (plop) {
  const input = message => [{type: 'input', name: 'name', message}];
  const add = (path, template, more = {}) => ({type: 'add', path, template, ...more});
  const define = (name, prompts, actions) => plop.setGenerator(name, {prompts, actions});

  define('module', input('Module name'), [{type: 'addMany', destination: 'modules/{{name}}',
    base: 'templates/module', templateFiles: 'templates/module/**/*'}]);
  define('route', input('Route name'), [{type: 'append', path: 'registry.txt',
    pattern: /ROUTES/, template: 'route={{name}}'}]);
  define('version', input('Replacement version'), [{type: 'modify', path: 'version.txt',
    pattern: /version=1/, template: 'version={{name}}'}]);
  define('optional', [...input('Required artifact name'), {type: 'confirm', name: 'extra',
    message: 'Include optional file?', default: false}], data => [
    add('required.txt', 'required={{name}}\n'),
    ...(data.extra ? [add('optional.txt', 'optional={{name}}\n')] : []),
  ]);
  define('preserve', [{type: 'confirm', name: 'ok', message: 'Preserve existing file?', default: true}],
    [add('existing.txt', 'replacement\n', {skipIfExists: true})]);
  define('overwrite', [{type: 'confirm', name: 'ok', message: 'Replace generated file?', default: false}],
    data => data.ok ? [add('existing.txt', 'approved replacement\n', {force: true})] : []);
  define('case-helpers', input('Module identifier'),
    [add('case/{{kebabCase name}}.txt', 'class {{pascalCase name}}\n')]);
  define('collision', input('Collision attempt name'), [add('existing.txt', 'name={{name}}\n')]);
  define('blocked-parent', input('Blocked output name'), [add('blocked/{{name}}.txt', 'name={{name}}\n')]);
  define('raw-files', [{type: 'confirm', name: 'ok', message: 'Copy raw reviewed fixtures?', default: true}],
    [{type: 'addMany', destination: 'raw-output', base: 'templates/raw', templateFiles: 'templates/raw/**/*'}]);
  define('route-unique', [{type: 'confirm', name: 'ok', message: 'Register the existing route once?', default: true}],
    [{type: 'append', path: 'unique-registry.txt', pattern: /ROUTES/, template: 'route=alpha'}]);
  define('missing-template', input('Missing template artifact'),
    [{type: 'add', path: 'missing-output.txt', templateFile: 'templates/not-present.hbs'}]);
  define('partial-abort', input('Partial generation name'), [
    add('partial.txt', 'first={{name}}\n'), add('collision.txt', 'must not replace\n'),
    add('never-created.txt', 'must not appear\n'),
  ]);
  define('continue-after-error', input('Continue generation name'), [
    add('collision.txt', 'must not replace\n', {abortOnFail: false}), add('continued.txt', 'continued={{name}}\n'),
  ]);
  define('late-choice', [{type: 'list', name: 'name', message: 'Choose a reviewed destination',
    pageSize: 5, choices: Array.from({length: 18}, (_, i) => ({name: `Destination ${String(i + 1).padStart(2, '0')}`, value: `item-${i + 1}`}))}],
    [add('selection.txt', 'selected={{name}}\n')]);
};
