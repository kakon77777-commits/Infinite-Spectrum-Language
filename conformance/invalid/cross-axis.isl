isl 0.1;
axis joy;
axis calm;
record x { text "toy"; context "toy"; provenance "manual"; joy = [0.1,0.3]; calm = [0.7,0.8]; }
let x2 = union(x.joy, x.calm);
