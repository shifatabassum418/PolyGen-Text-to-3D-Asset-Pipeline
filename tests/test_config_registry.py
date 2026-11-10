"""Configuration and generator-registry tests (no torch / models needed)."""
import unittest

from app.config import settings
from app.generators import get_generator
from tests.helpers import has


class ConfigTests(unittest.TestCase):
    def test_paths_are_absolute_so_cwd_does_not_matter(self):
        self.assertTrue(settings.output_dir.is_absolute())
        self.assertTrue(settings.triposr_dir.is_absolute())
        self.assertTrue(str(settings.output_dir).endswith("outputs"))

    def test_default_generator_is_one_of_the_two_routes(self):
        self.assertIn(settings.default_generator, ("shape", "triposr"))


class RegistryTests(unittest.TestCase):
    def test_unknown_generator_raises(self):
        with self.assertRaises(ValueError):
            get_generator("does-not-exist")

    @unittest.skipUnless(has("torch"), "torch not installed")
    def test_triposr_reports_clear_error_when_not_installed(self):
        from app import generators

        if settings.triposr_dir.exists():
            self.skipTest("TripoSR is installed here")
        generators._CACHE.pop("triposr", None)
        with self.assertRaisesRegex(RuntimeError, "setup_triposr"):
            get_generator("triposr")


if __name__ == "__main__":
    unittest.main()
