"""DXF bounding box measurement and scoop position calculation."""
import os
import ezdxf


def _collect_dxf_points(msp):
    """Collect all XY points from DXF entities, handling different entity types."""
    pts = []
    for e in msp:
        etype = e.dxftype()
        if etype == 'LWPOLYLINE':
            pts.extend((p[0], p[1]) for p in e.get_points())
        elif etype == 'POLYLINE':
            pts.extend((v.dxf.location.x, v.dxf.location.y) for v in e.vertices)
        elif etype == 'LINE':
            pts.append((e.dxf.start.x, e.dxf.start.y))
            pts.append((e.dxf.end.x, e.dxf.end.y))
        elif etype == 'SPLINE':
            # Use flattened approximation for accurate bounding box
            try:
                pts.extend((p[0], p[1]) for p in e.flattening(0.01))
            except Exception:
                pts.extend((p[0], p[1]) for p in e.control_points)
        elif etype == 'ARC':
            try:
                pts.extend((p[0], p[1]) for p in e.flattening(0.01))
            except Exception:
                pts.append((e.dxf.center.x, e.dxf.center.y))
        elif etype == 'CIRCLE':
            cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
            pts.extend([(cx - r, cy), (cx + r, cy), (cx, cy - r), (cx, cy + r)])
        else:
            try:
                pts.extend((p[0], p[1]) for p in e.get_points())
            except Exception:
                pass
    return pts


def measure_dxf_bounding_box(dxf_path, folder_path, splitDXF=False):
    """Measure DXF cutout dimensions in mm. Returns 'Length x Width' string or empty.
    When split, measures ALL DXF files and reports the largest bounding box (the main tool)."""
    try:
        if splitDXF and isinstance(dxf_path, list):
            # Measure all split DXFs, keep the largest (main tool outline)
            best_length = 0
            best_width = 0
            for p in dxf_path:
                measure_file = os.path.join(folder_path, os.path.basename(p))
                doc = ezdxf.readfile(measure_file)
                msp = doc.modelspace()
                pts = _collect_dxf_points(msp)
                if not pts:
                    continue
                l = (max(pt[0] for pt in pts) - min(pt[0] for pt in pts)) * 25.4
                w = (max(pt[1] for pt in pts) - min(pt[1] for pt in pts)) * 25.4
                if l * w > best_length * best_width:
                    best_length, best_width = l, w
            if best_length == 0:
                return ""
            return f"\nCutout: {best_length:.1f}mm x {best_width:.1f}mm"
        else:
            measure_file = os.path.join(folder_path, os.path.basename(dxf_path))
            doc = ezdxf.readfile(measure_file)
            msp = doc.modelspace()
            pts = _collect_dxf_points(msp)
            if not pts:
                return ""
            length_mm = (max(p[0] for p in pts) - min(p[0] for p in pts)) * 25.4
            width_mm = (max(p[1] for p in pts) - min(p[1] for p in pts)) * 25.4
            return f"\nCutout: {length_mm:.1f}mm x {width_mm:.1f}mm"
    except Exception:
        return ""


def calculate_scoop_positions(dxf_path, folder_path, gridy_size, splitDXF=False):
    """Calculate Y positions for finger scoops from DXF tool outline edges.
    When split, finds the largest contour (main tool) for scoop positioning."""
    scoop_y_pos = gridy_size * 42 / 2
    scoop_y_neg = gridy_size * 42 / 2
    try:
        if splitDXF and isinstance(dxf_path, list):
            # Find the largest split DXF (main tool outline)
            best_area = 0
            best_pts = None
            for p in dxf_path:
                measure_file = os.path.join(folder_path, os.path.basename(p))
                doc = ezdxf.readfile(measure_file)
                msp = doc.modelspace()
                pts = _collect_dxf_points(msp)
                if not pts:
                    continue
                l = max(pt[0] for pt in pts) - min(pt[0] for pt in pts)
                w = max(pt[1] for pt in pts) - min(pt[1] for pt in pts)
                if l * w > best_area:
                    best_area = l * w
                    best_pts = pts
            if best_pts:
                scoop_y_pos = max(pt[1] for pt in best_pts) * 25.4
                scoop_y_neg = abs(min(pt[1] for pt in best_pts)) * 25.4
        else:
            measure_file = os.path.join(folder_path, os.path.basename(dxf_path))
            doc = ezdxf.readfile(measure_file)
            msp = doc.modelspace()
            pts = _collect_dxf_points(msp)
            if pts:
                scoop_y_pos = max(p[1] for p in pts) * 25.4
                scoop_y_neg = abs(min(p[1] for p in pts)) * 25.4
    except Exception:
        pass
    return scoop_y_pos, scoop_y_neg
