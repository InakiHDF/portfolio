import * as THREE from "three";

// Sala reconstruida midiendo contra "Referencia Sala.png".
// Solo masas. Sin props chicos, sin luz de ambiente artistica.
// Eje x: izquierda(-) a derecha(+).  z: fondo(-) a frente(+).  y: alto.

export const ROOM = {
  backZ: -4.6, leftX: -6.7, rightX: 6.7, ceilY: 3.4, frontZ: 5.2
};

export function buildRoom(scene){
  const mats = [], targets = [];
  const M = (c,o) => { const m = new THREE.MeshLambertMaterial(
    Object.assign({color:c}, o||{})); mats.push(m); return m; };
  const B = (w,h,d) => new THREE.BoxGeometry(w,h,d);
  const add = (g,mat,x,y,z,ry) => { const m = new THREE.Mesh(g,mat);
    m.position.set(x,y,z); if (ry) m.rotation.y = ry; scene.add(m); return m; };
  const hot = (m,key,name) => { m.userData.key=key; m.userData.name=name;
    targets.push(m); return m; };

  const R = ROOM;
  const conc  = M(0x9c968b), floorW = M(0xb08a5c), ceil = M(0x3f3b36),
        wood  = M(0x6b4a2e), woodL = M(0x8a6135), dark = M(0x2f2d2b),
        black = M(0x1c1b1a), steel = M(0x6a6d72), cloth = M(0x6e737d),
        white = M(0xd8d4c9), green = M(0x38503a), screenM = M(0x8f9fae),
        rugD  = M(0x3a3936), rugL = M(0x9a938a), plant = M(0x3f6b38);

  // ── caja
  add(B(14,.3,11), floorW, 0,-.15,.3);
  add(B(14,.3,11), ceil,  0,R.ceilY+.15,.3);
  add(B(14,R.ceilY,.3), conc, 0,R.ceilY/2,R.backZ-.15);
  add(B(.3,R.ceilY,11), conc, R.leftX-.15,R.ceilY/2,.3);
  add(B(.3,R.ceilY,11), conc, R.rightX+.15,R.ceilY/2,.3);

  // ── A · escritorio de trabajo (desarrollos), pared del fondo izquierda
  add(B(4.3,.09,.86), wood, -4.5,.76,-4.1);
  add(B(.09,.76,.86), wood, -6.6,.38,-4.1);
  add(B(.78,.72,.82), wood, -2.85,.36,-4.1);
  [.14,.40,.66].forEach(y => add(B(.66,.16,.03), woodL, -2.85,y,-3.68));
  add(B(.32,.66,.56), dark,  -5.85,.33,-3.95);
  add(B(.06,.30,.02), M(0x2b3f52,{emissive:0x2f6f9a}), -5.68,.40,-3.66);
  const m1 = hot(add(B(.66,.40,.05), black, -5.05,1.02,-4.36), "web","desarrollos web");
  const m2 = hot(add(B(.66,.40,.05), black, -4.20,1.03,-4.33,-.10), "web","desarrollos web");
  add(B(.60,.35,.01), M(0x22303c,{emissive:0x2d6a94}), -5.05,1.02,-4.33);
  add(B(.60,.35,.01), M(0x22303c,{emissive:0x2d6a94}), -4.20,1.03,-4.30,-.10);
  add(B(.16,.10,.16), black, -5.05,.83,-4.33);
  add(B(.16,.10,.16), black, -4.20,.84,-4.30);
  add(B(.52,.03,.17), white, -4.72,.82,-3.86);
  add(B(.34,.01,.26), M(0x3d5f7a), -3.95,.81,-3.86);
  add(B(.20,.20,.20), white, -3.45,.90,-3.94);
  add(B(.22,.03,.22), black, -6.15,.81,-4.18);
  add(B(.04,.46,.04), black, -6.15,1.04,-4.18);
  add(B(.26,.14,.20), black, -5.98,1.24,-4.10);
  add(B(.52,.06,.52), steel, -4.35,.05,-3.30);
  add(B(.52,.09,.52), dark,  -4.35,.46,-3.30);
  add(B(.50,.56,.09), dark,  -4.35,.76,-3.55);
  add(B(.09,.42,.09), steel, -4.35,.26,-3.30);

  // estante de pared + cosas
  add(B(2.5,.07,.30), wood, -4.85,1.86,-4.44);
  add(B(.52,.16,.24), white, -5.75,1.97,-4.44);
  [0,1,2,3,4].forEach(i => add(B(.07,.34,.22), M([0xb8b2a4,0x33383d,0x8a4436,0x445a6b,0xd0c7b2][i]),
    -4.95+i*.10, 2.06,-4.44));
  add(new THREE.SphereGeometry(.15,10,8), M(0xf0e2c0,{emissive:0xffbb55}), -4.15,2.01,-4.44);
  add(B(.34,.90,.30), plant, -3.62,1.60,-4.40);

  // posters pared fondo izquierda + pared izquierda
  [[-6.05,2.35,.95,1.15],[-4.95,2.55,.95,.75],[-3.55,2.45,.60,.75]].forEach(p =>
    add(B(p[2],p[3],.03), M(0xe6e2d8), p[0],p[1],-4.55));
  add(B(.03,1.35,1.05), M(0xd8623a), R.leftX-.02,2.25,-3.90);
  add(B(.03,.80,.70), M(0xe6e2d8), R.leftX-.02,1.30,-3.35);

  // ── B · puerta verde y escalones
  add(B(2.0,.44,1.0), conc, -1.30,.22,-4.05);
  add(B(2.0,.22,.34), conc, -1.30,.11,-3.42);
  add(B(1.00,2.15,.10), green, -1.30,1.52,-4.52);
  add(B(.05,.05,.05), M(0xc9a24a), -0.92,1.45,-4.45);

  // ── C · escalera que sube hacia la derecha (bajo la cual va la consola)
  for (let i=0;i<9;i++){
    add(B(.34,.13,1.05), wood, -0.05+i*.34, .62+i*.255, -4.10);
    add(B(.34,.24,.06), woodL, -0.05+i*.34, .48+i*.255, -3.60);
  }
  const rail = new THREE.Group(); rail.position.set(1.35,1.95,-3.58);
  rail.rotation.z = .64; scene.add(rail);
  rail.add(new THREE.Mesh(B(3.6,.09,.09), steel));
  const railBot = new THREE.Mesh(B(3.6,.07,.07), steel); railBot.position.y = -.62;
  rail.add(railBot);
  for (let i=0;i<7;i++){
    const p = new THREE.Mesh(B(.05,.62,.05), steel);
    p.position.set(-1.55+i*.52,-.31,0); rail.add(p); }
  const under = add(B(3.5,1.9,.10), M(0x4a3a28), 1.35,1.35,-4.16);
  under.rotation.z = .64;

  // ── D · estante alto con botellas (al lado de la escalera)
  add(B(1.05,1.60,.34), wood, -0.30,2.30,-4.42);
  [1.72,2.22,2.72].forEach(y => add(B(.92,.05,.28), woodL, -0.30,y,-4.42));

  // ── E · mueble oscuro angosto
  add(B(.62,1.30,.44), black, 0.72,.65,-4.30);
  [.35,.72,1.08].forEach(y => add(B(.54,.04,.36), dark, 0.72,y,-4.30));

  // ── F · panel de malla con fotos
  add(B(1.70,1.55,.04), M(0x4a4640), 1.85,1.60,-4.54);
  [[-.5,.45],[.1,.55],[.55,.30],[-.25,-.2],[.35,-.35]].forEach(p =>
    add(B(.26,.32,.02), white, 1.85+p[0],1.60+p[1],-4.50));

  // ── G · consola de medios
  add(B(3.10,.74,.66), wood, 2.05,.37,-4.10);
  add(B(3.00,.05,.60), dark, 2.05,.52,-4.08);
  add(B(.50,.28,.42), white, 1.00,.88,-4.10);
  add(B(.58,.14,.46), black, 2.20,.81,-4.10);
  add(new THREE.CylinderGeometry(.16,.16,.02,14), M(0x8a8a86), 2.20,.89,-4.10);
  [[2.95,.86],[3.55,.83]].forEach(p => add(B(.44,.10,.34), dark, p[0],p[1],-4.10));

  // ── H · pantalla de proyeccion
  const scr = hot(add(B(2.75,1.62,.05), screenM, 3.55,2.10,-4.48), "video","videos");
  add(B(2.90,1.78,.03), M(0x33312e), 3.55,2.10,-4.52);
  add(B(2.90,.10,.10), M(0x33312e), 3.55,2.99,-4.50);

  // ── I · planta grande
  add(new THREE.CylinderGeometry(.30,.24,.55,8), M(0x55524d), 2.92,.28,-3.35);
  add(new THREE.ConeGeometry(.55,1.25,7), plant, 2.92,1.15,-3.35);

  // ── J · estanteria de vinilos + equipo (musica)
  add(B(2.85,1.28,.52), wood, 5.30,.64,-4.10);
  add(B(2.75,.05,.46), woodL, 5.30,.64,-4.10);
  [3.98,4.65,5.32,5.99,6.66].forEach(x => add(B(.05,1.20,.46), woodL, x,.64,-4.10));
  const hifi = hot(add(B(.80,.20,.42), black, 5.25,1.38,-4.05), "musica","música");
  add(B(.62,.05,.30), M(0x1e2226,{emissive:0x3f9a6a}), 5.25,1.44,-3.86);
  add(B(.66,.12,.46), black, 5.28,1.58,-4.05);
  add(new THREE.CylinderGeometry(.18,.18,.02,14), M(0x8a8a86), 5.28,1.65,-4.05);
  [[4.10],[6.45]].forEach(p => {
    add(B(.42,.62,.36), black, p[0],1.59,-4.05);
    add(new THREE.CylinderGeometry(.13,.13,.04,12), M(0x3a3937), p[0],1.72,-3.86,1.5708);
    add(new THREE.CylinderGeometry(.07,.07,.04,10), M(0x3a3937), p[0],1.45,-3.86,1.5708); });
  add(new THREE.CylinderGeometry(.09,.14,.46,10), M(0xd8802a,{emissive:0xd8802a}), 4.72,1.51,-3.95);
  add(new THREE.TorusGeometry(.13,.05,6,12), black, 6.10,1.48,-3.86);

  // ── K/L · reja de fotos y reloj (pared derecha del fondo)
  add(B(2.70,1.35,.04), M(0x3d3b38), 5.55,2.62,-4.54);
  [[-.75,.35],[-.15,.42],[.45,.28],[.95,.40],[-.45,-.28],[.30,-.30],[.90,-.18]].forEach(p =>
    add(B(.30,.34,.02), white, 5.55+p[0],2.62+p[1],-4.50));
  add(new THREE.CylinderGeometry(.24,.24,.05,18), black, 4.35,2.05,-4.50,1.5708);
  [[-.62,.16],[-.05,.20],[.42,.14]].forEach(p =>
    add(B(.22,.16,.02), M(0xc98a4a), 3.95+p[0],1.72+p[1],-4.50));

  // ── M · planta derecha
  add(new THREE.CylinderGeometry(.28,.22,.5,8), M(0x55524d), 6.45,.25,-3.55);
  add(new THREE.ConeGeometry(.5,1.4,7), plant, 6.45,1.15,-3.55);

  // ── N · cama (primer plano izquierda)
  const bed = new THREE.Group(); bed.position.set(-4.10,0,3.35); bed.rotation.y = .30;
  scene.add(bed);
  const bput = (g,mat,x,y,z) => { const m=new THREE.Mesh(g,mat);
    m.position.set(x,y,z); bed.add(m); return m; };
  bput(B(2.15,.42,2.85), dark, 0,.21,0);
  bput(B(2.10,.26,2.80), cloth, 0,.53,0);
  bput(B(2.05,.10,1.30), M(0x8b909a), 0,.68,.60);
  bput(B(.86,.20,.58), white, -.52,.72,-1.02);
  bput(B(.86,.20,.58), white,  .48,.72,-1.02);
  bput(B(.92,.28,.62), black, -.30,.74,.15);

  // ── O · alfombra
  add(B(4.60,.03,3.70), rugD, .35,.02,-1.35,.08);
  for (let i=0;i<24;i++){
    const cx = -1.65 + (i%6)*.66, cz = -2.75 + Math.floor(i/6)*.95;
    add(B(.55,.04,.72), (i*7%3===0)?rugL:M(0x746d64), .35+cx,.035,-1.35+cz,.08);
  }

  // ── P · mesa baja
  add(B(1.62,.10,.82), woodL, .55,.42,-1.95,.08);
  [[-.68,-.30],[.68,-.30],[-.68,.30],[.68,.30]].forEach(p =>
    add(B(.09,.42,.09), wood, .55+p[0],.21,-1.95+p[1]));
  add(B(.42,.10,.30), white, .30,.52,-2.05,.15);
  add(B(.30,.05,.20), black, .95,.50,-1.85,-.2);

  // ── Q · escritorio de escritos (primer plano derecha)
  const dsk = new THREE.Group(); dsk.position.set(4.55,0,4.10); dsk.rotation.y = -.16;
  scene.add(dsk);
  const dput = (g,mat,x,y,z,ry) => { const m=new THREE.Mesh(g,mat);
    m.position.set(x,y,z); if (ry) m.rotation.y=ry; dsk.add(m); return m; };
  dput(B(4.20,.10,2.00), woodL, 0,.74,0);
  [[-1.95,-.85],[1.95,-.85],[-1.95,.85],[1.95,.85]].forEach(p =>
    dput(B(.14,.74,.14), wood, p[0],.37,p[1]));
  const papers = hot(dput(B(3.30,.03,1.55), white, -.15,.80,0), "texto","escritos");
  for (let i=0;i<8;i++) dput(B(.56,.02,.78), white,
    -1.35+(i%4)*.78, .82+(i>3?.02:0), -.38+(i>3?.62:0), ((i*53)%40-20)*Math.PI/180);
  dput(B(.72,.14,.56), white, .95,.87,-.28,.12);
  dput(new THREE.CylinderGeometry(.10,.10,.22,8), dark, 1.35,.90,.42);
  dput(B(.34,.03,.34), steel, 1.72,.80,-.55);
  dput(B(.06,.62,.06), steel, 1.72,1.10,-.55);
  dput(new THREE.ConeGeometry(.22,.26,10), steel, 1.60,1.44,-.42);
  // silla de respaldo curvo
  dput(B(.52,.06,.52), wood, -1.15,.46,1.30);
  dput(B(.52,.52,.09), woodL, -1.15,.76,1.54);
  [[-.21,1.09],[.21,1.09],[-.21,1.51],[.21,1.51]].forEach(p =>
    dput(B(.07,.46,.07), wood, -1.15+p[0],.23,p[1]));

  // ── luces de techo (solo la carcasa)
  [-5.1,-4.5,-3.9].forEach(x => {
    add(B(.16,.26,.16), dark, x,3.18,-3.25);
    add(B(.13,.07,.13), M(0xf2e6c8,{emissive:0xffcc77}), x,3.03,-3.25); });
  add(B(2.0,.07,.07), dark, -4.5,3.32,-3.25);

  // ── personaje (placeholder)
  const stand = new THREE.Group();
  stand.position.set(-2.60,0,0.60); stand.rotation.y = 2.7; scene.add(stand);
  if (new URLSearchParams(location.search).get("nochar")) stand.visible = false;
  const ph = new THREE.Group(); stand.add(ph);
  const skin = M(0xb98a63), shirt = M(0x33465a), pant = M(0x26282c);
  const part = (g,mat,x,y,z) => { const m=new THREE.Mesh(g,mat);
    m.position.set(x,y,z); ph.add(m); return m; };
  hot(part(B(.58,.80,.31), shirt, 0,1.48,0), "mi","sobre mí");
  part(new THREE.SphereGeometry(.22,10,8), skin, 0,2.08,0);
  part(B(.18,.76,.18), pant, -.14,.53,0);
  part(B(.18,.76,.18), pant, .14,.53,0);
  part(B(.14,.68,.14), shirt, -.36,1.46,.04);
  part(B(.14,.68,.14), shirt, .36,1.46,.04);

  return { mats, targets, stand, placeholder: ph };
}

export function buildLights(scene){
  // Luz pareja a proposito: sirve para juzgar geometria, no atmosfera.
  scene.add(new THREE.AmbientLight(0xffffff, 1.9));
  const a = new THREE.DirectionalLight(0xffffff, .9); a.position.set(3,7,8);
  scene.add(a);
  const b = new THREE.DirectionalLight(0xcfd8e6, .5); b.position.set(-6,4,4);
  scene.add(b);
}
