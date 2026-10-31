const SVGNS = "http://www.w3.org/2000/svg";
const AZ = 55;
const VW = 1000;
const VH = 640;

const BOARD = {x: -256, y: -112, w: 520, d: 180, r: 12};
const CALLER = {x: -244, y: -84, w: 60, d: 52, r: 3};
const CALLER_TOP = 58;
const MAST = [-196, -72];
const SORT = {x0: -110, w: 24, n: 4, y: -40, d: 28};
const BIN_X = i => SORT.x0 + SORT.w * i + SORT.w / 2;
const RAIL_Z = 58;
const CARRIAGE_Y = -30;
const HOME_X = -104;
const RULES = {x: 6, y: -96, w: 72, d: 62, r: 3};
const RULES_TOP = 64;
const LEDGER = {x: 24, y: 4, w: 46, d: 34, r: 2};
const LEDGER_TOP = 28;
const HELD = {x: 84, y: 4, w: 36, d: 34, r: 2};
const CAGE = {x: 88, y: 8, w: 28, d: 26};
const CAGE_H = 20;
const CAGE_UP = 30;
const SHOP = {x: 128, y: -80, w: 130, d: 116, r: 2};
const COUNTER = {x: 150, y: -4, w: 92, d: 32, r: 1};
const COUNTER_TOP = 40;
const GALLA = {x: 210, y: 0, w: 26, d: 22, r: 2};
const COIN_REST = [223, 11, 50.3];
const PHONE = {x: 191, y: 5, w: 13, d: 20, r: 2};
const PHONE_AT = [197.5, 15, 41.6];
const MANAGER = {x: -176, y: 6, w: 30, d: 22, r: 2};
const SPIKE = [-64, 18];
const OUTTRAY = {x: 54, y: -58, w: 20, d: 20, r: 1.5};
const BINS = {haan: 0, na: 1, unsure: 2, question: 2, "no answer": 3};
const DIAL_AT = {call: -72, "ask again": -36, charged: 0, held: 36, "not charged": 72, rest: -112};
const OUT_ROUTE = [[-206, -32, 3], [-206, 52, 3], [200, 52, 3], [200, 31.6, 3], [200, 31.6, 39], [PHONE_AT[0], PHONE_AT[1] + 9, PHONE_AT[2]]];
const IN_ROUTE = [[PHONE_AT[0], PHONE_AT[1] + 9, PHONE_AT[2]], [200, 31.6, 39], [200, 31.6, 3], [200, 52, 3], [-118, 52, 3], [-118, -40, 3], [-118, -40, RAIL_Z - 3], [HOME_X, CARRIAGE_Y, RAIL_Z - 3]];

function buildScene(host) {
  const P = fitProjection([
    ...boxCorners(BOARD, -18, 0),
    [SHOP.x, SHOP.y, 128], [SHOP.x + SHOP.w, SHOP.y, 128], [MAST[0], MAST[1], 112],
  ], VW, VH, {pad: 4, azimuth: AZ, elevation: 36});
  const at = p => iso(p, P);
  const S = (paths, o = {}) => solidSvg(paths, o);
  const slab = (plan, z, h, o = {}) => S(slabOf(plan, z, h, P, o.steps || 8, o.bevel || 0), o);
  const cyl = (cx, cy, r, z, h, o = {}) => S(cylinder(cx, cy, r, z, h, P, o.steps || 28, o.bevel || 0), o);
  const L = (d, o) => lineSvg(d, o);
  const D = (pts, o) => dotsSvg(pts, o);
  const front = (x, y, z, inner) => `<g transform="${sideMatrix([x, y], z, P, "left")}">${inner}</g>`;
  const side = (x, y, z, inner) => `<g transform="${sideMatrix([x, y], z, P, "right")}">${inner}</g>`;
  const onTopG = (x, y, z, inner) => `<g transform="${topMatrix([x, y], z, P, "x")}">${inner}</g>`;
  const text = (s, x, y, size, cls = "engrave", anchor = "middle") => `<text class="${cls}" x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}">${s}</text>`;
  const halo = (plan, z, h, blur) => `<path class="iso-halo" d="${haloOf(plan, z, h, P)}"${blur ? ` style="filter:blur(${blur}px)"` : ""}/>`;
  const screws = (pts, z, r = .55) => D(pts.map(([x, y]) => at([x, y, z])), {size: r, tone: "mid"});
  const plate3 = (u, v, w, h) => `<rect class="face-paint" x="${u}" y="${v}" width="${w}" height="${h}" rx="1"/>` +
    [0.3, 0.52, 0.74].map((f, i) => `<path class="face-faint" d="M${u + 2.5} ${v + h * f}H${u + w - 2.5 - i * w * .12}"/>`).join("");

  const parts = [];
  const add = (key, svg) => parts.push({key, svg});

  // board
  {
    let s = halo(BOARD, -18, 18);
    const feet = corners(BOARD, 24).sort((a, b) => depthOf([...a, 0], P) - depthOf([...b, 0], P));
    for (const [x, y] of feet) s += cyl(x, y, 9, -18, 8, {tone: "lo", bevel: .8});
    s += slab(BOARD, -10, 10, {tone: "mid", bevel: 1.2, steps: 10});
    s += L(planOutline(insetPlan(BOARD, 7), 0, P, 10), {tone: "faint"});
    s += screws(corners(BOARD, 14), 0, .7);
    const ticks = topTicks(-190, 180, 5, 5, BOARD.y + BOARD.d - 7, 0, [-2.2, -4.2], P, "x");
    s += L(ticks.minor, {tone: "faint"}) + L(ticks.major, {tone: "lo"});
    s += L(lineOnTop([-190, BOARD.y + BOARD.d - 7], [180, BOARD.y + BOARD.d - 7], 0, P), {tone: "lo"});
    const plate = {x: -246, y: 22, w: 30, d: 24, r: 2};
    s += slab(plate, 0, 1.2, {tone: "lo"});
    s += screws(corners(plate, 3), 1.2, .5);
    s += onTopG(plate.x + 6, plate.y + 8, 1.2, text("SETTLED", 0, 0, 4.6, "engrave", "start") + `<path class="face-faint" d="M0 5H18M0 9H14M0 13H16"/>`);
    add(-1e9, s);
  }

  // call line tray, one non-convex extrusion, and the branch to the sorter
  {
    const ring = [[-210, -32], [-210, 56], [204, 56], [204, 31], [196, 31], [196, 48], [-202, 48], [-202, -32]];
    let s = S(extrude(ring, 0, 3, P, {convex: false}), {tone: "mid"});
    s += L(onTop([[-206, -32], [-206, 52], [200, 52], [200, 31]], 3, P), {tone: "lo"});
    const branch = {x: -122, y: -40, w: 8, d: 88, r: 0};
    s += slab(branch, 0, 3, {tone: "mid"});
    s += L(onTop([[-118, -40], [-118, 44]], 3, P), {tone: "lo"});
    const jbox = {x: -127, y: 43, w: 18, d: 18, r: 1.5};
    s += slab(jbox, 0, 7, {tone: "mid", bevel: .6});
    s += screws(corners(jbox, 2.6), 7, .55);
    for (const x of [-150, 10, 140]) {
      const clip = {x: x - 2.5, y: 47, w: 5, d: 10, r: .6};
      s += slab(clip, 3, 1.4, {tone: "lo"});
      s += screws([[x, 49.5], [x, 54.5]], 4.4, .45);
    }
    add(depthOf([0, 52, 0], P) - 400, s);
  }

  // caller: Settled's side of the call
  {
    let s = halo(CALLER, 0, 8);
    const plinth = {x: CALLER.x - 3, y: CALLER.y - 3, w: CALLER.w + 6, d: CALLER.d + 6, r: 4};
    s += slab(plinth, 0, 4, {tone: "lo", bevel: .8});
    s += slab(CALLER, 4, CALLER_TOP - 4, {tone: "hi", bevel: 1.2, inner: L(sideSeam(CALLER, 18, P), {tone: "faint"})});
    const fy = CALLER.y + CALLER.d;
    const grille = [];
    for (let r = 0; r < 6; r++) for (let c = 0; c < 9; c++) grille.push(`<circle cx="${7 + c * 3.4}" cy="${8 + r * 3.4}" r=".75" class="face-dark"/>`);
    s += front(CALLER.x, fy, CALLER_TOP, `<rect class="face-faint" x="4.5" y="5.5" width="31.5" height="21.5" rx="2"/>${grille.join("")}` +
      `<circle class="face-paint" cx="47" cy="11" r="4.2"/><circle id="caller-lamp" class="lamp" cx="47" cy="11" r="2.8"/>` +
      plate3(39, 18, 16, 9) + `<path class="face-faint" d="M4.5 42H55.5"/>`);
    s += side(CALLER.x + CALLER.w, fy, CALLER_TOP, [10, 16, 22, 28].map(v => `<rect class="face-dark" x="10" y="${v}" width="30" height="2.4" rx="1.2"/>`).join("") +
      `<path class="face-faint" d="M0 42H52"/>`);
    s += screws([[CALLER.x + 4, CALLER.y + 4], [CALLER.x + CALLER.w - 4, CALLER.y + 4], [CALLER.x + 4, fy - 4], [CALLER.x + CALLER.w - 4, fy - 4]], CALLER_TOP);
    // desk phone on top
    const base = {x: CALLER.x + 8, y: CALLER.y + 10, w: 30, d: 26, r: 3};
    s += slab(base, CALLER_TOP, 6, {tone: "mid", bevel: .8});
    s += D(dotGrid(base.x + 18, base.y + 11, 3, 4, 3.4, CALLER_TOP + 6, P), {size: .7, tone: "hi"});
    s += slab({x: base.x + 4, y: base.y + 11, w: 10, d: 11, r: 1}, CALLER_TOP + 6, .6, {tone: "lo", flat: true});
    s += `<g id="handset">${cyl(base.x + 5, base.y + 5, 4, CALLER_TOP + 6, 4.5, {tone: "hi", bevel: .5})}${slab({x: base.x + 5, y: base.y + 2.5, w: 20, d: 5, r: 2.4}, CALLER_TOP + 8, 3, {tone: "hi"})}${cyl(base.x + 25, base.y + 5, 4, CALLER_TOP + 6, 4.5, {tone: "hi", bevel: .5})}</g>`;
    // mast
    s += cyl(MAST[0], MAST[1], 5.5, CALLER_TOP, 3, {tone: "mid", bevel: .6});
    s += screws([[MAST[0] - 3.6, MAST[1]], [MAST[0] + 3.6, MAST[1]], [MAST[0], MAST[1] + 3.6]], CALLER_TOP + 3, .45);
    s += cyl(MAST[0], MAST[1], 1.6, CALLER_TOP + 3, 46, {tone: "hi", steps: 16});
    s += cyl(MAST[0], MAST[1], 3, CALLER_TOP + 24, 2.2, {tone: "mid", steps: 20});
    s += cyl(MAST[0], MAST[1], 3, CALLER_TOP + 49, 2.4, {tone: "mid", steps: 20});
    const tip = at([MAST[0], MAST[1], CALLER_TOP + 54]);
    s += `<circle class="face-paint" cx="${tip[0]}" cy="${tip[1]}" r="3.4"/><circle id="mast-lamp" class="lamp" cx="${tip[0]}" cy="${tip[1]}" r="2.3"/>`;
    s += `<g id="mast-waves">${[0, 1, 2].map(i => `<path class="wave" opacity="0" data-i="${i}" d="${ring(MAST[0], MAST[1], 9, CALLER_TOP + 54, P, 36)}"/>`).join("")}</g>`;
    add(depthOf([CALLER.x + 30, CALLER.y + 26, 0], P), s);
  }

  // manager's phone stand (WhatsApp lands here)
  {
    let s = "";
    s += slab(MANAGER, 0, 16, {tone: "hi", bevel: .8});
    s += front(MANAGER.x, MANAGER.y + MANAGER.d, 16, plate3(6, 4, 22, 9));
    const stand = {x: MANAGER.x + 18, y: MANAGER.y + 4, w: 12, d: 4, r: .8};
    s += slab(stand, 16, 20, {tone: "mid"});
    s += front(stand.x, stand.y + stand.d, 36, `<rect class="screen" id="mgr-screen" x="1.2" y="1.5" width="9.6" height="16" rx="1"/>`);
    s += slab({x: MANAGER.x + 17, y: MANAGER.y + 8, w: 14, d: 4, r: .8}, 16, 2, {tone: "lo"});
    add(depthOf([MANAGER.x + 17, MANAGER.y + 12, 0], P), s);
  }

  // support ticket spike
  {
    let s = "";
    s += cyl(SPIKE[0], SPIKE[1], 10, 0, 3.5, {tone: "mid", bevel: .8});
    s += L(knurl(SPIKE[0], SPIKE[1], 10, 0, 3.5, 40, P), {tone: "faint"});
    s += cyl(SPIKE[0], SPIKE[1], 2.4, 3.5, 2, {tone: "hi", steps: 16});
    s += `<g id="spike-tickets"></g>`;
    s += cyl(SPIKE[0], SPIKE[1], .8, 5.5, 26, {tone: "hi", steps: 12});
    add(depthOf([SPIKE[0], SPIKE[1], 0], P), s);
  }

  // sorter: a gantry carriage that drops each sorted reply into its bin
  const binSlots = [];
  {
    const bx = SORT.x0, by = SORT.y, bw = SORT.w * SORT.n, bd = SORT.d;
    let s = "";
    s += slab({x: bx - 2, y: by - 2, w: bw + 4, d: bd + 4, r: 2}, 0, 2.5, {tone: "lo", bevel: .6});
    s += slab({x: bx, y: by, w: bw, d: 2, r: 0}, 2.5, 13.5, {tone: "mid"});
    for (let i = 0; i < SORT.n; i++) s += `<path class="tray-tint" id="bin-tint-${i}" d="${planOutline({x: bx + SORT.w * i + 1.5, y: by + 2.5, w: SORT.w - 3, d: bd - 5, r: 1}, 2.6, P)}"/>`;
    for (let i = 0; i <= SORT.n; i++) {
      s += slab({x: bx + SORT.w * i - (i === 0 ? 0 : i === SORT.n ? 2 : 1), y: by + 2, w: 2, d: bd - 4, r: 0}, 2.5, 13.5, {tone: "mid"});
      if (i < SORT.n) s += `<g id="bin-slot-${i}"></g>`;
    }
    const fy = by + bd - 2;
    s += slab({x: bx, y: fy, w: bw, d: 2, r: 0}, 2.5, 7.5, {tone: "hi", inner: ""});
    const names = ["HAAN", "NA", "OTHER", "NONE"];
    s += front(bx, fy + 2, 10, names.map((n, i) => text(n, SORT.w * i + SORT.w / 2, 5.6, 5).replace('class="engrave"', `class="engrave" id="bin-label-${i}"`)).join("") +
      [1, 2, 3].map(i => `<path class="face-faint" d="M${SORT.w * i} 1.5V7.5"/>`).join(""));
    add(depthOf([bx + bw / 2, by + bd / 2, 0], P), s);
    // wire from bins to the rules cabinet
    add(depthOf([0, -22, 0], P), wireSvg(at([bx + bw + 2, -22, 1]), at([RULES.x - 2, -22, 1]), {tone: "mid", size: 1.1}));
  }
  {
    // gantry posts and rail
    let s = "";
    for (const x of [-118, -2]) {
      const post = {x: x - 3, y: -49, w: 6, d: 6, r: .6};
      s += slab({x: x - 6, y: -52, w: 12, d: 12, r: 1.5}, 0, 2.5, {tone: "lo", bevel: .5});
      s += screws([[x - 4, -50], [x + 4, -50], [x - 4, -42], [x + 4, -42]], 2.5, .45);
      s += slab(post, 2.5, RAIL_Z - 2.5, {tone: "mid"});
    }
    const rail = {x: -122, y: -50, w: 124, d: 8, r: .8};
    s += slab(rail, RAIL_Z, 6, {tone: "mid", bevel: .6});
    const t = sideTicks(-112, -8, 4, 6, -42, RAIL_Z + 5, [1.6, 3.2], P, "x");
    s += L(t.minor, {tone: "faint"}) + L(t.major, {tone: "lo"});
    s += L(segment([-112, -42, RAIL_Z + 5], [-8, -42, RAIL_Z + 5], P), {tone: "faint"});
    s += screws([[-118, -46], [-2, -46]], RAIL_Z + 6, .55);
    // riser conduit up the left post
    s += slab({x: -120.5, y: -43, w: 5, d: 2, r: 0}, 2.5, RAIL_Z - 4, {tone: "hi"});
    add(depthOf([-60, -46, 0], P) + 2, s);
    // carriage, built at home and slid along x
    const cx = HOME_X, cy = CARRIAGE_Y;
    let c = "";
    c += slab({x: cx - 9, y: cy - 12, w: 18, d: 4, r: .5}, RAIL_Z - 1, 8, {tone: "mid"});
    c += slab({x: cx - 9, y: cy - 8, w: 18, d: 18, r: 1.5}, RAIL_Z - 12, 14, {tone: "hi", bevel: .8, lit: true});
    c += front(cx - 9, cy + 10, RAIL_Z + 2, `<circle class="face-paint" cx="13" cy="5" r="2.3"/><circle id="carriage-lamp" class="lamp" cx="13" cy="5" r="1.5"/>` + `<path class="face-faint" d="M3 4H8M3 7H7"/>`);
    c += cyl(cx, cy + 1, 6, RAIL_Z + 2, 4, {tone: "mid", bevel: .5});
    c += cyl(cx, cy + 1, 4, RAIL_Z + 2, 4.6, {tone: "lo", flat: true});
    c += cyl(cx, cy + 1, 3, RAIL_Z - 17, 5, {tone: "mid"});
    c += screws([[cx - 7, cy - 6], [cx + 7, cy - 6], [cx - 7, cy + 8], [cx + 7, cy + 8]], RAIL_Z + 2, .45);
    add(depthOf([-60, -40, 0], P) + 3, `<g id="carriage">${c}</g>`);
  }

  // rules cabinet: plain code, a dial for the decision
  {
    let s = halo(RULES, 0, 8);
    s += slab({x: RULES.x - 3, y: RULES.y - 3, w: RULES.w + 6, d: RULES.d + 6, r: 4}, 0, 4, {tone: "lo", bevel: .8});
    s += slab(RULES, 4, RULES_TOP - 4, {tone: "hi", bevel: 1.2, inner: L(sideSeam(RULES, 14, P), {tone: "faint"})});
    const fy = RULES.y + RULES.d;
    const cx = 28, cy = 25, R = 19;
    const ticks = [];
    for (let a = -120; a <= 120; a += 6) {
      const big = Object.values(DIAL_AT).includes(a) || a % 36 === 0;
      const r0 = R - (big ? 3.4 : 1.8), rad = a * Math.PI / 180;
      ticks.push(`M${cx + Math.sin(rad) * r0} ${cy - Math.cos(rad) * r0}L${cx + Math.sin(rad) * R} ${cy - Math.cos(rad) * R}`);
    }
    const dots = Object.entries(DIAL_AT).filter(([k]) => k !== "rest").map(([k, a]) => {
      const rad = a * Math.PI / 180, r = R - 6.6;
      const cls = {call: "sc-accent", "ask again": "sc-accent", charged: "sc-charged", held: "sc-held", "not charged": "sc-not"}[k];
      return `<circle class="${cls}" cx="${cx + Math.sin(rad) * r}" cy="${cy - Math.cos(rad) * r}" r="1.35"/>`;
    }).join("");
    s += front(RULES.x, fy, RULES_TOP, `<circle class="face-paint" cx="${cx}" cy="${cy}" r="${R + 2.6}"/><circle class="face-line" cx="${cx}" cy="${cy}" r="${R + 1}"/>` +
      `<path class="face-line" d="${ticks.join("")}"/>${dots}` +
      `<g id="needle" transform="rotate(${DIAL_AT.rest} ${cx} ${cy})"><path class="needle" d="M${cx} ${cy + 3.5}V${cy - R + 2.2}"/></g><circle class="hub" cx="${cx}" cy="${cy}" r="1.9"/>` +
      plate3(14, 49, 28, 8) +
      [["lamp-charged", 12], ["lamp-held", 25], ["lamp-not", 38]].map(([id, v]) => `<circle class="face-paint" cx="61" cy="${v}" r="4.8"/><circle id="${id}" class="lamp" cx="61" cy="${v}" r="3.4"/>`).join("") +
      `<path class="face-faint" d="M53 48H69M53 52H65"/>`);
    s += side(RULES.x + RULES.w, fy, RULES_TOP, [12, 17, 22, 27, 32].map(v => `<rect class="face-dark" x="12" y="${v}" width="34" height="2.2" rx="1.1"/>`).join("") +
      `<circle class="face-paint" cx="8" cy="48" r="1.4"/><circle class="face-paint" cx="54" cy="48" r="1.4"/>`);
    s += screws([[RULES.x + 4, RULES.y + 4], [RULES.x + RULES.w - 4, RULES.y + 4], [RULES.x + 4, fy - 4], [RULES.x + RULES.w - 4, fy - 4]], RULES_TOP);
    // slot the records card goes into
    s += slab({x: 40, y: -74, w: 26, d: 6, r: 1}, RULES_TOP, .5, {tone: "lo", flat: true});
    s += L(planOutline({x: 41, y: -72.5, w: 24, d: 3, r: .8}, RULES_TOP + .5, P), {tone: "mid"});
    // records card file
    const file = {x: 12, y: -90, w: 22, d: 26, r: 1.2};
    s += slab(file, RULES_TOP, 10, {tone: "mid", bevel: .6});
    for (let i = 0; i < 4; i++) s += slab({x: 14, y: -86 + i * 5, w: 18, d: 1, r: 0}, RULES_TOP + 6, 6 - (i % 2), {tone: "hi", lit: false});
    s += `<g id="record-card">${slab({x: 14, y: -67, w: 18, d: 1, r: 0}, RULES_TOP + 6, 7, {tone: "hi", lit: true})}</g>`;
    s += slab({x: 12, y: -66, w: 22, d: 2, r: 0}, RULES_TOP, 7, {tone: "mid"});
    // beacon: blue while the call is on, then the outcome's colour
    s += cyl(66, -84, 6.5, RULES_TOP, 3, {tone: "mid", bevel: .6});
    s += `<g id="beacon" class="beacon">${cyl(66, -84, 5, RULES_TOP + 3, 10, {tone: "hi", steps: 32})}</g>`;
    s += cyl(66, -84, 5.8, RULES_TOP + 13, 2, {tone: "mid", bevel: .5});
    s += cyl(66, -84, 2, RULES_TOP + 15, 1.6, {tone: "mid", steps: 16});
    // out tray for texts
    s += slab(OUTTRAY, RULES_TOP, 3.5, {tone: "mid", bevel: .5});
    s += slab(insetPlan(OUTTRAY, 2), RULES_TOP + 3.5, .3, {tone: "lo", flat: true});
    add(depthOf([RULES.x + 36, RULES.y + 31, 0], P), s);
  }

  // ledger (Paytm's side): a strongbox with an open coin tray
  {
    let s = halo(LEDGER, 0, 8);
    s += slab({x: LEDGER.x - 2, y: LEDGER.y - 2, w: LEDGER.w + 4, d: LEDGER.d + 4, r: 3}, 0, 3, {tone: "lo", bevel: .6});
    s += slab(LEDGER, 3, LEDGER_TOP - 3, {tone: "hi", bevel: 1});
    const fy = LEDGER.y + LEDGER.d;
    s += front(LEDGER.x, fy, LEDGER_TOP, `<rect class="face-faint" x="3" y="3" width="40" height="25" rx="1.5"/>` +
      `<circle class="face-paint" cx="31" cy="14.5" r="6"/><circle class="face-line" cx="31" cy="14.5" r="4"/>` +
      [0, 1, 2, 3, 4, 5, 6, 7].map(i => { const a = i * Math.PI / 4; return `<path class="face-faint" d="M${31 + Math.sin(a) * 4.6} ${14.5 - Math.cos(a) * 4.6}L${31 + Math.sin(a) * 5.6} ${14.5 - Math.cos(a) * 5.6}"/>`; }).join("") +
      `<path class="face-line" d="M31 14.5L31 11"/>` + text("LEDGER", 13, 16.5, 4.6) + `<path class="face-faint" d="M6 20H20M6 23.5H17"/>`);
    s += side(LEDGER.x + LEDGER.w, fy, LEDGER_TOP, `<rect class="face-paint" x="5" y="5" width="2.5" height="7" rx="1"/><rect class="face-paint" x="5" y="18" width="2.5" height="7" rx="1"/>`);
    const tray = {x: LEDGER.x + 6, y: LEDGER.y + 5, w: 34, d: 26, r: 2};
    s += slab(tray, LEDGER_TOP, 1, {tone: "lo"});
    s += `<g id="ledger-coins"></g>`;
    s += slab({x: tray.x, y: tray.y + tray.d - 1.5, w: tray.w, d: 1.5, r: 0}, LEDGER_TOP + 1, 3, {tone: "mid"});
    s += slab({x: tray.x + tray.w - 1.5, y: tray.y, w: 1.5, d: tray.d - 1.5, r: 0}, LEDGER_TOP + 1, 3, {tone: "mid"});
    add(depthOf([LEDGER.x + 23, LEDGER.y + 18, 0], P), s);
  }

  // held tray: a cage on a gallows drops over the coin and locks
  {
    let s = "";
    s += slab(HELD, 0, 4, {tone: "mid", bevel: .8});
    s += slab(insetPlan(HELD, 3), 4, .4, {tone: "lo", flat: true});
    s += screws(corners(HELD, 2), 4, .5);
    const gx = HELD.x + 2, gy = HELD.y + 2;
    s += slab({x: gx - 1.5, y: gy - 1.5, w: 5, d: 5, r: .5}, 4, 66, {tone: "mid"});
    s += slab({x: gx - 1.5, y: gy - 1.5, w: 21, d: 5, r: .5}, 70, 4, {tone: "mid"});
    s += `<path class="iso-line" data-tone="mid" id="cage-rope" d=""/>`;
    const cageBack = [], cageFront = [];
    const {x, y, w, d} = CAGE;
    const z0 = 4 + CAGE_UP, z1 = z0 + CAGE_H;
    for (let i = 0; i <= 6; i++) {
      cageBack.push(segment([x + w * i / 6, y, z0], [x + w * i / 6, y, z1], P));
      cageFront.push(segment([x + w * i / 6, y + d, z0], [x + w * i / 6, y + d, z1], P));
    }
    for (let i = 1; i < 6; i++) {
      cageBack.push(segment([x, y + d * i / 6, z0], [x, y + d * i / 6, z1], P));
      cageFront.push(segment([x + w, y + d * i / 6, z0], [x + w, y + d * i / 6, z1], P));
    }
    const bottom = onTop([[x, y], [x + w, y], [x + w, y + d], [x, y + d]], z0, P, true);
    const lock = at([x + w / 2, y + d, z0 + 7]);
    s += `<g id="cage-back">${L(cageBack.join(""), {tone: "mid"})}${L(onTop([[x, y + d], [x, y], [x + w, y]], z0, P), {tone: "mid"})}</g>`;
    s += `<g id="held-slot"></g>`;
    s += `<g id="cage-front">${L(cageFront.join(""), {tone: "hi"})}${L(onTop([[x, y + d], [x + w, y + d], [x + w, y]], z0, P), {tone: "hi"})}` +
      slab({x: x - .8, y: y - .8, w: w + 1.6, d: d + 1.6, r: 1}, z1, 1.6, {tone: "hi"}) + L(bottom, {tone: "faint"}) +
      `<g id="padlock" opacity="0"><path class="face-line" d="M${lock[0] - 2.4} ${lock[1] - 2}V${lock[1] - 4.2}a2.4 2.4 0 0 1 4.8 0V${lock[1] - 2}"/><rect class="sc-held" x="${lock[0] - 3.6}" y="${lock[1] - 2.4}" width="7.2" height="6" rx="1.2"/><circle cx="${lock[0]}" cy="${lock[1] + .4}" r=".9" fill="#fff"/></g></g>`;
    add(depthOf([HELD.x + 18, HELD.y + 17, 0], P), s);
  }

  // the shop: plinth, back wall with shelves, counter, canopy
  {
    let s = halo(SHOP, 0, 10);
    s += slab(SHOP, 0, 5, {tone: "mid", bevel: 1});
    for (let gx = SHOP.x + 13; gx < SHOP.x + SHOP.w; gx += 13) s += L(lineOnTop([gx, SHOP.y + 9], [gx, SHOP.y + SHOP.d - 1], 5, P), {tone: "faint"});
    for (let gy = SHOP.y + 9 + 13; gy < SHOP.y + SHOP.d; gy += 13) s += L(lineOnTop([SHOP.x + 1, gy], [SHOP.x + SHOP.w - 1, gy], 5, P), {tone: "faint"});
    const wall = {x: SHOP.x, y: SHOP.y, w: SHOP.w, d: 8, r: 0};
    s += slab(wall, 5, 112, {tone: "mid"});
    const wy = SHOP.y + 8;
    // shelves and goods, back to front, bottom to top
    const goods = [];
    for (const z of [30, 58, 86]) {
      const shelf = {x: SHOP.x + 6, y: wy, w: SHOP.w - 12, d: 15, r: 0};
      for (const bx of [SHOP.x + 14, SHOP.x + SHOP.w - 14]) s += slab({x: bx - 1, y: wy, w: 2, d: 10, r: 0}, z - 6, 6, {tone: "lo"});
      s += slab(shelf, z, 2.4, {tone: "hi"});
      let gx = SHOP.x + 10;
      const pattern = z === 30 ? "jjjbbjjjbb" : z === 58 ? "bbjjjbbjjb" : "jjbbbjjjbj";
      for (const kind of pattern) {
        if (kind === "j") { goods.push([gx + 4.5, wy + 7.5, z + 2.4, "j"]); gx += 11; }
        else { goods.push([gx, wy + 2.5, z + 2.4, "b"]); gx += 12; }
        if (gx > SHOP.x + SHOP.w - 16) break;
      }
      for (const [x, y, gz, k] of goods.splice(0)) {
        if (k === "j") {
          s += cyl(x, y, 4.4, gz, 10, {tone: "mid", steps: 20});
          s += cyl(x, y, 3.2, gz + 10, 2.2, {tone: "hi", steps: 18});
        } else {
          s += slab({x, y, w: 10, d: 9, r: .5}, gz, 14, {tone: "mid"});
          s += front(x, y + 9, gz + 14, `<path class="face-faint" d="M2 4H8M2 7H6"/>`);
        }
      }
    }
    // sacks on the floor
    s += cyl(SHOP.x + 12, SHOP.y + 34, 8, 5, 15, {tone: "mid", steps: 24, bevel: 2});
    s += cyl(SHOP.x + 13, SHOP.y + 52, 7, 5, 12, {tone: "mid", steps: 24, bevel: 2});
    // counter
    s += slab({x: COUNTER.x + 2, y: COUNTER.y + 2, w: COUNTER.w - 4, d: COUNTER.d - 2, r: 0}, 5, 3, {tone: "lo"});
    s += slab(COUNTER, 8, COUNTER_TOP - 11, {tone: "hi", inner: L(sideSeam(COUNTER, 22, P), {tone: "faint"})});
    s += front(COUNTER.x, COUNTER.y + COUNTER.d, COUNTER_TOP - 3, [0, 1, 2].map(i => `<rect class="face-faint" x="${4 + i * 29}" y="5" width="26" height="21" rx="1"/>`).join(""));
    s += slab({x: COUNTER.x - 2, y: COUNTER.y - 2, w: COUNTER.w + 4, d: COUNTER.d + 4, r: 1.5}, COUNTER_TOP - 3, 3, {tone: "hi", bevel: .8});
    s += slab({x: 197, y: COUNTER.y + COUNTER.d, w: 6, d: 3.2, r: 0}, 5, COUNTER_TOP - 9, {tone: "hi"});
    // posts and canopy
    for (const px of [SHOP.x + 3, SHOP.x + SHOP.w - 3]) s += cyl(px, SHOP.y + 54, 2, 5, 100, {tone: "mid", steps: 16});
    const can = {x: SHOP.x - 4, y: SHOP.y - 4, w: SHOP.w + 8, d: 62, r: 1};
    s += slab(can, 117, 5, {tone: "hi", bevel: .8});
    for (let rx = can.x + 9; rx < can.x + can.w - 4; rx += 9) s += L(lineOnTop([rx, can.y + 3], [rx, can.y + can.d - 3], 122, P), {tone: "faint"});
    s += L(lineOnTop([can.x + 3, can.y + 3], [can.x + can.w - 3, can.y + 3], 122, P) + lineOnTop([can.x + 3, can.y + can.d - 3], [can.x + can.w - 3, can.y + can.d - 3], 122, P), {tone: "faint"});
    const vy = can.y + can.d;
    s += slab({x: can.x, y: vy, w: can.w, d: 2, r: 0}, 103, 14, {tone: "hi"});
    const stripes = [];
    for (let i = 0; i < 17; i++) stripes.push(`<rect class="${i % 2 ? "cloth-a" : "cloth-b"}" x="${i * can.w / 17}" y="0" width="${can.w / 17}" height="4"/>`);
    s += front(can.x, vy + 2, 117, `${stripes.join("")}<path class="face-faint" d="M0 4H${can.w}"/>` +
      `<text id="shop-name" class="engrave ink" x="${can.w / 2}" y="11.6" font-size="6.6" text-anchor="middle"></text>`);
    add(depthOf([SHOP.x + 65, SHOP.y + 20, 0], P), s);
  }
  // counter top things, after the shop
  {
    let s = "";
    s += `<g id="soundbox">`;
    const sb = {x: 158, y: 3, w: 18, d: 15, r: 2.2};
    s += slab(sb, COUNTER_TOP, 22, {tone: "hi", bevel: .8, lit: true});
    const g = [];
    for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) g.push(`<circle class="face-dark" cx="${4.4 + c * 3.1}" cy="${9 + r * 2.9}" r=".7"/>`);
    s += front(sb.x, sb.y + sb.d, COUNTER_TOP + 22, `<rect class="screen" x="3.5" y="2.5" width="11" height="4" rx=".8"/>${g.join("")}`);
    s += cyl(sb.x + 9, sb.y + 7, 2.6, COUNTER_TOP + 22, 1.4, {tone: "mid", steps: 18});
    s += slab({x: 179, y: 1, w: 12, d: 2, r: 0}, COUNTER_TOP, 17, {tone: "hi"});
    const qr = [];
    for (let r = 0; r < 6; r++) for (let c = 0; c < 6; c++) if ((r * 7 + c * 3 + r * c) % 3) qr.push(`<rect x="${2 + c * 1.35}" y="${3 + r * 1.35}" width="1.35" height="1.35" fill="#3a3a3e"/>`);
    s += front(179, 3, COUNTER_TOP + 17, qr.join(""));
    s += `</g>`;
    s += `<g id="soundbox-gone" opacity="0">${L(planOutline({x: 158, y: 3, w: 18, d: 15, r: 2.2}, COUNTER_TOP + .1, P), {tone: "mid"})}${L(planOutline({x: 160, y: 5, w: 14, d: 11, r: 1.6}, COUNTER_TOP + .1, P), {tone: "faint"})}</g>`;
    // phone
    s += `<g id="phone">${slab(PHONE, COUNTER_TOP, 1.6, {tone: "hi", bevel: .4})}<path id="phone-screen" class="screen" d="${planOutline(insetPlan(PHONE, 1.2), COUNTER_TOP + 1.65, P)}"/></g>`;
    s += `<g id="phone-waves">${[0, 1, 2].map(i => `<path class="wave" opacity="0" data-i="${i}" d="${ring(PHONE_AT[0], PHONE_AT[1], 9, COUNTER_TOP + 2, P, 36)}"/>`).join("")}</g>`;
    // galla, the shop's own cash box
    s += slab(GALLA, COUNTER_TOP, 10, {tone: "mid", bevel: .8});
    s += slab({x: GALLA.x + 4, y: GALLA.y + 4, w: 4, d: 12, r: 1}, COUNTER_TOP + 10, .3, {tone: "lo", flat: true});
    s += `<path id="kept-ring" opacity="0" style="fill:none;stroke:var(--charged);stroke-width:1.6px" d="${ring(COIN_REST[0], COIN_REST[1], 10.4, COUNTER_TOP + 10.1, P, 40)}"/>`;
    s += front(GALLA.x, GALLA.y + GALLA.d, COUNTER_TOP + 10, `<rect class="face-faint" x="3" y="2.5" width="18" height="5.5" rx="1"/><circle class="face-paint" cx="12" cy="5.2" r="1.1"/>` +
      `<circle class="face-paint" cx="20.5" cy="1.8" r="1.3"/><circle id="lamp-kept" class="lamp" cx="20.5" cy="1.8" r=".9"/>`);
    add(depthOf([200, 14, 0], P) + 60, s);
  }

  const sceneSvg = `<svg id="scene-svg" xmlns="${SVGNS}" viewBox="0 0 ${VW} ${VH}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Settled's call as a machine: the caller, the sorter, the rules dial, the ledger, the held cage and the shop">` +
    parts.sort((a, b) => a.key - b.key).map(p => p.svg).join("") +
    `<g id="pulses"></g><g id="coin-top"></g><g id="flying"></g></svg>`;
  host.innerHTML = sceneSvg;
  const svg = host.firstElementChild;
  const refs = {};
  const $ = id => refs[id] || (refs[id] = svg.querySelector("#" + id));
  const make = (tag, attrs = {}, html = "") => {
    const el = document.createElementNS(SVGNS, tag);
    for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    if (html) el.innerHTML = html;
    return el;
  };

  // moving pieces drawn at the world origin, placed with a screen translate
  const origin = at([0, 0, 0]);
  const offset = p => { const q = at(p); return [q[0] - origin[0], q[1] - origin[1]]; };
  const place = (el, p) => { const [x, y] = offset(p); el.setAttribute("transform", `translate(${x.toFixed(2)} ${y.toFixed(2)})`); };
  const coinSvg = () => `<g class="coin">${S(cylinder(0, 0, 9.5, 0, 2.8, P, 40, .6), {tone: "hi", lit: true})}` +
    `${L(ring(0, 0, 7.6, 2.8, P, 40), {tone: "lo"})}<g transform="${topMatrix([0, 0], 2.8, P, "x")}"><text class="coin-amount" x="0" y="2" font-size="5.6" font-weight="750" text-anchor="middle" font-family="var(--sans)"></text></g></g>`;
  const tokenSvg = () => `<g class="token">${S(slabOf({x: -6.5, y: -6.5, w: 13, d: 13, r: 1.4}, 0, 3, P, 8, .4), {tone: "hi", lit: true})}${L(planOutline({x: -3.5, y: -3.5, w: 7, d: 7, r: 3.5}, 3, P), {tone: "mid"})}</g>`;
  const envSvg = (cls) => {
    const w = 16, d = 11;
    const top = (x, y) => at([x, y, 0]);
    const lift = (x, y) => at([x, y, 1.2]);
    const pts = [lift(-w / 2 + .8, -d / 2 + .8), lift(w / 2 - .8, -d / 2 + .8), lift(w / 2 - .8, d / 2 - .8), lift(-w / 2 + .8, d / 2 - .8)];
    const m = lift(0, 1.5);
    return `<g class="env">${S(slabOf({x: -w / 2, y: -d / 2, w, d, r: .6}, 0, 1.2, P, 4), {tone: "hi", lit: true})}` +
      `<path class="face-line" d="M${pts[0][0]} ${pts[0][1]}L${m[0]} ${m[1]}L${pts[1][0]} ${pts[1][1]}"/>` +
      `<path class="${cls}" d="${planOutline({x: w / 2 - 5.5, y: d / 2 - 4.5, w: 3.6, d: 3.6, r: 1.8}, 1.25, P)}"/></g>`;
  };

  const coin = make("g", {}, coinSvg());
  const carriage = $("carriage");
  const handset = $("handset");
  const needle = $("needle");
  const card = $("record-card");
  const cageBack = $("cage-back"), cageFront = $("cage-front"), rope = $("cage-rope");
  const pulses = $("pulses");
  const flying = $("flying");
  const routeOut = OUT_ROUTE.map(at), routeIn = IN_ROUTE.map(at);
  const lens = r => { const l = [0]; for (let i = 1; i < r.length; i++) l.push(l[i - 1] + Math.hypot(r[i][0] - r[i - 1][0], r[i][1] - r[i - 1][1])); return l; };
  const lenOut = lens(routeOut), lenIn = lens(routeIn);
  const along = (r, l, t) => {
    const s = t * l[l.length - 1];
    let i = 1;
    while (i < l.length - 1 && l[i] < s) i++;
    const f = Math.max(0, Math.min(1, (s - l[i - 1]) / ((l[i] - l[i - 1]) || 1)));
    return [r[i - 1][0] + (r[i][0] - r[i - 1][0]) * f, r[i - 1][1] + (r[i][1] - r[i - 1][1]) * f];
  };
  const PULSES = 7;
  const dots = Array.from({length: PULSES}, () => { const c = make("circle", {r: 3.8, class: "pulse", opacity: 0}); pulses.appendChild(c); return c; });

  const st = {needle: DIAL_AT.rest, carriageX: HOME_X, cage: 0, handset: 0, card: 0, coinIn: "galla", ledgerN: 0, tickets: 0, mgr: 0, sms: 0};
  const tweens = new Set();
  let raf = 0;
  const live = {speaking: false, ringing: false, listening: false, rec: false, level: 0, hearing: false, onCall: false, outcome: null};
  let wakeFn = () => {};
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const easeOut = t => 1 - Math.pow(1 - t, 3);
  const spring = t => 1 - Math.exp(-6 * t) * Math.cos(9 * t);

  function tween(ms, fn, curve = ease) {
    if (REDUCED || ms === 0) { fn(1); return Promise.resolve(); }
    return new Promise(done => {
      const tw = {t0: performance.now(), ms, fn, curve, done};
      tweens.add(tw);
      wakeFn();
    });
  }
  const wait = ms => REDUCED || ms === 0 ? Promise.resolve() : new Promise(r => setTimeout(r, ms));

  function setNeedle(a) { st.needle = a; needle.setAttribute("transform", `rotate(${a.toFixed(2)} 28 25)`); }
  function setCarriage(x) { st.carriageX = x; carriage.setAttribute("transform", translateAlong(P, [x - HOME_X, 0, 0])); }
  function setHandset(f) { st.handset = f; handset.setAttribute("transform", translateAlong(P, [0, 0, 7 * f])); }
  function setCage(f) {
    st.cage = f;
    const t = translateAlong(P, [0, 0, -CAGE_UP * f]);
    cageBack.setAttribute("transform", t);
    cageFront.setAttribute("transform", t);
    const top = at([CAGE.x + 16, CAGE.y + CAGE.d / 2 - 2, 70]);
    const bot = at([CAGE.x + 16, CAGE.y + CAGE.d / 2 - 2, 4 + CAGE_UP + CAGE_H + 1.6 - CAGE_UP * f]);
    rope.setAttribute("d", `M${top[0]} ${top[1]}L${bot[0]} ${bot[1]}`);
  }
  function lamp(id, cls) { const el = $(id); if (el) el.setAttribute("class", "lamp" + (cls ? ` on-${cls}` : "")); }
  function setCard(f) {
    st.card = f;
    // lift out of the file, glide over the slot, sink in
    const lift = Math.min(1, f * 3), glide = Math.max(0, Math.min(1, f * 3 - 1)), sink = Math.max(0, f * 3 - 2);
    card.setAttribute("transform", translateAlong(P, [glide * 39, glide * -5.5, lift * 14 - sink * 18]));
    card.setAttribute("opacity", f >= 1 ? 1 : 1);
  }

  function coinTo(where) {
    st.coinIn = where;
    const parent = where === "held" ? $("held-slot") : where === "ledger" ? $("ledger-coins") : $("coin-top");
    parent.appendChild(coin);
    place(coin, where === "held" ? [CAGE.x + CAGE.w / 2, CAGE.y + CAGE.d / 2, 4.4] : where === "ledger" ? [LEDGER.x + 23, LEDGER.y + 18, LEDGER_TOP + 1] : COIN_REST);
  }

  let gen = 0;
  const stale = g => g !== gen;

  function reset() {
    gen++;
    inFlight = null;
    for (const tw of tweens) tw.done();
    tweens.clear();
    setNeedle(DIAL_AT.rest);
    setCarriage(HOME_X);
    setHandset(0);
    setCage(0);
    setCard(0);
    coinTo("galla");
    coin.removeAttribute("opacity");
    $("padlock").setAttribute("opacity", 0);
    $("kept-ring").setAttribute("opacity", 0);
    for (let i = 0; i < SORT.n; i++) { $(`bin-slot-${i}`).innerHTML = ""; $(`bin-tint-${i}`).classList.remove("on"); $(`bin-label-${i}`).classList.remove("lit"); }
    flying.innerHTML = "";
    $("spike-tickets").innerHTML = "";
    st.tickets = st.mgr = st.sms = 0;
    for (const id of ["lamp-charged", "lamp-held", "lamp-not", "lamp-kept", "caller-lamp", "mast-lamp", "carriage-lamp"]) lamp(id, null);
    $("mgr-screen").setAttribute("class", "screen");
    live.outcome = null;
  }

  function setShop(name, boxThere, amount) {
    $("shop-name").textContent = (name || "").toUpperCase();
    coin.querySelector(".coin-amount").textContent = amount || "";
    $("soundbox").setAttribute("opacity", boxThere ? 1 : 0);
    $("soundbox-gone").setAttribute("opacity", boxThere ? 0 : 1);
  }

  async function records(instant) {
    const g = gen;
    if (instant) { setCard(1); return; }
    lamp("carriage-lamp", null);
    await tween(1400, setCard);
    if (stale(g)) return;
  }

  async function call() {}

  let inFlight = null;
  async function answer(kind, instant) {
    const g = gen;
    const bin = BINS[kind] ?? 2;
    const slot = $(`bin-slot-${bin}`);
    const n = slot.childElementCount;
    const tok = make("g", {}, tokenSvg());
    const rest = [BIN_X(bin), -26, 2.5 + n * 3];
    const tint = () => { for (let i = 0; i < SORT.n; i++) { $(`bin-tint-${i}`).classList.toggle("on", i === bin); $(`bin-label-${i}`).classList.toggle("lit", i === bin); } };
    if (instant) { slot.appendChild(tok); place(tok, rest); setCarriage(BIN_X(bin)); tint(); return; }
    // his reply travels back along the line to the sorter
    inFlight = {t0: performance.now(), ms: 1500};
    wakeFn();
    await wait(1500);
    if (stale(g)) return;
    inFlight = null;
    lamp("carriage-lamp", "accent");
    const from = st.carriageX;
    await tween(Math.max(450, Math.abs(BIN_X(bin) - from) * 9), t => setCarriage(from + (BIN_X(bin) - from) * t));
    if (stale(g)) return;
    slot.appendChild(tok);
    const z0 = RAIL_Z - 18;
    await tween(520, t => place(tok, [BIN_X(bin), CARRIAGE_Y + (rest[1] - CARRIAGE_Y) * t, z0 + (rest[2] - z0) * t * t]), t => t);
    if (stale(g)) return;
    tint();
    lamp("carriage-lamp", null);
  }

  async function decide(outcome, instant) {
    const g = gen;
    const a = DIAL_AT[outcome] ?? DIAL_AT.rest;
    const from = st.needle;
    live.outcome = outcome;
    const lamps = {charged: "lamp-charged", held: "lamp-held", "not charged": "lamp-not"};
    const show = () => {
      for (const [k, id] of Object.entries(lamps)) lamp(id, k === outcome ? {charged: "charged", held: "held", "not charged": "not"}[k] : null);
    };
    if (instant) { setNeedle(a); show(); }
    else { await tween(900, t => setNeedle(from + (a - from) * t), spring); show(); }
    if (stale(g)) return;
    if (!lamps[outcome]) return;
    await moveCoin(outcome, instant);
    if (stale(g)) return;
  }

  async function moveCoin(outcome, instant) {
    const g = gen;
    if (outcome === "not charged") {
      lamp("lamp-kept", "charged");
      $("kept-ring").setAttribute("opacity", 1);
      if (!instant) await tween(600, t => place(coin, [COIN_REST[0], COIN_REST[1], COIN_REST[2] + Math.sin(t * Math.PI) * 6]));
      if (stale(g)) return;
      return;
    }
    const to = outcome === "charged" ? [LEDGER.x + 23, LEDGER.y + 18, LEDGER_TOP + 1] : [CAGE.x + CAGE.w / 2, CAGE.y + CAGE.d / 2, 4.4];
    if (!instant) {
      coinTo("galla");
      const from = COIN_REST;
      const peak = 92;
      await tween(1500, t => {
        const p = [from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t, from[2] + (to[2] - from[2]) * t + Math.sin(t * Math.PI) * (peak - Math.max(from[2], to[2]) * .4)];
        place(coin, p);
      });
      if (stale(g)) return;
    }
    coinTo(outcome === "charged" ? "ledger" : "held");
    if (outcome === "held") {
      if (instant) setCage(1); else await tween(800, setCage, t => 1 - Math.pow(1 - t, 2) * Math.abs(Math.cos(t * 7.5)) * (1 - t));
      if (stale(g)) return;
      $("padlock").setAttribute("opacity", 1);
    }
  }

  async function message(m, instant) {
    const g = gen;
    const to = m.to_whom;
    const cls = to === "manager" ? "sc-held" : to === "support" ? "sc-not" : "sc-accent";
    const env = make("g", {}, envSvg(cls));
    let dest;
    if (to === "support") { dest = [SPIKE[0], SPIKE[1], 6 + st.tickets * 1.6]; st.tickets++; }
    else if (to === "manager") { dest = [MANAGER.x + 9, MANAGER.y + 12, 16.2 + st.mgr * 1.4]; st.mgr++; }
    else { dest = [214, -10 + st.sms * 0, COUNTER_TOP + .2 + st.sms * 1.4]; st.sms++; }
    flying.appendChild(env);
    const from = [OUTTRAY.x + 10, OUTTRAY.y + 10, RULES_TOP + 4];
    if (!instant) {
      await tween(1100, t => {
        const p = [from[0] + (dest[0] - from[0]) * t, from[1] + (dest[1] - from[1]) * t, from[2] + (dest[2] - from[2]) * t + Math.sin(t * Math.PI) * 46];
        place(env, p);
      });
      if (stale(g)) return;
    }
    place(env, dest);
    if (to === "support") $("spike-tickets").appendChild(env);
    if (to === "manager") $("mgr-screen").setAttribute("class", "screen on");
  }

  // continuous parts: pulses, waves, ringing, mic level
  const mastWaves = [...$("mast-waves").children];
  const phoneWaves = [...$("phone-waves").children];
  const phone = $("phone"), phoneScreen = $("phone-screen"), beacon = $("beacon");
  const mastCenter = at([MAST[0], MAST[1], CALLER_TOP + 54]);
  const phoneCenter = at([PHONE_AT[0], PHONE_AT[1], COUNTER_TOP + 2]);
  const scaleAt = ([cx, cy], k) => `translate(${cx} ${cy}) scale(${k}) translate(${-cx} ${-cy})`;
  let level = 0;

  function frame(now) {
    for (const tw of [...tweens]) {
      const t = Math.min(1, (now - tw.t0) / tw.ms);
      tw.fn(tw.curve(t));
      if (t >= 1) { tweens.delete(tw); tw.done(); }
    }
    const speaking = live.speaking, hearing = live.hearing || !!inFlight;
    const sec = now / 1000;
    // pulses: out while Settled speaks, in while his reply travels
    if ((speaking || hearing) && !REDUCED) {
      const r = speaking ? routeOut : routeIn, l = speaking ? lenOut : lenIn;
      const base = inFlight && !speaking ? Math.min(1, (now - inFlight.t0) / inFlight.ms) : (sec * .32) % 1;
      dots.forEach((d, i) => {
        let t = inFlight && !speaking ? base - i * .035 : (base + i / PULSES) % 1;
        const vis = t >= 0 && t <= 1 ? Math.min(1, t * 10, (1 - t) * 10) : 0;
        t = Math.max(0, Math.min(1, t));
        const [x, y] = along(r, l, t);
        d.setAttribute("cx", x.toFixed(1)); d.setAttribute("cy", y.toFixed(1));
        d.setAttribute("opacity", (vis * (inFlight && !speaking ? 1 - i * .1 : 1)).toFixed(2));
        d.setAttribute("class", speaking ? "pulse" : "pulse in");
      });
    } else dots.forEach(d => d.setAttribute("opacity", 0));
    // radio waves at the mast while speaking, and at his phone
    mastWaves.forEach((w, i) => {
      const p = REDUCED ? .35 + i * .25 : (sec * .7 + i / 3) % 1;
      w.setAttribute("opacity", speaking ? ((1 - p) * .8).toFixed(2) : 0);
      if (speaking) w.setAttribute("transform", scaleAt(mastCenter, .6 + p * 1.9));
    });
    level += ((live.rec ? live.level : 0) - level) * .3;
    phoneWaves.forEach((w, i) => {
      if (live.rec) {
        const k = .5 + level * (1 + i * .55);
        w.setAttribute("opacity", (.25 + level * .7 - i * .12).toFixed(2));
        w.setAttribute("transform", scaleAt(phoneCenter, k));
        w.style.stroke = "var(--rec)";
      } else if (speaking) {
        const p = REDUCED ? .35 + i * .25 : (sec * .7 + i / 3) % 1;
        w.style.stroke = "";
        w.setAttribute("opacity", ((1 - p) * .7).toFixed(2));
        w.setAttribute("transform", scaleAt(phoneCenter, .5 + p * 1.4));
      } else w.setAttribute("opacity", 0);
    });
    // his phone buzzes while it rings
    if (live.ringing && !REDUCED) phone.setAttribute("transform", `translate(${(Math.sin(sec * 90) * .9 * (Math.sin(sec * 6) > 0 ? 1 : 0)).toFixed(2)} 0)`);
    else phone.removeAttribute("transform");
    phoneScreen.setAttribute("class", live.onCall || live.ringing ? "screen on" : "screen");
    lamp("mast-lamp", speaking ? "accent" : live.listening ? (live.rec ? "rec" : null) : null);
    if (live.listening && !live.rec) $("mast-lamp").setAttribute("class", REDUCED || Math.sin(sec * 4) > 0 ? "lamp on-accent" : "lamp");
    const fin = {charged: "var(--charged)", held: "var(--held)", "not charged": "var(--not)"}[live.outcome];
    const glow = fin || (live.onCall ? "var(--accent)" : "");
    if (beacon._on !== glow) { beacon._on = glow; glow ? (beacon.setAttribute("data-on", ""), beacon.style.setProperty("--b", glow)) : beacon.removeAttribute("data-on"); }
    const want = live.onCall ? 1 : 0;
    if (Math.abs(st.handset - want) > .002) setHandset(REDUCED ? want : st.handset + (want - st.handset) * .12);
    else if (st.handset !== want) setHandset(want);
    lamp("caller-lamp", live.onCall ? "accent" : null);
    const busy = st.handset !== want || tweens.size || (!REDUCED && (speaking || hearing || live.rec || live.ringing || live.listening));
    raf = busy && !document.hidden ? requestAnimationFrame(frame) : 0;
  }
  wakeFn = () => { if (!raf) raf = requestAnimationFrame(frame); };
  document.addEventListener("visibilitychange", () => { if (!document.hidden) wakeFn(); });

  reset();
  return {
    reset, setShop, records, call, answer, decide, message,
    setLive(flags) { Object.assign(live, flags); wakeFn(); },
  };
}
