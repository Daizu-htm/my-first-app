// ちょうどいい長さと展開になる初期条件(seed)を探す
const { createSim } = require('./sim.js');
const out = [];
for (let seed = 1; seed <= 3000; seed++) {
  const S = createSim(seed);
  while (S.doneAt < 0 && S.t < 40) S.step();
  if (S.doneAt < 0) continue;
  const br = S.events.filter(e => e.type === 1).map(e => e.t);
  let maxGap = br[0]; for (let i = 1; i < br.length; i++) maxGap = Math.max(maxGap, br[i] - br[i - 1]);
  const lastGap = br[11] - br[10];
  out.push({ seed, done: +S.doneAt.toFixed(2), first: +br[0].toFixed(2), maxGap: +maxGap.toFixed(2), lastGap: +lastGap.toFixed(2), bounces: S.bounces, br: br.map(v => +v.toFixed(1)) });
}
const d = out.map(o => o.done).sort((a, b) => a - b);
console.log('n', out.length, 'median', d[d.length >> 1], 'min', d[0], 'max', d[d.length - 1]);
const ok = out.filter(o => o.done >= 16 && o.done <= 24 && o.first >= .8 && o.first <= 2.6 && o.maxGap <= 3.4 && o.lastGap >= .4 && o.lastGap <= 3);
ok.sort((a, b) => a.maxGap - b.maxGap);
console.log(ok.length); ok.slice(0, 8).forEach(o => console.log(JSON.stringify(o)));
