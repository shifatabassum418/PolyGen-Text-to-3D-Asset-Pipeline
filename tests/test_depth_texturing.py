"""Pure NumPy/PIL tests: depth rendering, texture baking, textured OBJ export, export validation."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from app.depth import render_depth
from app.texturing import bake_projected_texture, write_textured_obj
from app.validation import validate_textured_export
from tests.helpers import make_box, trivial_unwrap


class DepthTests(unittest.TestCase):
    def test_box_center_is_near_and_corner_is_background(self):
        v, f = make_box((0.5, 0.5, 0.5))
        img = np.asarray(render_depth(v, f, resolution=64))[:, :, 0]
        self.assertGreater(img[32, 32], 200)  # front face is the nearest part of the box
        self.assertEqual(img[0, 0], 0)

    def test_elongated_box_silhouette_changes_with_azimuth(self):
        v, f = make_box((1.0, 0.2, 0.2))
        front = (np.asarray(render_depth(v, f, azimuth_deg=0, resolution=64))[:, :, 0] > 0).sum()
        side = (np.asarray(render_depth(v, f, azimuth_deg=90, resolution=64))[:, :, 0] > 0).sum()
        self.assertGreater(front, 2 * side)

    def test_output_is_rgb_image_of_requested_size(self):
        v, f = make_box()
        img = render_depth(v, f, resolution=48)
        self.assertEqual((img.size, img.mode), ((48, 48), "RGB"))


class BakeTests(unittest.TestCase):
    def setUp(self):
        v, f = make_box((0.5, 0.5, 0.5))
        self.v, self.f, self.uv = trivial_unwrap(v, f)

    def test_solid_image_fills_the_whole_atlas(self):
        red = Image.new("RGB", (64, 64), (200, 30, 30))
        atlas = np.asarray(bake_projected_texture(self.v, self.f, self.uv, red, atlas_size=128))
        self.assertEqual(atlas.shape, (128, 128, 3))
        self.assertTrue((atlas == [200, 30, 30]).all())

    def test_back_faces_sample_the_mirrored_image(self):
        S = 256
        img = np.zeros((64, 64, 3), np.uint8)
        img[:, :32] = (255, 0, 0)   # left half red
        img[:, 32:] = (0, 0, 255)   # right half blue
        atlas = np.asarray(bake_projected_texture(self.v, self.f, self.uv, Image.fromarray(img), atlas_size=S))
        tri = self.v[self.f]
        nz = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])[:, 2]
        cx = tri[:, :, 0].mean(axis=1)

        def color_at_centroid(face):
            u, w = self.uv[self.f[face]].mean(axis=0)
            return atlas[int(round((1 - w) * (S - 1))), int(round(u * (S - 1)))]

        front_right = next(i for i in range(len(self.f)) if nz[i] > 0 and cx[i] > 0.05)
        back_right = next(i for i in range(len(self.f)) if nz[i] < 0 and cx[i] > 0.05)
        self.assertGreater(color_at_centroid(front_right)[2], color_at_centroid(front_right)[0])  # blue
        self.assertGreater(color_at_centroid(back_right)[0], color_at_centroid(back_right)[2])    # mirrored -> red


class ExportTests(unittest.TestCase):
    def setUp(self):
        v, f = make_box((0.5, 0.5, 0.5))
        self.v, self.f, self.uv = trivial_unwrap(v, f)
        self.img = Image.new("RGB", (32, 32), (10, 200, 10))

    def test_written_obj_has_expected_records_and_validates(self):
        with tempfile.TemporaryDirectory() as d:
            files = write_textured_obj(d, self.v, self.f, self.uv, self.img)
            lines = (Path(d) / files["obj"]).read_text().splitlines()
            self.assertEqual(sum(l.startswith("v ") for l in lines), len(self.v))
            self.assertEqual(sum(l.startswith("vt ") for l in lines), len(self.uv))
            self.assertEqual(sum(l.startswith("f ") for l in lines), len(self.f))
            self.assertEqual(validate_textured_export(d), [])

    def test_uv_count_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                write_textured_obj(d, self.v, self.f, self.uv[:-1], self.img)

    def test_validator_reports_missing_texture_file(self):
        with tempfile.TemporaryDirectory() as d:
            files = write_textured_obj(d, self.v, self.f, self.uv, self.img)
            (Path(d) / files["texture"]).unlink()
            self.assertTrue(any("does not exist" in p for p in validate_textured_export(d)))

    def test_validator_reports_out_of_range_uvs(self):
        with tempfile.TemporaryDirectory() as d:
            write_textured_obj(d, self.v, self.f, self.uv * 3.0, self.img)
            self.assertTrue(any("outside [0,1]" in p for p in validate_textured_export(d)))

    def test_validator_reports_missing_obj(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(validate_textured_export(d), ["model.obj is missing"])


if __name__ == "__main__":
    unittest.main()
