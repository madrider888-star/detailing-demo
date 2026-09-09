/**
 * Generates the site's automotive artwork as static SVG scenes.
 *
 * Everything is drawn locally so the demo has no external image dependencies:
 * a dark studio scene (three body silhouettes, lighting rig, floor reflection),
 * plus macro "detail shot" styles for surfaces — beading, polish, leather,
 * film weave, tinted glass, headlight optics and wheels.
 */
import { mkdirSync, writeFileSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "public", "media");

/* ------------------------------------------------------------------ tokens */

const INK = {
  void: "#050607",
  deep: "#0A0C0F",
  mid: "#12161A",
  panel: "#181D22",
  steel: "#98A2AC",
  light: "#D7DEE5",
};

const ACCENTS = {
  gold: "#D9B778",
  ice: "#8FC1EA",
  steel: "#A9B4BF",
  ember: "#D08A5C",
};

/** Deterministic PRNG so regenerating the media folder is reproducible. */
function rng(seed) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let x = t;
    x = Math.imul(x ^ (x >>> 15), x | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

const round = (n) => Math.round(n * 100) / 100;

/* ----------------------------------------------------------- car geometry */

const BODIES = {
  coupe: {
    body:
      "M 208 652 C 196 634 194 596 206 570 C 216 548 240 534 276 526 " +
      "C 330 514 384 498 440 476 C 512 448 590 428 676 420 " +
      "C 760 412 838 418 902 436 C 946 448 984 466 1022 486 " +
      "C 1076 512 1136 528 1210 538 C 1300 550 1368 566 1404 592 " +
      "C 1424 606 1430 632 1422 650 C 1418 658 1408 662 1394 662 " +
      "L 236 662 C 220 662 212 658 208 652 Z",
    glass:
      "M 402 500 C 470 458 566 440 668 436 C 760 432 838 442 894 458 " +
      "L 960 496 L 402 500 Z",
    pillars: ["M 560 444 L 548 498", "M 812 440 L 826 496"],
    shoulder:
      "M 250 566 C 420 548 700 540 980 552 C 1160 560 1320 578 1400 600",
    roofline:
      "M 384 498 C 470 452 566 434 672 430 C 766 426 844 438 900 456",
    wheels: [
      { cx: 398, cy: 642, r: 118 },
      { cx: 1218, cy: 642, r: 118 },
    ],
  },
  sedan: {
    body:
      "M 210 656 C 198 638 194 598 204 570 C 212 548 234 534 268 526 " +
      "L 372 512 C 420 470 486 436 574 424 C 664 412 792 414 872 432 " +
      "C 918 442 952 462 984 486 L 1108 508 C 1230 524 1330 552 1382 584 " +
      "C 1414 604 1428 628 1420 650 C 1416 658 1406 662 1392 662 " +
      "L 236 662 C 222 662 214 660 210 656 Z",
    glass:
      "M 396 508 C 440 470 500 448 578 440 C 664 430 780 432 856 448 " +
      "C 898 458 928 474 952 492 L 396 508 Z",
    pillars: ["M 560 442 L 548 506", "M 792 438 L 806 500"],
    shoulder:
      "M 250 574 C 430 558 720 552 1000 566 C 1180 576 1330 594 1398 612",
    roofline:
      "M 392 506 C 440 466 502 444 580 436 C 668 426 782 428 858 444",
    wheels: [
      { cx: 396, cy: 648, r: 112 },
      { cx: 1206, cy: 648, r: 112 },
    ],
  },
  suv: {
    body:
      "M 200 662 C 190 640 188 574 196 540 C 202 512 218 494 244 484 " +
      "L 268 396 C 276 366 300 350 336 346 C 470 334 700 330 880 340 " +
      "C 940 344 972 358 992 388 L 1058 486 C 1140 500 1260 516 1340 540 " +
      "C 1392 556 1420 578 1428 610 C 1432 634 1428 652 1418 660 " +
      "C 1412 663 1402 664 1390 664 L 232 664 C 214 664 206 664 200 662 Z",
    glass:
      "M 264 478 L 284 390 C 290 368 310 360 342 358 C 480 350 700 348 872 356 " +
      "C 920 360 946 372 960 396 L 1002 470 Z",
    pillars: ["M 470 356 L 462 474", "M 700 352 L 700 474"],
    shoulder:
      "M 236 556 C 430 540 740 534 1000 548 C 1180 558 1340 580 1412 606",
    roofline:
      "M 268 394 C 290 360 330 350 400 348 C 560 340 762 342 882 350",
    wheels: [
      { cx: 392, cy: 634, r: 126 },
      { cx: 1226, cy: 634, r: 126 },
    ],
  },
};

const GROUND = 760;

function wheel({ cx, cy, r }, id, opts = {}) {
  const face = r * 0.71;
  const spokeCount = 10;
  const spokes = [];
  for (let i = 0; i < spokeCount; i += 1) {
    const a = (i / spokeCount) * Math.PI * 2;
    const x1 = cx + Math.cos(a) * (face * 0.24);
    const y1 = cy + Math.sin(a) * (face * 0.24);
    const x2 = cx + Math.cos(a) * (face * 0.92);
    const y2 = cy + Math.sin(a) * (face * 0.92);
    spokes.push(
      `<path d="M ${round(x1)} ${round(y1)} L ${round(x2)} ${round(y2)}" stroke="url(#${id}-rim)" stroke-width="${round(
        Math.max(1.2, r * 0.062),
      )}" stroke-linecap="round" opacity=".55"/>`,
    );
  }
  const caliper = opts.caliper
    ? `<path d="M ${round(cx + face * 0.34)} ${round(cy - face * 0.5)} A ${round(face * 0.6)} ${round(
        face * 0.6,
      )} 0 0 1 ${round(cx + face * 0.34)} ${round(cy + face * 0.5)}" stroke="${
        opts.caliper
      }" stroke-width="${round(Math.max(2, r * 0.08))}" fill="none" stroke-linecap="round" opacity=".45"/>`
    : "";
  return `<g>
  <circle cx="${cx}" cy="${cy}" r="${r}" fill="#07090B"/>
  <path d="M ${round(cx - r)} ${cy} A ${r} ${r} 0 0 1 ${round(cx + r)} ${cy}" fill="none" stroke="#ffffff" stroke-width="${round(
    Math.max(1, r * 0.012),
  )}" opacity=".16"/>
  <circle cx="${cx}" cy="${cy}" r="${round(face)}" fill="url(#${id}-disc)"/>
  ${caliper}
  ${spokes.join("\n  ")}
  <circle cx="${cx}" cy="${cy}" r="${round(face)}" fill="none" stroke="url(#${id}-rim)" stroke-width="${round(
    Math.max(1.4, r * 0.05),
  )}" opacity=".62"/>
  <circle cx="${cx}" cy="${cy}" r="${round(face * 0.2)}" fill="#0B0F13" stroke="url(#${id}-rim)" stroke-width="${round(
    Math.max(1, r * 0.02),
  )}" opacity=".9"/>
</g>`;
}

function carGroup(variant, { paint = "gloss", accent = ACCENTS.steel, swirls = false } = {}) {
  const b = BODIES[variant];
  const gloss = paint === "gloss";
  const arches = b.wheels
    .map(
      (w) =>
        `<path d="M ${round(w.cx - w.r - 10)} ${w.cy} A ${round(w.r + 10)} ${round(w.r + 10)} 0 0 1 ${round(
          w.cx + w.r + 10,
        )} ${w.cy}" fill="none" stroke="#ffffff" stroke-width="2" opacity="${gloss ? ".22" : ".1"}"/>`,
    )
    .join("\n  ");

  const swirlLayer = swirls
    ? `<g clip-path="url(#body-clip-${variant})" opacity=".5">${Array.from({ length: 26 }, (_, i) => {
        const r2 = rng(i + 11);
        const cx = 260 + r2() * 1100;
        const cy = 470 + r2() * 180;
        const rr = 26 + r2() * 54;
        return `<circle cx="${round(cx)}" cy="${round(cy)}" r="${round(rr)}" fill="none" stroke="#ffffff" stroke-width=".9" opacity=".14"/>`;
      }).join("")}</g>`
    : "";

  return `<g id="car-${variant}">
  <path d="${b.body}" fill="url(#paint-${variant})"/>
  <path d="${b.body}" fill="url(#sheen-${variant})" opacity="${gloss ? ".9" : ".35"}"/>
  ${gloss ? "" : `<path d="${b.body}" fill="#8C97A2" opacity=".07"/>`}
  ${swirlLayer}
  <path d="${b.glass}" fill="url(#glass-${variant})"/>
  ${b.pillars.map((p) => `<path d="${p}" stroke="#05070A" stroke-width="6" opacity=".8" fill="none"/>`).join("\n  ")}
  <path d="${b.glass}" fill="none" stroke="#ffffff" stroke-width="1.4" opacity="${gloss ? ".3" : ".15"}"/>
  <path d="${b.roofline}" fill="none" stroke="#ffffff" stroke-width="3" opacity="${gloss ? ".42" : ".16"}" stroke-linecap="round"/>
  <path d="${b.shoulder}" fill="none" stroke="url(#spec-${variant})" stroke-width="${gloss ? 4 : 2.5}" opacity="${gloss ? ".85" : ".3"}" stroke-linecap="round"/>
  ${arches}
  ${b.wheels.map((w, i) => wheel(w, `wh-${variant}-${i}`, { caliper: accent })).join("\n  ")}
</g>`;
}

function carDefs(variant, { paint = "gloss", accent = ACCENTS.steel } = {}) {
  const b = BODIES[variant];
  const gloss = paint === "gloss";
  const wheelDefs = b.wheels
    .map(
      (_, i) => `<radialGradient id="wh-${variant}-${i}-disc" cx="38%" cy="30%" r="80%">
    <stop offset="0" stop-color="#3A424B"/><stop offset=".55" stop-color="#1A1F25"/><stop offset="1" stop-color="#0A0D10"/>
  </radialGradient>
  <linearGradient id="wh-${variant}-${i}-rim" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#E4EAF0"/><stop offset=".5" stop-color="#8D98A3"/><stop offset="1" stop-color="#4A535C"/>
  </linearGradient>`,
    )
    .join("\n  ");

  return `<linearGradient id="paint-${variant}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${gloss ? "#2B333B" : "#242A30"}"/>
    <stop offset=".38" stop-color="${gloss ? "#13181D" : "#171B1F"}"/>
    <stop offset=".72" stop-color="${gloss ? "#0A0E12" : "#121519"}"/>
    <stop offset="1" stop-color="${gloss ? "#161C22" : "#15181B"}"/>
  </linearGradient>
  <linearGradient id="sheen-${variant}" x1=".1" y1="0" x2=".9" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".14"/>
    <stop offset=".28" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset=".62" stop-color="${accent}" stop-opacity=".07"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity=".05"/>
  </linearGradient>
  <linearGradient id="glass-${variant}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#28313A"/><stop offset=".5" stop-color="#10161C"/><stop offset="1" stop-color="#070A0D"/>
  </linearGradient>
  <linearGradient id="spec-${variant}" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset=".22" stop-color="#ffffff" stop-opacity=".9"/>
    <stop offset=".55" stop-color="${accent}" stop-opacity=".55"/>
    <stop offset=".85" stop-color="#ffffff" stop-opacity=".65"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="body-clip-${variant}"><path d="${b.body}"/></clipPath>
  ${wheelDefs}`;
}

/* -------------------------------------------------------- shared scene bits */

function grainDefs(id = "grain", freq = 0.8, opacity = 0.055) {
  return {
    defs: `<filter id="${id}-f" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="${freq}" numOctaves="3" stitchTiles="stitch"/>
    <feColorMatrix type="saturate" values="0"/>
  </filter>
  <pattern id="${id}" width="220" height="220" patternUnits="userSpaceOnUse">
    <rect width="220" height="220" filter="url(#${id}-f)" opacity="${opacity}"/>
  </pattern>`,
    rect: (w, h, x = 0, y = 0) =>
      `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="url(#${id})" style="mix-blend-mode:overlay"/>`,
  };
}

function svg(width, height, viewBox, body, defs) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="${viewBox}" fill="none" role="img">
<defs>
  ${defs}
</defs>
${body}
</svg>
`;
}

/**
 * Dark photo-studio scene: lighting rig above, gradient floor, mirrored
 * reflection of the car and a soft vignette.
 */
function studioScene({
  variant = "coupe",
  accent = ACCENTS.steel,
  paint = "gloss",
  swirls = false,
  viewBox = "0 0 1600 900",
  width = 1600,
  height = 900,
  rigTint = null,
} = {}) {
  const tint = rigTint || accent;
  const grain = grainDefs("g", 0.85, 0.05);
  const defs = `${carDefs(variant, { paint, accent })}
  <radialGradient id="room" cx="50%" cy="34%" r="78%">
    <stop offset="0" stop-color="#1A2027"/><stop offset=".52" stop-color="#0C0F13"/><stop offset="1" stop-color="${INK.void}"/>
  </radialGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#141A20"/><stop offset=".45" stop-color="#0B0E12"/><stop offset="1" stop-color="#06080A"/>
  </linearGradient>
  <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".5"/>
    <stop offset=".45" stop-color="#ffffff" stop-opacity=".12"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <mask id="reflect-mask"><rect x="0" y="${GROUND}" width="1600" height="420" fill="url(#fade)"/></mask>
  <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="${tint}" stop-opacity="0"/>
    <stop offset=".5" stop-color="#ffffff" stop-opacity=".72"/>
    <stop offset="1" stop-color="${tint}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="pool" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".13"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="contact" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#000000" stop-opacity=".85"/><stop offset="1" stop-color="#000000" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="vig" cx="50%" cy="45%" r="72%">
    <stop offset=".55" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".72"/>
  </radialGradient>
  <filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="26"/></filter>
  <filter id="mirror" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="5"/></filter>
  ${grain.defs}`;

  const body = `<rect width="1600" height="900" fill="url(#room)"/>
<rect y="${GROUND}" width="1600" height="${900 - GROUND}" fill="url(#floor)"/>
<g filter="url(#soft)" opacity=".9">
  <rect x="150" y="96" width="1300" height="14" rx="7" fill="url(#bar)"/>
  <rect x="340" y="176" width="920" height="10" rx="5" fill="url(#bar)" opacity=".65"/>
  <ellipse cx="380" cy="330" rx="330" ry="200" fill="url(#pool)"/>
  <ellipse cx="1240" cy="300" rx="300" ry="180" fill="url(#pool)"/>
</g>
<ellipse cx="800" cy="${GROUND + 6}" rx="700" ry="60" fill="url(#pool)" opacity=".55"/>
<g mask="url(#reflect-mask)" opacity="${paint === "gloss" ? ".44" : ".16"}" filter="url(#mirror)">
  <use href="#car-${variant}" transform="translate(0 ${GROUND * 2}) scale(1 -1)"/>
</g>
<ellipse cx="800" cy="${GROUND + 4}" rx="600" ry="30" fill="url(#contact)"/>
${BODIES[variant].wheels
  .map((w) => `<ellipse cx="${w.cx}" cy="${GROUND + 2}" rx="${round(w.r * 1.1)}" ry="18" fill="url(#contact)"/>`)
  .join("\n")}
${carGroup(variant, { paint, accent, swirls })}
${grain.rect(1600, 900)}
<rect width="1600" height="900" fill="url(#vig)"/>`;

  return svg(width, height, viewBox, body, defs);
}

/* ------------------------------------------------------------ macro styles */

/** Glossy coated panel with water beading — the ceramic-coating signature shot. */
function beadingScene({ accent = ACCENTS.ice, width = 1200, height = 800, count = 46, seed = 7 } = {}) {
  const r = rng(seed);
  const grain = grainDefs("g", 1.1, 0.045);
  const drops = [];
  for (let i = 0; i < count; i += 1) {
    const cx = r() * 1200;
    const cy = 60 + r() * 740;
    const rad = 7 + Math.pow(r(), 2.1) * 46;
    const blur = rad > 34 ? ' filter="url(#dof)"' : "";
    drops.push(`<g${blur}>
    <ellipse cx="${round(cx)}" cy="${round(cy + rad * 0.14)}" rx="${round(rad * 1.02)}" ry="${round(rad * 0.9)}" fill="#000" opacity=".45"/>
    <circle cx="${round(cx)}" cy="${round(cy)}" r="${round(rad)}" fill="url(#drop)"/>
    <circle cx="${round(cx)}" cy="${round(cy)}" r="${round(rad)}" fill="none" stroke="#ffffff" stroke-width="1" opacity=".28"/>
    <ellipse cx="${round(cx - rad * 0.34)}" cy="${round(cy - rad * 0.38)}" rx="${round(rad * 0.24)}" ry="${round(rad * 0.17)}" fill="#ffffff" opacity=".8" transform="rotate(-30 ${round(cx - rad * 0.34)} ${round(cy - rad * 0.38)})"/>
    <path d="M ${round(cx - rad * 0.62)} ${round(cy + rad * 0.5)} A ${round(rad)} ${round(rad)} 0 0 0 ${round(cx + rad * 0.68)} ${round(cy + rad * 0.42)}" stroke="${accent}" stroke-width="${round(Math.max(1, rad * 0.09))}" opacity=".55" fill="none"/>
  </g>`);
  }
  const defs = `<linearGradient id="panel" x1=".1" y1="0" x2=".9" y2="1">
    <stop offset="0" stop-color="#161C22"/><stop offset=".42" stop-color="#0A0D11"/><stop offset="1" stop-color="#05070A"/>
  </linearGradient>
  <linearGradient id="sweep" x1="0" y1="0" x2="1" y2=".8">
    <stop offset=".12" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset=".38" stop-color="${accent}" stop-opacity=".22"/>
    <stop offset=".52" stop-color="#ffffff" stop-opacity=".16"/>
    <stop offset=".78" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="drop" cx="36%" cy="30%" r="76%">
    <stop offset="0" stop-color="#5C6C7A" stop-opacity=".95"/>
    <stop offset=".45" stop-color="#1B2229" stop-opacity=".9"/>
    <stop offset="1" stop-color="#080B0E" stop-opacity=".95"/>
  </radialGradient>
  <radialGradient id="vig" cx="50%" cy="45%" r="72%">
    <stop offset=".5" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".62"/>
  </radialGradient>
  <filter id="dof" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3.2"/></filter>
  ${grain.defs}`;
  const body = `<rect width="1200" height="800" fill="url(#panel)"/>
<rect width="1200" height="800" fill="url(#sweep)"/>
${drops.join("\n")}
${grain.rect(1200, 800)}
<rect width="1200" height="800" fill="url(#vig)"/>`;
  return svg(width, height, "0 0 1200 800", body, defs);
}

/** Split panel: swirled, oxidised clear coat on the left, corrected gloss right. */
function correctionScene({ accent = ACCENTS.gold, width = 1200, height = 800, seed = 3 } = {}) {
  const r = rng(seed);
  const swirls = Array.from({ length: 120 }, () => {
    const cx = r() * 620;
    const cy = r() * 800;
    const rad = 12 + r() * 70;
    const a0 = r() * 360;
    return `<path d="M ${round(cx + rad)} ${round(cy)} A ${round(rad)} ${round(rad)} 0 0 1 ${round(
      cx - rad * 0.2,
    )} ${round(cy + rad * 0.95)}" stroke="#ffffff" stroke-width=".9" opacity="${round(0.1 + r() * 0.2)}" fill="none" transform="rotate(${round(a0)} ${round(cx)} ${round(cy)})"/>`;
  }).join("\n");
  const grain = grainDefs("g", 1.0, 0.05);
  const defs = `<linearGradient id="dull" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#191E23"/><stop offset="1" stop-color="#0D1114"/>
  </linearGradient>
  <linearGradient id="clean" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#222A32"/><stop offset=".4" stop-color="#0A0E12"/><stop offset="1" stop-color="#141A20"/>
  </linearGradient>
  <linearGradient id="hot" x1="0" y1="0" x2="1" y2=".6">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset=".45" stop-color="#ffffff" stop-opacity=".2"/>
    <stop offset=".6" stop-color="${accent}" stop-opacity=".2"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="vig" cx="50%" cy="48%" r="72%">
    <stop offset=".5" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".6"/>
  </radialGradient>
  <filter id="edge" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="8"/></filter>
  ${grain.defs}`;
  const body = `<rect width="1200" height="800" fill="url(#clean)"/>
<rect width="620" height="800" fill="url(#dull)"/>
<g clip-path="url(#half)">${swirls}</g>
<clipPath id="half"><rect width="620" height="800"/></clipPath>
<rect x="600" width="1200" height="800" fill="url(#hot)"/>
<rect x="612" width="16" height="800" fill="#ffffff" opacity=".1" filter="url(#edge)"/>
<rect x="619" width="2" height="800" fill="${accent}" opacity=".55"/>
${grain.rect(1200, 800)}
<rect width="1200" height="800" fill="url(#vig)"/>`;
  return svg(width, height, "0 0 1200 800", body, defs);
}

/** Nappa leather macro with stitch lines — interior work. */
function leatherScene({ accent = ACCENTS.ember, width = 1200, height = 800, seed = 21, tone = "black" } = {}) {
  const r = rng(seed);
  const base = tone === "tan" ? ["#4A3626", "#2A1D14", "#160F0A"] : ["#22262A", "#121518", "#080A0C"];
  const cells = Array.from({ length: 210 }, () => {
    const cx = r() * 1200;
    const cy = r() * 800;
    const rad = 16 + r() * 30;
    return `<circle cx="${round(cx)}" cy="${round(cy)}" r="${round(rad)}" fill="none" stroke="#ffffff" stroke-width="1" opacity="${round(
      0.04 + r() * 0.06,
    )}"/>`;
  }).join("");
  const grain = grainDefs("g", 1.6, 0.14);
  const defs = `<linearGradient id="hide" x1=".15" y1="0" x2=".85" y2="1">
    <stop offset="0" stop-color="${base[0]}"/><stop offset=".5" stop-color="${base[1]}"/><stop offset="1" stop-color="${base[2]}"/>
  </linearGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="1" y2=".5">
    <stop offset=".1" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset=".4" stop-color="#ffffff" stop-opacity=".1"/>
    <stop offset=".7" stop-color="${accent}" stop-opacity=".08"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="vig" cx="50%" cy="45%" r="70%">
    <stop offset=".45" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".66"/>
  </radialGradient>
  <filter id="bump" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="4" seed="${seed}" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="26" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
  ${grain.defs}`;
  const body = `<rect width="1200" height="800" fill="url(#hide)"/>
<g filter="url(#bump)">${cells}</g>
<g opacity=".85">
  <path d="M 0 250 C 320 226 880 226 1200 254" stroke="${accent}" stroke-width="3" stroke-dasharray="18 16" opacity=".5" fill="none"/>
  <path d="M 0 292 C 320 268 880 268 1200 296" stroke="${accent}" stroke-width="3" stroke-dasharray="18 16" opacity=".5" fill="none"/>
  <path d="M 0 262 C 320 238 880 238 1200 266" stroke="#000000" stroke-width="26" opacity=".28" fill="none"/>
</g>
<rect width="1200" height="800" fill="url(#sheen)"/>
${grain.rect(1200, 800)}
<rect width="1200" height="800" fill="url(#vig)"/>`;
  return svg(width, height, "0 0 1200 800", body, defs);
}

/** Protective-film / carbon weave surface with a peeling light edge. */
function filmScene({ accent = ACCENTS.ice, width = 1200, height = 800 } = {}) {
  const grain = grainDefs("g", 1.2, 0.05);
  const defs = `<linearGradient id="base" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#171C21"/><stop offset=".5" stop-color="#0A0D10"/><stop offset="1" stop-color="#12171C"/>
  </linearGradient>
  <pattern id="weave" width="48" height="48" patternUnits="userSpaceOnUse" patternTransform="rotate(30)">
    <rect width="48" height="48" fill="#0B0E11"/>
    <rect width="24" height="24" fill="#161B20"/>
    <rect x="24" y="24" width="24" height="24" fill="#161B20"/>
    <rect width="24" height="24" fill="url(#wg)" opacity=".7"/>
    <rect x="24" y="24" width="24" height="24" fill="url(#wg)" opacity=".7"/>
  </pattern>
  <linearGradient id="wg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#39424B"/><stop offset="1" stop-color="#0D1013"/>
  </linearGradient>
  <linearGradient id="filmEdge" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#ffffff" stop-opacity=".85"/>
    <stop offset="1" stop-color="${accent}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="lift" x1="0" y1="0" x2=".6" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".2"/>
    <stop offset=".6" stop-color="${accent}" stop-opacity=".08"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="vig" cx="50%" cy="45%" r="72%">
    <stop offset=".5" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".64"/>
  </radialGradient>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="10"/></filter>
  ${grain.defs}`;
  const body = `<rect width="1200" height="800" fill="url(#base)"/>
<rect width="1200" height="800" fill="url(#weave)" opacity=".5"/>
<path d="M 0 470 C 260 402 560 382 830 402 C 1000 414 1120 442 1200 470 L 1200 800 L 0 800 Z" fill="#06080B" opacity=".92"/>
<path d="M 0 470 C 260 402 560 382 830 402 C 1000 414 1120 442 1200 470" stroke="url(#filmEdge)" stroke-width="3" fill="none"/>
<path d="M 0 470 C 260 402 560 382 830 402 C 1000 414 1120 442 1200 470 L 1200 560 C 1080 520 860 486 640 484 C 400 482 180 520 0 566 Z" fill="url(#lift)"/>
<ellipse cx="600" cy="180" rx="640" ry="150" fill="#ffffff" opacity=".05" filter="url(#soft)"/>
${grain.rect(1200, 800)}
<rect width="1200" height="800" fill="url(#vig)"/>`;
  return svg(width, height, "0 0 1200 800", body, defs);
}

/** Tinted glass panel seen against a bright exterior. */
function tintScene({ accent = ACCENTS.ice, width = 1200, height = 800 } = {}) {
  const grain = grainDefs("g", 1.0, 0.04);
  const defs = `<linearGradient id="outside" x1="0" y1="0" x2=".4" y2="1">
    <stop offset="0" stop-color="#63707C"/><stop offset=".45" stop-color="#2A333C"/><stop offset="1" stop-color="#101519"/>
  </linearGradient>
  <linearGradient id="film" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#05070A" stop-opacity=".92"/><stop offset="1" stop-color="#05070A" stop-opacity=".72"/>
  </linearGradient>
  <linearGradient id="ref" x1="0" y1="0" x2="1" y2="1">
    <stop offset=".1" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset=".34" stop-color="#ffffff" stop-opacity=".2"/>
    <stop offset=".4" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset=".62" stop-color="${accent}" stop-opacity=".14"/>
    <stop offset=".7" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="vig" cx="50%" cy="45%" r="72%">
    <stop offset=".5" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".6"/>
  </radialGradient>
  ${grain.defs}`;
  const body = `<rect width="1200" height="800" fill="url(#outside)"/>
<g opacity=".5">
  <rect x="70" y="330" width="190" height="300" fill="#0B0F13"/>
  <rect x="330" y="250" width="150" height="380" fill="#0E1317"/>
  <rect x="560" y="300" width="220" height="330" fill="#0A0E12"/>
  <rect x="850" y="220" width="170" height="410" fill="#0D1216"/>
</g>
<path d="M 120 120 L 1080 120 L 1140 700 L 60 700 Z" fill="url(#film)"/>
<path d="M 120 120 L 1080 120 L 1140 700 L 60 700 Z" fill="url(#ref)"/>
<path d="M 120 120 L 1080 120 L 1140 700 L 60 700 Z" stroke="#ffffff" stroke-opacity=".22" stroke-width="2" fill="none"/>
<path d="M 128 138 L 1068 138" stroke="${accent}" stroke-opacity=".35" stroke-width="3"/>
${grain.rect(1200, 800)}
<rect width="1200" height="800" fill="url(#vig)"/>`;
  return svg(width, height, "0 0 1200 800", body, defs);
}

/** Restored projector headlight with a beam. */
function headlightScene({ accent = ACCENTS.ice, width = 1200, height = 800 } = {}) {
  const grain = grainDefs("g", 1.0, 0.05);
  const defs = `<linearGradient id="body" x1="0" y1="0" x2=".6" y2="1">
    <stop offset="0" stop-color="#1B2128"/><stop offset=".55" stop-color="#0B0E12"/><stop offset="1" stop-color="#05070A"/>
  </linearGradient>
  <radialGradient id="lens" cx="42%" cy="36%" r="70%">
    <stop offset="0" stop-color="#E8F1F8"/><stop offset=".26" stop-color="${accent}" stop-opacity=".8"/>
    <stop offset=".55" stop-color="#1E2932" stop-opacity=".9"/><stop offset="1" stop-color="#080B0E"/>
  </radialGradient>
  <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".38"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="vig" cx="42%" cy="42%" r="72%">
    <stop offset=".45" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".68"/>
  </radialGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="34"/></filter>
  <filter id="soft" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="14"/></filter>
  ${grain.defs}`;
  const rings = Array.from(
    { length: 6 },
    (_, i) =>
      `<ellipse cx="430" cy="400" rx="${240 - i * 34}" ry="${210 - i * 30}" fill="none" stroke="#ffffff" stroke-width="1.4" opacity="${round(
        0.05 + i * 0.035,
      )}"/>`,
  ).join("");
  const body = `<rect width="1200" height="800" fill="url(#body)"/>
<path d="M 640 250 L 1200 96 L 1200 700 L 640 552 Z" fill="url(#beam)" filter="url(#soft)" opacity=".55"/>
<ellipse cx="430" cy="400" rx="330" ry="290" fill="#0A0E12"/>
<ellipse cx="430" cy="400" rx="300" ry="262" fill="url(#lens)"/>
${rings}
<ellipse cx="382" cy="330" rx="86" ry="60" fill="#ffffff" opacity=".55" filter="url(#soft)"/>
<ellipse cx="430" cy="400" rx="110" ry="96" fill="#ffffff" opacity=".34" filter="url(#glow)"/>
<ellipse cx="430" cy="400" rx="330" ry="290" fill="none" stroke="#ffffff" stroke-opacity=".2" stroke-width="3"/>
${grain.rect(1200, 800)}
<rect width="1200" height="800" fill="url(#vig)"/>`;
  return svg(width, height, "0 0 1200 800", body, defs);
}

/** Forged wheel close-up with caliper — wheel & brake protection. */
function wheelScene({ accent = ACCENTS.gold, width = 1200, height = 800 } = {}) {
  const grain = grainDefs("g", 0.95, 0.05);
  const defs = `<radialGradient id="bay" cx="50%" cy="40%" r="75%">
    <stop offset="0" stop-color="#1A2027"/><stop offset=".55" stop-color="#0A0D11"/><stop offset="1" stop-color="#050708"/>
  </radialGradient>
  <radialGradient id="wh-x-disc" cx="38%" cy="30%" r="80%">
    <stop offset="0" stop-color="#3E4750"/><stop offset=".55" stop-color="#1A1F25"/><stop offset="1" stop-color="#0A0D10"/>
  </radialGradient>
  <linearGradient id="wh-x-rim" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#EDF2F7"/><stop offset=".5" stop-color="#909BA6"/><stop offset="1" stop-color="#454E57"/>
  </linearGradient>
  <radialGradient id="vig" cx="50%" cy="45%" r="70%">
    <stop offset=".45" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".68"/>
  </radialGradient>
  <radialGradient id="pool" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".14"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </radialGradient>
  ${grain.defs}`;
  const body = `<rect width="1200" height="800" fill="url(#bay)"/>
<ellipse cx="520" cy="180" rx="520" ry="200" fill="url(#pool)"/>
<path d="M 0 120 C 300 60 900 60 1200 130 L 1200 800 L 0 800 Z" fill="#080B0E" opacity=".55"/>
${wheel({ cx: 600, cy: 400, r: 300 }, "wh-x", { caliper: accent })}
<ellipse cx="600" cy="740" rx="330" ry="34" fill="#000000" opacity=".6"/>
${grain.rect(1200, 800)}
<rect width="1200" height="800" fill="url(#vig)"/>`;
  return svg(width, height, "0 0 1200 800", body, defs);
}

/** Cabin at night: dashboard sweep, vents, ambient light line. */
function interiorScene({ accent = ACCENTS.ember, width = 1200, height = 800 } = {}) {
  const grain = grainDefs("g", 1.1, 0.06);
  const defs = `<linearGradient id="cabin" x1=".2" y1="0" x2=".8" y2="1">
    <stop offset="0" stop-color="#1C222A"/><stop offset=".45" stop-color="#0C1014"/><stop offset="1" stop-color="#05070A"/>
  </linearGradient>
  <linearGradient id="dash" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#232A32"/><stop offset="1" stop-color="#0A0D11"/>
  </linearGradient>
  <linearGradient id="amb" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="${accent}" stop-opacity="0"/>
    <stop offset=".45" stop-color="${accent}" stop-opacity=".9"/>
    <stop offset="1" stop-color="${accent}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="screen" cx="50%" cy="40%" r="70%">
    <stop offset="0" stop-color="#2E3A46"/><stop offset="1" stop-color="#0A0E12"/>
  </radialGradient>
  <radialGradient id="vig" cx="50%" cy="45%" r="70%">
    <stop offset=".45" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity=".7"/>
  </radialGradient>
  <filter id="soft" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="18"/></filter>
  ${grain.defs}`;
  const body = `<rect width="1200" height="800" fill="url(#cabin)"/>
<path d="M -40 300 C 260 236 900 232 1240 306 L 1240 620 C 900 556 260 560 -40 626 Z" fill="url(#dash)"/>
<path d="M -40 300 C 260 236 900 232 1240 306" stroke="#ffffff" stroke-opacity=".16" stroke-width="2.5" fill="none"/>
<path d="M -40 352 C 260 288 900 284 1240 358" stroke="url(#amb)" stroke-width="5" fill="none" opacity=".8"/>
<path d="M -40 352 C 260 288 900 284 1240 358" stroke="url(#amb)" stroke-width="18" fill="none" opacity=".28" filter="url(#soft)"/>
<rect x="368" y="392" width="470" height="210" rx="14" fill="url(#screen)"/>
<rect x="368" y="392" width="470" height="210" rx="14" fill="none" stroke="#ffffff" stroke-opacity=".14" stroke-width="2"/>
<rect x="400" y="424" width="180" height="10" rx="5" fill="#ffffff" opacity=".28"/>
<rect x="400" y="452" width="300" height="8" rx="4" fill="#ffffff" opacity=".14"/>
<rect x="400" y="474" width="240" height="8" rx="4" fill="#ffffff" opacity=".1"/>
<g opacity=".85">
  <rect x="120" y="430" width="170" height="56" rx="28" fill="#0A0D11" stroke="#ffffff" stroke-opacity=".1"/>
  <rect x="920" y="430" width="170" height="56" rx="28" fill="#0A0D11" stroke="#ffffff" stroke-opacity=".1"/>
</g>
<ellipse cx="600" cy="150" rx="560" ry="130" fill="#ffffff" opacity=".05" filter="url(#soft)"/>
${grain.rect(1200, 800)}
<rect width="1200" height="800" fill="url(#vig)"/>`;
  return svg(width, height, "0 0 1200 800", body, defs);
}

/* ------------------------------------------------------------------ output */

const CROP = {
  wide: "0 0 1600 900",
  full: "190 70 1230 820",
  rear: "200 280 930 620",
  front: "620 290 930 620",
  low: "260 420 1200 480",
};

const MANIFEST = {
  // Hero + section imagery
  "hero-studio.svg": () =>
    studioScene({ variant: "coupe", accent: ACCENTS.gold, viewBox: CROP.wide, width: 1600, height: 900 }),
  "showcase-suv.svg": () =>
    studioScene({ variant: "suv", accent: ACCENTS.ice, viewBox: CROP.full, width: 1230, height: 820 }),

  // Service cards
  "service/ceramic-coating.svg": () => beadingScene({ accent: ACCENTS.ice, seed: 7 }),
  "service/paint-protection-film.svg": () => filmScene({ accent: ACCENTS.ice }),
  "service/full-body-ppf.svg": () =>
    studioScene({ variant: "coupe", accent: ACCENTS.ice, viewBox: CROP.full, width: 1200, height: 800 }),
  "service/partial-ppf.svg": () => filmScene({ accent: ACCENTS.gold }),
  "service/paint-correction.svg": () => correctionScene({ accent: ACCENTS.gold, seed: 3 }),
  "service/interior-detailing.svg": () => interiorScene({ accent: ACCENTS.ember }),
  "service/exterior-detailing.svg": () =>
    studioScene({ variant: "sedan", accent: ACCENTS.steel, viewBox: CROP.rear, width: 1200, height: 800 }),
  "service/full-detailing.svg": () =>
    studioScene({ variant: "suv", accent: ACCENTS.gold, viewBox: CROP.front, width: 1200, height: 800 }),
  "service/window-tinting.svg": () => tintScene({ accent: ACCENTS.ice }),
  "service/wheel-protection.svg": () => wheelScene({ accent: ACCENTS.gold }),
  "service/leather-protection.svg": () => leatherScene({ accent: ACCENTS.ember, tone: "tan", seed: 21 }),
  "service/headlight-restoration.svg": () => headlightScene({ accent: ACCENTS.ice }),

  // Before / after pairs
  "compare/paint-before.svg": () =>
    studioScene({ variant: "sedan", accent: ACCENTS.steel, paint: "dull", swirls: true, viewBox: CROP.full, width: 1230, height: 820 }),
  "compare/paint-after.svg": () =>
    studioScene({ variant: "sedan", accent: ACCENTS.gold, paint: "gloss", viewBox: CROP.full, width: 1230, height: 820 }),
  "compare/coupe-before.svg": () =>
    studioScene({ variant: "coupe", accent: ACCENTS.steel, paint: "dull", swirls: true, viewBox: CROP.rear, width: 1200, height: 800 }),
  "compare/coupe-after.svg": () =>
    studioScene({ variant: "coupe", accent: ACCENTS.ice, paint: "gloss", viewBox: CROP.rear, width: 1200, height: 800 }),
  "compare/suv-before.svg": () =>
    studioScene({ variant: "suv", accent: ACCENTS.steel, paint: "dull", swirls: true, viewBox: CROP.front, width: 1200, height: 800 }),
  "compare/suv-after.svg": () =>
    studioScene({ variant: "suv", accent: ACCENTS.gold, paint: "gloss", viewBox: CROP.front, width: 1200, height: 800 }),

  // Gallery
  "gallery/g-01.svg": () => correctionScene({ accent: ACCENTS.gold, seed: 3 }),
  "gallery/g-02.svg": () => beadingScene({ accent: ACCENTS.ice, seed: 13, count: 54 }),
  "gallery/g-03.svg": () => filmScene({ accent: ACCENTS.ice }),
  "gallery/g-04.svg": () => interiorScene({ accent: ACCENTS.ember }),
  "gallery/g-05.svg": () =>
    studioScene({ variant: "sedan", accent: ACCENTS.gold, viewBox: CROP.full, width: 1200, height: 800 }),
  "gallery/g-06.svg": () => beadingScene({ accent: ACCENTS.gold, seed: 41, count: 38 }),
  "gallery/g-07.svg": () =>
    studioScene({ variant: "coupe", accent: ACCENTS.ice, viewBox: CROP.front, width: 1200, height: 800 }),
  "gallery/g-08.svg": () => leatherScene({ accent: ACCENTS.steel, tone: "black", seed: 5 }),
  "gallery/g-09.svg": () => correctionScene({ accent: ACCENTS.ice, seed: 29 }),
  "gallery/g-10.svg": () =>
    studioScene({ variant: "suv", accent: ACCENTS.gold, viewBox: CROP.full, width: 1200, height: 800 }),
  "gallery/g-11.svg": () => wheelScene({ accent: ACCENTS.ice }),
  "gallery/g-12.svg": () => tintScene({ accent: ACCENTS.steel }),
  "gallery/g-13.svg": () =>
    studioScene({ variant: "coupe", accent: ACCENTS.gold, viewBox: CROP.low, width: 1200, height: 480 }),
  "gallery/g-14.svg": () => headlightScene({ accent: ACCENTS.ice }),
  "gallery/g-15.svg": () => leatherScene({ accent: ACCENTS.ember, tone: "tan", seed: 61 }),
  "gallery/g-16.svg": () =>
    studioScene({ variant: "sedan", accent: ACCENTS.ice, viewBox: CROP.rear, width: 1200, height: 800 }),

  // About
  "about/bay.svg": () =>
    studioScene({ variant: "coupe", accent: ACCENTS.gold, viewBox: CROP.wide, width: 1600, height: 900, rigTint: ACCENTS.ember }),
  "about/craft.svg": () => correctionScene({ accent: ACCENTS.ice, seed: 77 }),
  "about/materials.svg": () => beadingScene({ accent: ACCENTS.gold, seed: 91, count: 32 }),
};

rmSync(OUT, { recursive: true, force: true });
let bytes = 0;
for (const [name, make] of Object.entries(MANIFEST)) {
  const file = join(OUT, name);
  mkdirSync(dirname(file), { recursive: true });
  const content = make();
  writeFileSync(file, content, "utf8");
  bytes += Buffer.byteLength(content);
}
console.log(
  `Generated ${Object.keys(MANIFEST).length} artwork files (${(bytes / 1024).toFixed(1)} kB) into public/media`,
);
