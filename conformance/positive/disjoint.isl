isl 0.1;
axis intensity;
record low {
  text "example low";
  context "toy";
  provenance "manual";
  intensity = [0.10, 0.20];
}
record high {
  text "example high";
  context "toy";
  provenance "manual";
  intensity = [0.80, 0.90];
}
let overlap = intersect(low.intensity, high.intensity);
let regions = union(low.intensity, high.intensity);
print overlap;
print regions;
