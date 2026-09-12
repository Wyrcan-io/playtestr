(() => {
  const root = document.querySelector('[data-terminal-demo]');
  if (!root) return;
  const elements = {
    status: root.querySelector('[data-demo-status]'), command: root.querySelector('[data-demo-command]'), filename: root.querySelector('[data-demo-filename]'),
    lines: root.querySelector('[data-spec-lines]'), screen: root.querySelector('[data-demo-screen]'),
    explanation: root.querySelector('[data-demo-explanation]'), result: root.querySelector('[data-demo-result]'),
    progress: root.querySelector('[data-demo-progress]'), provenance: root.querySelector('[data-demo-provenance]'), live: root.querySelector('[data-demo-live]'),
    evidencePanel: root.querySelector('[data-evidence-panel]'), evidenceOutput: root.querySelector('[data-evidence-output]')
  };
  const buttons = {play: root.querySelector('[data-demo-action="play"]'), next: root.querySelector('[data-demo-action="next"]'), restart: root.querySelector('[data-demo-action="restart"]')};
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let scenarios = [];
  let scenario;
  let frameIndex = 0;
  let timer;
  let evidenceKind = 'expected';

  const validScenario = (item) => item && typeof item.id === 'string' && typeof item.specFile === 'string' && typeof item.command === 'string' && item.command.length < 300 && typeof item.runnerVersion === 'string' && typeof item.host === 'string' && typeof item.sourceRevision === 'string' && Array.isArray(item.specLines) && item.specLines.length <= 80 && Array.isArray(item.frames) && item.frames.length > 0 && item.frames.length <= 40 && item.frames.every((frame) => Number.isInteger(frame.activeLine) && typeof frame.screen === 'string' && frame.screen.length <= 12000 && typeof frame.explanation === 'string' && frame.explanation.length <= 500);
  const stop = () => { if (timer) window.clearInterval(timer); timer = undefined; buttons.play.textContent = 'Play'; elements.status.textContent = frameIndex === scenario?.frames.length - 1 ? 'Complete' : 'Paused'; };
  const renderEvidence = () => {
    const value = scenario.evidence?.[evidenceKind] || 'No evidence for this view.';
    elements.evidenceOutput.replaceChildren();
    value.split('\n').forEach((line, index, lines) => {
      const span = document.createElement('span');
      if (evidenceKind === 'diff' && line.startsWith('-') && !line.startsWith('---')) span.className = 'diff-remove';
      if (evidenceKind === 'diff' && line.startsWith('+') && !line.startsWith('+++')) span.className = 'diff-add';
      span.textContent = line + (index < lines.length - 1 ? '\n' : '');
      elements.evidenceOutput.appendChild(span);
    });
    elements.evidenceOutput.className = `evidence-output evidence-${evidenceKind}`;
  };
  const render = (announce = false) => {
    if (!scenario) return;
    const frame = scenario.frames[frameIndex];
    elements.command.textContent = scenario.command;
    elements.filename.textContent = scenario.specFile;
    elements.provenance.textContent = `${scenario.runnerVersion} · ${scenario.host} · source ${scenario.sourceRevision}`;
    elements.lines.replaceChildren();
    scenario.specLines.forEach((line, index) => {
      const item = document.createElement('li');
      if (index + 1 === frame.activeLine) item.className = 'active';
      const number = document.createElement('span'); number.className = 'line-no'; number.textContent = String(index + 1);
      item.append(number, document.createTextNode(line)); elements.lines.appendChild(item);
    });
    elements.screen.textContent = frame.screen;
    elements.explanation.textContent = frame.explanation;
    elements.result.textContent = frame.result || `Step ${frameIndex + 1} of ${scenario.frames.length}`;
    elements.result.className = `demo-result ${frame.outcome || ''}`;
    elements.progress.textContent = `${frameIndex + 1} / ${scenario.frames.length}`;
    buttons.next.disabled = frameIndex === scenario.frames.length - 1;
    elements.evidencePanel.hidden = !(scenario.evidence && frameIndex === scenario.frames.length - 1);
    if (!elements.evidencePanel.hidden) renderEvidence();
    if (announce) elements.live.textContent = `${elements.result.textContent}. ${frame.explanation}`;
  };
  const next = () => { if (frameIndex < scenario.frames.length - 1) { frameIndex += 1; render(true); } else stop(); };
  const play = () => {
    if (timer) { stop(); return; }
    if (frameIndex === scenario.frames.length - 1) frameIndex = 0;
    if (reducedMotion) { frameIndex = scenario.frames.length - 1; render(true); stop(); return; }
    buttons.play.textContent = 'Pause'; elements.status.textContent = 'Playing';
    timer = window.setInterval(() => { next(); if (frameIndex === scenario.frames.length - 1) stop(); }, 1300);
  };
  const choose = (id) => {
    stop(); scenario = scenarios.find((item) => item.id === id); frameIndex = 0; evidenceKind = 'expected';
    root.querySelectorAll('[data-scenario]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.scenario === id)));
    root.querySelectorAll('[data-evidence]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.evidence === evidenceKind)));
    render(true);
  };
  buttons.play.addEventListener('click', play);
  buttons.next.addEventListener('click', () => { stop(); next(); });
  buttons.restart.addEventListener('click', () => { stop(); frameIndex = 0; render(true); });
  root.querySelectorAll('[data-scenario]').forEach((button) => button.addEventListener('click', () => choose(button.dataset.scenario)));
  root.querySelectorAll('[data-evidence]').forEach((button) => button.addEventListener('click', () => { evidenceKind = button.dataset.evidence; root.querySelectorAll('[data-evidence]').forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button))); renderEvidence(); }));
  root.addEventListener('keydown', (event) => { if (event.target.matches('button')) return; if (event.key === 'ArrowRight') { event.preventDefault(); stop(); next(); } else if (event.key === 'Enter') { event.preventDefault(); play(); } });
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });

  fetch(root.dataset.source).then((response) => { if (!response.ok) throw new Error('demo data unavailable'); return response.json(); }).then((data) => {
    if (!data || !Array.isArray(data.scenarios) || !data.scenarios.every(validScenario)) throw new Error('invalid demo data');
    scenarios = data.scenarios; choose('pass');
  }).catch(() => { elements.status.textContent = 'Static example'; elements.live.textContent = 'Interactive controls are unavailable. The static example is still visible.'; Object.values(buttons).forEach((button) => { button.disabled = true; }); });
})();
