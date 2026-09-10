#!/usr/bin/env node
/**
 * Builds the service catalogue shown on /services and the home page from the
 * work lines of every imported project.
 *
 * INPUT  src/content/work/projects.generated.json  (written by import-instagram.mjs)
 *        src/content/work/selection.json           (category names and order)
 * OUTPUT src/content/work/services.generated.json  (what the site renders)
 *
 * The studio's posts describe the same service in many ways ("Бронювання
 * внутрішніх прорізів дверей", "Обклеювання внутрішніх прорізів дверей",
 * "Дверні прорізи" …). Each rule below maps every such wording onto one
 * canonical service, so the catalogue never repeats itself. Rules are tried in
 * order and the first match wins — keep specific rules above generic ones.
 *
 * Every canonical name is taken from the wording the studio itself uses in
 * its posts; no service is listed here that does not appear in a project.
 * Lines that are not services (a colour code, a layer count, a sub-list)
 * are in SKIP and are ignored.
 *
 * Run:  npm run work:services
 * Re-run it after every Instagram import. Lines no rule recognises are
 * printed at the end and stored under "unmatched" — add a rule for them.
 */

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const ROOT = resolve(new URL("..", import.meta.url).pathname);
const PROJECTS = resolve(ROOT, "src/content/work/projects.generated.json");
const SELECTION = resolve(ROOT, "src/content/work/selection.json");
const OUT = resolve(ROOT, "src/content/work/services.generated.json");

/* ── Lines that are details of a service, not a service ─────────────────── */

const SKIP = [
  /^\(/, // "(підлога, багажник, двері …)" — a sub-list of the line above
  /^колір /i,
  /— \d+ шар/i,
  /^помаранчевий колір|^чорний — |^чорний поліуретан \(|^вінілова плівка золотий/i,
  /^ліврею розроблено/i,
  /^кастомні дизайнерські/i,
];

/* ── Canonical services, grouped by the portfolio categories ────────────── */

const RULES = [
  /* Салон — matched first so "салон" wording never falls into body rules */
  { group: "soundproofing", id: "sp-anti-squeak", uk: "Антискрип салону", en: "Cabin anti-squeak treatment", match: [/антискрип/] },
  { group: "soundproofing", id: "sp-doors", uk: "Шумоізоляція дверей", en: "Door soundproofing", match: [/шумоізоляція (чотирьох|двох)? ?дверей/, /шумоізоляція дверей/] },
  { group: "soundproofing", id: "sp-arches", uk: "Шумоізоляція колісних арок", en: "Wheel-arch soundproofing", match: [/шумоізоляція.*ар(ок|ки)/] },
  { group: "soundproofing", id: "sp-boot", uk: "Шумоізоляція багажника", en: "Boot soundproofing", match: [/шумоізоляція багажника/] },
  { group: "soundproofing", id: "sp-full", uk: "Повна шумо- та віброізоляція салону", en: "Full cabin sound and vibration insulation", match: [/шумо/, /вібро/, /звукопоглинач/] },

  { group: "ceramic", id: "ceramic-interior", uk: "Кераміка для шкіри салону", en: "Ceramic coating on interior leather", match: [/керамі.*салон/] },
  { group: "ceramic", id: "ceramic-wheels", uk: "Кераміка на диски", en: "Ceramic coating on the wheels", match: [/керамі.*диск/] },
  { group: "ceramic", id: "ceramic-film", uk: "Керамічне покриття на плівку", en: "Ceramic coating over the film", match: [/керамі.*плівк/] },
  { group: "ceramic", id: "ceramic-glass", uk: "Керамічне покриття кузова та скла", en: "Ceramic coating on the body and glass", match: [/керамі.*скл/] },
  { group: "ceramic", id: "ceramic-body", uk: "Керамічне покриття кузова", en: "Ceramic coating on the body", match: [/керамі/, /кварц/] },

  { group: "styling", id: "st-lighting", uk: "LED-підсвітка салону та «Зоряне небо»", en: "LED ambient lighting and starlight headliner", match: [/підсвіт/, /зоряне небо/] },
  { group: "interior", id: "int-clean", uk: "Хімчистка салону", en: "Interior deep clean", match: [/хімчист/, /вологе прибирання/, /очищення (чотирьох|та захист шкір)/] },
  { group: "interior", id: "int-seats", uk: "Підфарбовування сидінь", en: "Seat re-dyeing", match: [/підфарбовування .*сидін/] },
  { group: "styling", id: "st-interior", uk: "Стайлінг салону: мат, карбон, аквадрук під дерево", en: "Interior trim styling: matte, carbon-effect, hydro-dipped wood", match: [/салону в мат/, /салону карбонов/, /аквадрук/] },
  { group: "interior", id: "int-screens", uk: "Захисне скло на монітори", en: "Tempered screen protectors on the displays", match: [/захисн(е|ого|их) (скл|стек)/, /^захист моніт(ор|ора|орів)( салону| склом| захисним склом)?$/, /^захист інтер'єру/, /центральної консолі/] },
  { group: "interior", id: "int-gloss", uk: "Обклеювання глянцевих елементів салону", en: "Gloss interior trim protection film", match: [/салон/, /інтер'єр/, /чорного глянцю та дерева/, /^чорний глянець салону/, /скляних елементів/, /^бронювання деталей салону/] },

  /* Антихром і шильдики */
  { group: "antichrome", id: "ac-full", uk: "Повний антихром", en: "Full anti-chrome package", match: [/повний антихром/, /антихром (усіх|всіх)/, /^антихром:/] },
  { group: "antichrome", id: "ac-badges", uk: "Антихром шильдиків", en: "Anti-chrome badges", match: [/антихром шильд/, /затемнення шильд/] },
  { group: "antichrome", id: "ac-trim", uk: "Антихром молдингів, накладок і рейлінгів", en: "Anti-chrome mouldings, trims and roof rails", match: [/антихром/] },

  /* Полірування та підготовка — specific paint jobs before generic painting */
  { group: "polish", id: "polish-dents", uk: "Видалення вм'ятин і ремонт сколів", en: "Dent removal and chip repair", match: [/вм'ятин/, /ремонт сколів/, /пошкодження лакофарбового/] },
  { group: "polish", id: "polish-headlights", uk: "Відновлення фар", en: "Headlight restoration", match: [/відновлення фар/] },
  { group: "polish", id: "polish-paintwork", uk: "Малярні роботи по кузову", en: "Body paintwork", match: [/малярн/, /у рідний колір/, /фарбування переднього бампера/] },
  { group: "polish", id: "polish-film-removal", uk: "Демонтаж старої плівки", en: "Old film removal", match: [/демонтаж (старої|кольорової|матової)/] },
  { group: "polish", id: "polish-hull", uk: "Очищення корпусу від сольових відкладень", en: "Hull cleaning from salt deposits", match: [/сольових/] },

  /* Тонування — removal and lights before generic tint */
  { group: "tint", id: "tint-removal", uk: "Зняття старого тонування", en: "Old tint removal", match: [/старого тонування/] },
  { group: "tint", id: "tint-lights", uk: "Затемнення оптики", en: "Tinted lights", match: [/затемнення (передньої|задніх|фар|оптики)/] },
  { group: "tint", id: "tint-rain", uk: "Антидощ на скло", en: "Rain-repellent glass treatment", match: [/антидощ/] },
  { group: "tint", id: "tint-euro", uk: "Євротонування", en: "Rear-glass tint", match: [/євротон/] },
  { group: "styling", id: "st-windscreen", uk: "Заміна лобового скла", en: "Windscreen replacement", match: [/заміна (та тонування )?лобового скла/] },
  { group: "tint", id: "tint-athermal-full", uk: "Повне атермальне тонування", en: "Full athermal window tint", match: [/повне атермальне/, /атермальне тонування (всіх|автомобіля)/, /^атермальне тонування$/, /перетонування атермальною/, /атермальн.*15\/80/] },
  { group: "tint", id: "tint-athermal-front", uk: "Атермальне тонування лобового та передніх стекол", en: "Athermal tint on the windscreen and front windows", match: [/атермальн/] },
  { group: "tint", id: "tint-standard", uk: "Тонування стекол", en: "Window tinting", match: [/тонування/] },

  /* Стайлінг — painting of parts, before body-prep and PPF rules */
  { group: "styling", id: "st-calipers", uk: "Фарбування супортів", en: "Painted brake calipers", match: [/супорт/] },
  { group: "styling", id: "st-wheels", uk: "Фарбування, відновлення та заміна дисків", en: "Wheels painted, refurbished or replaced", match: [/диск/] },
  { group: "styling", id: "st-paint-trim", uk: "Фарбування решітки, шильдиків, дзеркал і накладок", en: "Grille, badges, mirrors and trims painted", match: [/фарбування/] },
  { group: "styling", id: "st-badges", uk: "Заміна шильдиків", en: "Badges replaced", match: [/заміна шильдиків/] },
  { group: "styling", id: "st-softclose", uk: "Встановлення доводчиків дверей", en: "Soft-close doors", match: [/доводчик/] },
  { group: "styling", id: "st-mesh", uk: "Захисна сітка в бампер", en: "Protective mesh in the bumper", match: [/сітк/] },
  { group: "styling", id: "st-exhaust", uk: "Встановлення вихлопної системи Maxhaust", en: "Maxhaust exhaust system", match: [/вихлопн/, /maxhaust/] },
  { group: "styling", id: "st-steering", uk: "Встановлення керма в стилі AMG / M", en: "AMG- and M-style steering wheels", match: [/керм/] },
  { group: "styling", id: "st-audio", uk: "Встановлення аудіосистеми", en: "Audio system installation", match: [/аудіо/] },
  { group: "styling", id: "st-sidesteps", uk: "Встановлення висувних електропорогів", en: "Power-deployable side steps", match: [/електропорог/] },
  { group: "styling", id: "st-security", uk: "Антивандальна плівка на бокові стекла", en: "Security film on the side windows", match: [/антивандал/] },
  { group: "styling", id: "st-bodykit", uk: "Встановлення обвісів і елементів екстер'єру", en: "Body kits and exterior parts fitted", match: [/обвіс/, /обвес/, /бамперів, порогів, дифузора/, /карбонових корпусів/, /заводських пластикових/, /стиль m760/, /заміна решітки/] },

  /* Зміна кольору та дизайн — before clear-PPF rules */
  { group: "color-change", id: "cc-design", uk: "Індивідуальний дизайн і лівреї", en: "Custom liveries and design wraps", match: [/лівре/, /дизайн/, /брендув/, /наклей/, /смуг уздовж/, /акцентн/, /two face/, /логотип/] },
  { group: "color-change", id: "cc-two-tone", uk: "Обклеювання кузова у два кольори", en: "Two-tone wrap", match: [/у два кольори/] },
  { group: "color-change", id: "cc-vinyl", uk: "Обклеювання вініловою плівкою", en: "Vinyl wrap", match: [/вініл/] },
  { group: "color-change", id: "cc-roof", uk: "Обклеювання даху чорним поліуретаном", en: "Roof in black PPF", match: [/даху (чорн|карбон)/] },
  { group: "color-change", id: "cc-trim", uk: "Зміна кольору елементів кузова: капот, спойлер, решітка, накладки", en: "Colour change of body elements: bonnet, spoiler, grille, trims", match: [/капота чорним/, /спойлера чорним/, /заміна кольору сірих накладок/, /карбоновою плівкою/, /карбоновим поліуретаном/, /карбонового корпусу/, /молдингів чорною/, /вставками з кольорового/, /обклеювання чорним поліуретаном$/, /рейлінгів$/] },
  { group: "color-change", id: "cc-full", uk: "Повна заміна кольору кольоровим поліуретаном", en: "Full colour change in colour PPF", match: [/заміна кольору/, /кольоров/, /frozen black/, /чорним (матовим|сатиновим|глянцевим)? ?поліуретаном/, /хромованою плівкою/] },

  /* Захисна плівка — specific zones before full-body */
  { group: "ppf", id: "ppf-correction", uk: "Корекція раніше встановленої плівки", en: "Correction of previously installed film", match: [/корекція.*плівки/] },
  { group: "polish", id: "polish-prep", uk: "Підготовка кузова під обклеювання", en: "Body preparation before wrapping", match: [/підготовк/, /розбирання (кузова|даху)/] },
  { group: "polish", id: "polish-glass", uk: "Полірування лобового скла", en: "Windscreen polishing", match: [/полірування лобового/] },
  { group: "ppf", id: "ppf-lights", uk: "Бронювання оптики", en: "Headlight and tail-light protection film", match: [/бронювання (передньої |задньої )?оптики/, /обклеювання (задньої та передньої|передньої та задньої) оптики/, /оптики та всіх глянцевих/, /стоп-сигналів/, /бронювання фар/] },
  { group: "polish", id: "polish-body", uk: "Полірування кузова", en: "Body polishing and paint correction", match: [/полірув/] },
  { group: "ppf", id: "ppf-windscreen", uk: "Бронювання лобового скла", en: "Windscreen protection film", match: [/бронювання лобового/, /захист лобового скла/, /бронювання панорами, порогів і лобового/] },
  { group: "ppf", id: "ppf-pillars", uk: "Бронювання стійок лобового скла та смуги над лобовим", en: "A-pillars and the strip above the windscreen", match: [/стій(ок|ки) лобового/, /смуг[аи] над лобовим/, /стійок і смуги/, /глянцю над лобовим/] },
  { group: "ppf", id: "ppf-roof", uk: "Бронювання панорамного даху", en: "Panoramic roof protection film", match: [/панорамного даху/] },
  { group: "ppf", id: "ppf-jambs", uk: "Бронювання внутрішніх прорізів дверей", en: "Door-jamb protection film", match: [/проріз/] },
  { group: "ppf", id: "ppf-loading-edge", uk: "Захист полиці заднього бампера", en: "Rear-bumper loading edge protection", match: [/полиц[яі] заднього бампера/] },
  { group: "ppf", id: "ppf-lower", uk: "Бронювання порогів, низу дверей і задніх арок", en: "Sills, lower doors and rear arches protected", match: [/порог/, /низу дверей/, /низу автомобіля/, /задніх арок/, /відбійник/, /накладок дверей/] },
  { group: "ppf", id: "ppf-gloss-exterior", uk: "Бронювання глянцевих елементів кузова", en: "Gloss exterior trim protection film", match: [/глянцевих (елементів|деталей) кузова/, /всіх глянцевих елементів (та оптики|прозорою)/, /глянцевих (бокових |дверних )?стійок/, /глянцеві дверні стійки/, /бокових стійок/, /молдинг/, /решітки сатин/, /окантовка решітки/, /спойлера/] },
  { group: "ppf", id: "ppf-partial", uk: "Часткове бронювання зон ризику", en: "Partial protection film on high-risk areas", match: [/часткове бронювання/, /зон ризику/, /зон під ручками/, /задньої частини/] },
  { group: "ppf", id: "ppf-front", uk: "Бронювання передньої частини", en: "Front-end protection film", match: [/передньої частини/, /фронтальн/, /^бронювання, пакет vip/] },
  { group: "ppf", id: "ppf-full-satin", uk: "Повне обклеювання кузова сатиновим або матовим поліуретаном", en: "Full-body satin or matte PPF", match: [/сатин/, /матов/] },
  { group: "ppf", id: "ppf-full", uk: "Повне обклеювання кузова прозорим поліуретаном", en: "Full-body clear PPF", match: [/повне обклеювання/, /обклеювання (кузова|всіх елементів кузова|лфп|всього)/, /бронювання авто/, /антигравійн/, /повне обклеювання разом із дахом/] },
];

/* ── Build ───────────────────────────────────────────────────────────────── */

const { projects } = JSON.parse(readFileSync(PROJECTS, "utf8"));
const selection = JSON.parse(readFileSync(SELECTION, "utf8"));

const byId = new Map(RULES.map((rule) => [rule.id, { ...rule, projects: new Set(), lines: new Set() }]));
const unmatched = new Map();
const skipped = new Set();

function classify(line) {
  const text = line.toLowerCase().replace(/[’`]/g, "'");
  if (SKIP.some((re) => re.test(text))) return "skip";
  return RULES.find((rule) => rule.match.some((re) => re.test(text)))?.id ?? null;
}

for (const project of projects) {
  if (!project.visible) continue;
  for (const work of project.works ?? []) {
    const id = classify(work.uk);
    if (id === "skip") {
      skipped.add(work.uk);
    } else if (id === null) {
      unmatched.set(work.uk, (unmatched.get(work.uk) ?? 0) + 1);
    } else {
      const entry = byId.get(id);
      entry.projects.add(project.id);
      entry.lines.add(work.uk);
    }
  }
}

const groups = selection.categories.map((category) => ({
  id: category.id,
  uk: category.uk,
  en: category.en,
  services: RULES.filter((rule) => rule.group === category.id)
    .map((rule) => byId.get(rule.id))
    .filter((entry) => entry.projects.size > 0)
    .sort((a, b) => b.projects.size - a.projects.size)
    .map((entry) => ({
      id: entry.id,
      uk: entry.uk,
      en: entry.en,
      projects: entry.projects.size,
      /* Every wording from the posts that this service covers — for review. */
      sources: [...entry.lines].sort(),
    })),
})).filter((group) => group.services.length > 0);

const output = {
  generatedAt: new Date().toISOString(),
  stats: {
    projects: projects.filter((p) => p.visible).length,
    services: groups.reduce((n, g) => n + g.services.length, 0),
    groups: groups.length,
    skippedLines: skipped.size,
    unmatchedLines: unmatched.size,
  },
  groups,
  skipped: [...skipped].sort(),
  unmatched: [...unmatched.entries()].sort((a, b) => b[1] - a[1]).map(([line, n]) => ({ line, projects: n })),
};

writeFileSync(OUT, JSON.stringify(output, null, 2) + "\n");

console.log(JSON.stringify(output.stats, null, 2));
for (const group of groups) {
  console.log(`\n${group.uk} / ${group.en}`);
  for (const s of group.services) console.log(`  ${String(s.projects).padStart(3)}  ${s.uk}  |  ${s.en}`);
}
if (unmatched.size > 0) {
  console.log("\nUnmatched lines (add a rule):");
  for (const { line, projects: n } of output.unmatched) console.log(`  ${n}  ${line}`);
}
