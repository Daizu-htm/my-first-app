import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
const html = readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');
assert.match(html, /<html lang="ja">/);
assert.match(html, /name="viewport"/);
assert.match(html, /<title>[^<]+<\/title>/);
assert.match(html, /id="btn"/);
console.log('smoke test passed');
