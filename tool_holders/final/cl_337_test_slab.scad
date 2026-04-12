// Test slab for fit validation
// Drop tool onto slab to check pocket fit before full print

/* [Slab Settings] */
// Margin around tool outline in mm
margin = 10; // [5:1:30]
// Slab thickness in mm
slab_height = 0.60; // [0.20:0.20:2.0]

linear_extrude(height = slab_height)
difference() {
    offset(delta = margin)
        scale([25.4, 25.4])
            import("cl_337_contour_1.dxf");
    scale([25.4, 25.4])
        import("cl_337_contour_1.dxf");
}
