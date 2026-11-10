"""API tests using FastAPI's TestClient with the heavy pipeline replaced by a fake. Need fastapi + httpx."""
import time
import unittest

from tests.helpers import has


@unittest.skipUnless(has("fastapi") and has("httpx"), "fastapi/httpx not installed")
class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from app import main

        cls.main = main
        cls.client = TestClient(main.app)

    def _wait(self, job_id, timeout=5.0):
        end = time.time() + timeout
        while time.time() < end:
            job = self.client.get(f"/api/jobs/{job_id}").json()
            if job["status"] != "running":
                return job
            time.sleep(0.05)
        self.fail("job did not finish")

    def test_health(self):
        body = self.client.get("/api/health").json()
        self.assertTrue(body["ok"])
        self.assertIn("device", body)

    def test_prompt_too_short_is_rejected(self):
        self.assertEqual(self.client.post("/api/generate", json={"prompt": "a"}).status_code, 422)

    def test_unknown_generator_is_rejected(self):
        r = self.client.post("/api/generate", json={"prompt": "a chair", "generator": "nope"})
        self.assertEqual(r.status_code, 422)

    def test_unknown_job_is_404(self):
        self.assertEqual(self.client.get("/api/jobs/doesnotexist").status_code, 404)

    def test_successful_job_reports_result_urls(self):
        original = self.main.run_pipeline
        self.main.run_pipeline = lambda *a, **k: {"obj": "model.obj", "mtl": "model.mtl", "stats": {"faces": 12}}
        try:
            job = self.client.post("/api/generate", json={"prompt": "a wooden chair", "generator": "shape", "texture": "flat"}).json()
            done = self._wait(job["id"])
        finally:
            self.main.run_pipeline = original
        self.assertEqual(done["status"], "done")
        self.assertTrue(done["result"]["obj_url"].endswith("/model.obj"))
        self.assertTrue(done["result"]["mtl_url"].endswith("/model.mtl"))

    def test_pipeline_failure_is_reported_not_hung(self):
        original = self.main.run_pipeline

        def boom(*a, **k):
            raise RuntimeError("model download failed")

        self.main.run_pipeline = boom
        try:
            job = self.client.post("/api/generate", json={"prompt": "a wooden chair"}).json()
            done = self._wait(job["id"])
        finally:
            self.main.run_pipeline = original
        self.assertEqual(done["status"], "error")
        self.assertIn("model download failed", done["error"])

    def test_triposr_without_install_returns_400(self):
        if self.main.settings.triposr_dir.exists():
            self.skipTest("TripoSR installed")
        r = self.client.post("/api/generate", json={"prompt": "a wooden chair", "generator": "triposr"})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
