// Test slab for fit validation — ~10-15 min print
// Drop tool onto slab to check pocket fit before full print
$fa = 6;
$fs = 0.4;
difference() {
    cube([7*42, 2*42, 1.2], center=true);
    translate([0, 0, -0.1])\n        linear_extrude(height = 1.6)\n            scale([25.4, 25.4])\n                import("cl_420_contour_1.dxf");
}
