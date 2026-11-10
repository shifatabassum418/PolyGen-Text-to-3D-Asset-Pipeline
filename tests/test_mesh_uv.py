"""Tests that need trimesh (and xatlas for UVs). Skipped automatically when those are not installed."""
import tempfile
import unittest

import numpy as np

from tests.helpers import has

HAS_TRIMESH = has("trimesh")


@unittest.skipUnless(HAS_TRIMESH, "trimesh not installed")
class MeshProcessingTests(unittest.TestCase):
    def test_clean_removes_floating_debris(self):
        import trimesh
        from app.mesh_processing import clean_mesh, mesh_stats

        big = trimesh.creation.icosphere(subdivisions=3)
        speck = trimesh.creation.box(extents=(0.01, 0.01, 0.01))
        speck.apply_translation([5, 5, 5])
        cleaned = clean_mesh(trimesh.util.concatenate([big, speck]))
        self.assertEqual(mesh_stats(cleaned)["components"], 1)

    def test_normalize_centers_and_scales(self):
        import trimesh
        from app.mesh_processing import normalize_mesh

        box = trimesh.creation.box(extents=(2, 4, 1))
        box.apply_translation([10, -3, 7])
        m = normalize_mesh(box)
        self.assertAlmostEqual(float(m.extents.max()), 1.0, places=6)
        self.assertTrue(np.allclose((m.bounds[0] + m.bounds[1]) / 2, 0, atol=1e-6))

    def test_stats_for_watertight_box(self):
        import trimesh
        from app.mesh_processing import mesh_stats

        s = mesh_stats(trimesh.creation.box())
        self.assertTrue(s["watertight"])
        self.assertEqual(s["faces"], 12)
        self.assertAlmostEqual(s["convexity"], 1.0, places=2)


@unittest.skipUnless(HAS_TRIMESH and has("xatlas"), "trimesh and xatlas required")
class UVUnwrapTests(unittest.TestCase):
    def test_xatlas_unwrap_gives_uvs_in_unit_square_and_keeps_surface(self):
        import trimesh
        from app.mesh_processing import normalize_mesh
        from app.uv import uv_unwrap

        out = uv_unwrap(normalize_mesh(trimesh.creation.box(extents=(1, 1, 1))))
        uv = out.visual.uv
        self.assertEqual(uv.shape, (len(out.vertices), 2))
        self.assertGreaterEqual(uv.min(), -1e-6)
        self.assertLessEqual(uv.max(), 1 + 1e-6)
        self.assertEqual(len(out.faces), 12)

    def test_unwrap_then_bake_then_export_validates(self):
        import trimesh
        from PIL import Image
        from app.mesh_processing import normalize_mesh
        from app.texturing import bake_projected_texture, write_textured_obj
        from app.uv import uv_unwrap
        from app.validation import validate_textured_export

        m = uv_unwrap(normalize_mesh(trimesh.creation.icosphere(subdivisions=2)))
        atlas = bake_projected_texture(m.vertices, m.faces, m.visual.uv, Image.new("RGB", (64, 64), (90, 140, 200)), atlas_size=128)
        with tempfile.TemporaryDirectory() as d:
            write_textured_obj(d, m.vertices, m.faces, m.visual.uv, atlas)
            self.assertEqual(validate_textured_export(d), [])


if __name__ == "__main__":
    unittest.main()
