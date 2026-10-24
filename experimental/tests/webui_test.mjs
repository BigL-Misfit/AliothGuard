// SPDX-License-Identifier: MIT
import assert from 'node:assert/strict';
import { commandFor, execute, present } from '../module/webroot/app.mjs';
for (const action of ['status', 'builtin', 'next', 'rollback']) {
  assert.match(commandFor(action), /^sh \/data\/adb\/modules\/aliothguard_experimental\/scripts\/control\.sh /);
}
for (const input of ['__proto__', 'constructor', 'status; reboot', 'next$(id)', '', 'toString']) {
  assert.throws(() => commandFor(input), /Unsupported action/);
}
await assert.rejects(execute({}, 'status'), /No compatible WebUI bridge/);
const host = {};
host.ksu = { exec(command, options, callback) {
  assert.equal(command, commandFor('status')); assert.equal(options, '{}');
  host[callback](0, '{"schema":1}', '');
} };
assert.equal(await execute(host, 'status'), '{"schema":1}');
assert.equal(Object.keys(host).length, 1, 'Callback must be removed');
host.ksu.exec = (_, __, callback) => host[callback](1, '', 'Provider conflict');
await assert.rejects(execute(host, 'builtin'), /Provider conflict/);
host.ksu.exec = () => { throw new Error('bridge unavailable'); };
await assert.rejects(execute(host, 'status'), /bridge unavailable/);
const data = { schema: 1, version: '0.2.0', hooks_enabled: false,
  provider_configuration: 'conflict', provider_reason: 'multiple_providers',
  external_provider_count: 1, hiding_module_count: 0, integrity_module_count: 1,
  module_disabled: true, session_file_present: false, rom: { gms_spoof_property: 'true' } };
const view = present(data);
assert.match(view.conflicts, /multiple_providers/);
assert.match(view.integrity, /not requested/);
assert.match(view.root, /no hidden\/not-hidden verdict/);
assert.throws(() => present({ ...data, hooks_enabled: true }), /Unexpected status schema/);
assert.throws(() => present({ ...data, version: '9.9' }), /Unexpected status schema/);
console.log('AGX_WEBUI_PASS: command allowlist, bridge errors, cleanup, schema, separate verdicts');
