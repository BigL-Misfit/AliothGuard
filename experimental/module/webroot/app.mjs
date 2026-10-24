// SPDX-License-Identifier: MIT
// Original adapter for the documented KernelSU-style exec bridge. No dependencies.
const control = 'sh /data/adb/modules/aliothguard_experimental/scripts/control.sh';
const commands = Object.freeze({
  status: `${control} status`,
  builtin: `${control} arm builtin --lab-device`,
  next: `${control} arm next --lab-device`,
  rollback: `${control} rollback`,
});
let sequence = 0;
export function commandFor(action) {
  if (!Object.hasOwn(commands, action)) throw new Error('Unsupported action');
  return commands[action];
}
export function execute(host, action) {
  const command = commandFor(action);
  if (!host.ksu || typeof host.ksu.exec !== 'function') {
    return Promise.reject(new Error('No compatible WebUI bridge. Open in a trusted Magisk-compatible host.'));
  }
  return new Promise((resolve, reject) => {
    const name = `agx_callback_${++sequence}`;
    const timer = setTimeout(() => { delete host[name]; reject(new Error('Command timed out; refresh status before retrying.')); }, 15000);
    const clean = () => { clearTimeout(timer); delete host[name]; };
    host[name] = (errno, stdout, stderr) => {
      clean();
      if (Number(errno) !== 0) reject(new Error(String(stderr || `Command failed (${errno})`)));
      else resolve(String(stdout));
    };
    try { host.ksu.exec(command, '{}', name); } catch (error) { clean(); reject(error); }
  });
}
export function present(status) {
  if (status.schema !== 1 || status.version !== '0.2.0' || status.hooks_enabled !== false) {
    throw new Error('Unexpected status schema; refusing configuration controls.');
  }
  return {
    provider: `Configured provider: ${status.provider_configuration}. Running provider: unverified.`,
    conflicts: `Gate: ${status.provider_reason}. External providers: ${status.external_provider_count}; hiding modules: ${status.hiding_module_count}; integrity modules: ${status.integrity_module_count}.`,
    rom: `AxionOS 1.6 source contains PIF and Tricky-Store-derived hooks. Installed ROM settings and key material are not inspected or changed. GMS spoofing property: ${status.rom.gms_spoof_property || 'unknown'}.`,
    session: `Module disabled: ${status.module_disabled}. Session file present: ${status.session_file_present}. A file is not proof of an active probe; check the test app.`,
    root: 'Root detection: observations only; no hidden/not-hidden verdict. Use the dedicated test app for individual signals.',
    integrity: 'Play Integrity: not requested. BASIC, DEVICE and STRONG are unknown.',
  };
}
if (typeof document !== 'undefined') {
  const element = id => document.getElementById(id);
  let connected = false;
  let busy = false;
  function controls() {
    element('arm').disabled = !connected || busy || !element('lab-confirm').checked;
    element('rollback').disabled = !connected || busy;
    element('refresh').disabled = busy;
  }
  async function refresh() {
    const data = JSON.parse(await execute(window, 'status'));
    const view = present(data);
    for (const key of ['provider', 'conflicts', 'rom', 'session']) element(key).textContent = view[key];
    element('root-result').textContent = view.root;
    element('integrity-result').textContent = view.integrity;
    connected = true;
  }
  async function run(action) {
    busy = true; controls();
    try {
      if (action !== 'status') element('message').textContent = await execute(window, action);
      await refresh();
      if (action === 'status') element('message').textContent = 'Status refreshed. No configuration changed.';
    } catch (error) { connected = false; element('message').textContent = error.message; }
    finally { busy = false; controls(); }
  }
  element('refresh').onclick = () => run('status');
  element('rollback').onclick = () => run('rollback');
  element('lab-confirm').onchange = controls;
  element('arm').onclick = () => { if (element('lab-confirm').checked) run(element('provider-choice').value); };
  run('status');
}
