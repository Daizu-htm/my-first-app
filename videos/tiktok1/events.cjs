// 選んだ初期条件でシミュレーションし、音を鳴らすタイミングを書き出す
const fs = require('fs');
const { createSim } = require('./sim.js');
const SEED = 2738, TAIL = 2.4;
const S = createSim(SEED);
while (S.doneAt < 0) S.step();
const frames = Math.ceil((S.doneAt + TAIL) * S.FPS);
fs.writeFileSync(__dirname + '/events.json', JSON.stringify({ seed: SEED, frames, fps: S.FPS, done: S.doneAt, events: S.events.map(e => ({ t: +e.t.toFixed(4), type: e.type, ring: e.ring || 0, x: Math.round(e.x || 540) })) }));
fs.writeFileSync(__dirname + '/meta.js', `window.META=${JSON.stringify({ seed: SEED, frames, done: S.doneAt })};\n`);
console.log('frames', frames, 'done', S.doneAt.toFixed(2), 'bounces', S.bounces, 'events', S.events.length);
