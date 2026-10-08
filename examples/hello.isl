# ISL P1 / synthetic numeric demonstration, not inferred from text.
isl 0.1;

axis joy;
axis calm;

record morning {
  text "今天心情很好。";
  context "invented demonstration";
  provenance "manual synthetic coordinates, not AI-inferred";
  joy = [0.75, 0.90];
  calm = [0.45, 0.65];
}

record evening {
  text "今天還不錯。";
  context "invented demonstration";
  provenance "manual synthetic coordinates, not AI-inferred";
  joy = [0.60, 0.80];
  calm = [0.50, 0.70];
}

let shared = intersect(morning.joy, evening.joy);
let combined = union(morning.calm, evening.calm);
let mix = blend(morning.joy, evening.joy, 0.5);
let ranking = cosine(morning, evening);
let strong_joy = filter(joy, lower >= 0.70);

print shared;
print combined;
print mix;
print ranking;
print strong_joy;
