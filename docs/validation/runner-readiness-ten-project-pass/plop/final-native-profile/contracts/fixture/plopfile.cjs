// Synthetic user configuration for the documented Plop CLI (no shell actions).
module.exports = function (plop) {
  plop.setGenerator('artifact', {
    description: 'Generate a named reviewed artifact',
    prompts: [{type: 'input', name: 'name', message: 'Artifact name',
      validate: value => value.trim() ? true : 'Enter a nonempty artifact name'}],
    actions: [{type: 'add', path: 'out/{{name}}.txt', template: 'name={{name}}\n'}],
  });
};
