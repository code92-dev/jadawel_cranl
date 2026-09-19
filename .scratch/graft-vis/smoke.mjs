// Smoke test for .scratch/graft-vis: exercises the non-canvas logic paths
// (navigation, search, hotspots, detail panel) with minimal DOM stubs.
import fs from "node:fs";
import vm from "node:vm";

const html = fs.readFileSync(process.argv[2] || ".scratch/graft-vis/index.html", "utf8");
const js = html.match(/<script>([\s\S]*)<\/script>/)[1];

const els = new Map();
const listeners = new Map();
function el(id) {
  if (els.has(id)) return els.get(id);
  const node = {
    id, innerHTML: "", textContent: "", className: "", value: "", dataset: {},
    style: {}, children: [], onclick: null, classList: { add() {}, remove() {}, toggle() {} },
    addEventListener(type, fn) { listeners.set(id + ":" + type, fn); },
    querySelectorAll() { return []; }, querySelector() { return null; },
    closest() { return null; }, getBoundingClientRect() { return { left: 0, top: 0, width: 900, height: 700 }; },
    getContext() { return proxy; },
    appendChild() {},
  };
  els.set(id, node);
  return node;
}
const proxy = new Proxy({}, { get: () => () => {} , set: () => true });
const errors = [];
const sandbox = {
  console,
  document: { getElementById: el, querySelectorAll: () => [], addEventListener() {} },
  window: { addEventListener() {}, devicePixelRatio: 1 },
  location: { hash: "" },
  ResizeObserver: class { observe() {} },
  requestAnimationFrame: () => 0,
  Math, JSON, Set, Map, Array, Object, Number, String, Infinity, isNaN, parseInt,
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
try {
  vm.runInContext(js, sandbox, { filename: "explorer.js" });
} catch (e) {
  errors.push("boot: " + e.stack.split("\n").slice(0, 3).join(" | "));
}
const g = sandbox.window.__graft;
const check = (name, fn) => { try { fn(); console.log("ok   " + name); } catch (e) { errors.push(name + ": " + e.message); console.log("FAIL " + name + " :: " + e.message); } };

check("__graft hook exposed", () => { if (!g) throw new Error("missing window.__graft"); });
check("booted into a dir view", () => {
  if (!g.view.nodes.length) throw new Error("no nodes");
});

const paths = ["", "backend", "backend/src/jadawel", "backend/src/arabase", "web-frontend", "web-frontend/modules/database", "plugins"];
const FILES = vm.runInContext("FILES", sandbox);
const DIRSUB = vm.runInContext("dirSub", sandbox);
const indexed = (d) => (DIRSUB.get(d) || { filesN: 0 }).filesN > 0;

for (const p of paths) {
  check(`buildDirView(${JSON.stringify(p)})`, () => {
    g.buildDirView(p);
    if (!indexed(p)) return; // not part of the graft index (no marker file)
    if (!g.view.nodes.length) throw new Error("empty dir view");
  });
}
// every one of the repo's directories must render without throwing
let dirCount = 0;
const seen = new Set();
for (const n of g.view.nodes) { seen.add(n); }
check("all dirs and their children build", () => {
  const all = [];
  const walk = (p, depth) => { all.push(p); if (depth > 6) return; g.buildDirView(p);
    for (const nd of g.view.nodes) if (nd.kind === "dir" && nd.id !== "__out__") walk(nd.id, depth + 1); };
  walk("", 0);
  dirCount = all.length;
  if (dirCount < 20) throw new Error("expected many dirs, got " + dirCount);
});

const filePaths = ["backend/src/jadawel/core/mixins.py", "backend/src/jadawel/contrib/database/rows/handler.py", "web-frontend/modules/core/registry.js"];
for (const fp of filePaths) {
  check(`buildSymbolView(${fp})`, () => {
    const fi = FILES.indexOf(fp);
    if (fi < 0) throw new Error("file not in index: " + fp);
    g.buildSymbolView(fi);
    if (!g.view.nodes.length) throw new Error("no symbol nodes");
    if (g.view.nodes.length !== new Set(g.view.nodes.map((n) => n.id)).size) throw new Error("duplicate nodes");
    for (const l of g.view.links) if (!l.a || !l.b) throw new Error("dangling link");
  });
}
check("buildSymbolView with focus symbol selects it", () => {
  const fi = FILES.indexOf("backend/src/jadawel/core/mixins.py");
  g.buildSymbolView(fi);
  const target = g.view.nodes.find((n) => n.own);
  g.buildSymbolView(fi, target.id);
  if (!g.state.sel) throw new Error("nothing selected");
  const html = el("detail").innerHTML;
  if (!html.includes("open its file")) throw new Error("detail panel not rendered: " + html.slice(0, 80));
});
check("search returns hits and builds rows", () => {
  const input = el("q");
  input.value = "handler";
  const fn = listeners.get("q:input");
  if (!fn) throw new Error("no input listener");
  fn();
  const out = el("results").innerHTML;
  if (!out.includes("data-sym") && !out.includes("data-file")) throw new Error("no results: " + out.slice(0, 120));
});
check("hotspot lists populated", () => {
  const out = el("hot").innerHTML;
  if (!out.includes("data-sym")) throw new Error("hotspot rows missing");
  if (!el("stats").innerHTML.includes("4,169")) throw new Error("stats line wrong: " + el("stats").innerHTML);
});
check("every file builds a symbol view", () => {
  let n = 0;
  for (let fi = 0; fi < FILES.length; fi++) { g.buildSymbolView(fi); n++; }
  if (n !== FILES.length) throw new Error("only " + n);
});
check("every dir builds a file view", () => {
  const dirs = vm.runInContext("[...dirs]", sandbox);
  let n = 0;
  for (const d of dirs) { g.buildFileView(d); n++; }
  if (n !== dirs.length) throw new Error("only " + n);
});

console.log(`\nchecked ${paths.length} dirs walk (${dirCount} dirs), ${filePaths.length} symbol files, all files/dirs`);
if (errors.length) { console.log(`\n${errors.length} FAILURES:`); errors.forEach((e) => console.log(" - " + e)); process.exit(1); }
console.log("all smoke checks passed");
