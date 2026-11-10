// 物理シミュレーション本体。ブラウザ(描画)とNode(音のタイミング抽出)の両方で同じ計算をする。
(function (root) {
  function rng32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  var CX = 540, CY = 850, NR = 12, G = 1100, BR = 11, SUB = 4, FPS = 60, MAXB = 96;
  function createSim(seed) {
    var r = rng32(seed), rings = [], i;
    for (i = 0; i < NR; i++) {
      var rad = 112 + i * 27;
      rings.push({ r: rad, a: r() * 6.283, w: (i % 2 ? -1 : 1) * (1.3 - .05 * i), gap: (32 + i * -1) / rad, alive: true, flash: 0, hue: (190 + i * 28) % 360 });
    }
    var S = { t: 0, frame: -1, rings: rings, balls: [{ x: CX, y: CY - 30, vx: (r() - .5) * 500, vy: -300 - r() * 200, hue: 50, trail: [] }],
      parts: [], waves: [], events: [], inner: 0, bounces: 0, shake: 0, flash: 0, punch: 0, doneAt: -1, CX: CX, CY: CY, NR: NR, BR: BR, FPS: FPS };
    function breakRing() {
      var ring = rings[S.inner]; ring.alive = false;
      S.events.push({ t: S.t, type: 1, ring: S.inner, n: S.balls.length });
      for (var k = 0; k < 90; k++) {
        var an = ring.a + ring.gap + r() * (6.283 - 2 * ring.gap), sp = 120 + r() * 480, c = Math.cos(an), s = Math.sin(an);
        S.parts.push({ x: CX + c * ring.r, y: CY + s * ring.r, vx: c * sp - s * ring.w * ring.r, vy: s * sp + c * ring.w * ring.r - 120, life: 1, d: .6 + r() * .7, hue: ring.hue + r() * 30, sz: 4 + r() * 9, rot: an, vr: (r() - .5) * 14 });
      }
      S.waves.push({ r: ring.r, life: 1, hue: ring.hue });
      S.inner++; S.flash = .4; S.shake = 16; S.punch = 1;
      var n = S.balls.length;
      for (var b = 0; b < n && S.balls.length < MAXB; b++) {
        var o = S.balls[b], da = (r() - .5) * 1.7, c2 = Math.cos(da), s2 = Math.sin(da), m = .9 + r() * .25;
        S.balls.push({ x: o.x, y: o.y, vx: (o.vx * c2 - o.vy * s2) * m, vy: (o.vx * s2 + o.vy * c2) * m, hue: (o.hue + 40 + r() * 80) % 360, trail: [] });
      }
      if (S.inner >= NR) {
        S.doneAt = S.t; S.events.push({ t: S.t, type: 2 });
        for (var q = 0; q < 320; q++) { var a2 = r() * 6.283, v2 = 200 + r() * 1100; S.parts.push({ x: CX, y: CY, vx: Math.cos(a2) * v2, vy: Math.sin(a2) * v2 - 300, life: 1, d: .35 + r() * .35, hue: r() * 360, sz: 6 + r() * 12, rot: a2, vr: (r() - .5) * 16 }); }
      }
    }
    S.step = function () {
      S.frame++;
      for (var sub = 0; sub < SUB; sub++) {
        var dt = 1 / (FPS * SUB), brk = false; S.t += dt;
        for (var i2 = 0; i2 < NR; i2++) rings[i2].a += rings[i2].w * dt;
        var ring = rings[S.inner];
        for (var b = 0; b < S.balls.length; b++) {
          var p = S.balls[b]; p.vy += G * dt; p.x += p.vx * dt; p.y += p.vy * dt;
          if (!ring) continue;
          var dx = p.x - CX, dy = p.y - CY, d = Math.sqrt(dx * dx + dy * dy), lim = ring.r - 5 - BR;
          if (d < lim) continue;
          var nx = dx / d, ny = dy / d, vr = p.vx * nx + p.vy * ny;
          if (vr <= 0) continue;
          var da = Math.atan2(dy, dx) - ring.a; da = Math.atan2(Math.sin(da), Math.cos(da));
          if (Math.abs(da) < ring.gap - BR / ring.r * .7) { brk = true; continue; }
          p.vx -= 2 * vr * nx; p.vy -= 2 * vr * ny;
          p.vx += -ny * ring.w * ring.r * .08; p.vy += nx * ring.w * ring.r * .08;
          var vn = -(p.vx * nx + p.vy * ny); if (vn < 260) { p.vx -= nx * (260 - vn); p.vy -= ny * (260 - vn); }
          var sp = Math.sqrt(p.vx * p.vx + p.vy * p.vy), k = sp < 560 ? 560 / sp : sp > 1150 ? 1150 / sp : 1; p.vx *= k; p.vy *= k;
          p.x = CX + nx * lim; p.y = CY + ny * lim; p.hue = (p.hue + 23) % 360;
          ring.flash = 1; S.bounces++;
          S.events.push({ t: S.t, type: 0, ring: S.inner, x: p.x });
          if (S.parts.length < 900) for (var q = 0; q < 3; q++) S.parts.push({ x: p.x + nx * BR, y: p.y + ny * BR, vx: -nx * (80 + r() * 200) + (r() - .5) * 260, vy: -ny * (80 + r() * 200) + (r() - .5) * 260, life: 1, d: 2.6, hue: ring.hue, sz: 3 + r() * 3, rot: 0, vr: 0 });
        }
        if (brk) breakRing();
      }
      var f = 1 / FPS, j;
      for (j = 0; j < S.balls.length; j++) { var bl = S.balls[j]; bl.trail.push(bl.x, bl.y); if (bl.trail.length > 20) bl.trail.splice(0, 2); }
      S.balls = S.balls.filter(function (o) { return o.y < 2300; });
      for (j = 0; j < S.parts.length; j++) { var pt = S.parts[j]; pt.vy += 700 * f; pt.x += pt.vx * f; pt.y += pt.vy * f; pt.rot += pt.vr * f; pt.life -= pt.d * f; }
      S.parts = S.parts.filter(function (o) { return o.life > 0; });
      for (j = 0; j < S.waves.length; j++) { S.waves[j].r += 900 * f; S.waves[j].life -= 2.2 * f; }
      S.waves = S.waves.filter(function (o) { return o.life > 0; });
      for (j = 0; j < NR; j++) rings[j].flash *= .86;
      S.shake *= .88; S.flash *= .85; S.punch *= .9;
    };
    return S;
  }
  root.createSim = createSim;
  if (typeof module !== 'undefined') module.exports = { createSim: createSim };
})(typeof window !== 'undefined' ? window : globalThis);
