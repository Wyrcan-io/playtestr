import {createRequire} from 'node:module';
import {dirname, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

// Resolve the reviewed official framework beside the actual unmodified yo
// entry. This also follows a cold runtime copy without personal absolute paths.
const requireFramework = createRequire(resolve(dirname(process.argv[1]), '../../generator-toolchain/package.json'));
const {default: Generator} = await import(pathToFileURL(requireFramework.resolve('yeoman-generator')).href);

export default class extends Generator {
  async prompting() {
    this.answers = await this.prompt([
      {type: 'input', name: 'label', message: 'Project label',
       validate: value => value.trim() ? true : 'Project label is required', filter: value => value.trim()},
      {type: 'list', name: 'language', message: 'Project language', choices: ['TypeScript', 'JavaScript'], default: 'TypeScript'},
      {type: 'confirm', name: 'readme', message: 'Include README', default: true}
    ]);
  }
  writing() {
    const value = {label: this.answers.label, language: this.answers.language};
    this.fs.write(this.destinationPath('output/project.json'), JSON.stringify(value, null, 2) + '\n');
    if (this.answers.readme) {
      this.fs.write(this.destinationPath('output/README.md'), '# ' + value.label + '\n\nLanguage: ' + value.language + '\n');
    }
  }
  end() { this.log('Scaffold complete'); }
}
