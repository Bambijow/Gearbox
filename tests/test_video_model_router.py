"""No-billing video routing contract tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import video_model_router as router
from video_fal import source_image

class VideoRoutingTests(unittest.TestCase):
    def test_requires_image(self):
        self.assertEqual(router.select()["blocker"],"IMAGE_REFERENCE_REQUIRED")
        self.assertEqual(router.select()["predecessor_task_kind"],"asset-image")
    def test_cheap_simple(self):
        result=router.select(has_image=True)
        self.assertFalse(result["blocked"])
        self.assertEqual(result["estimated_usd"],0.35)
    def test_standard_requires_more_capability(self):
        self.assertEqual(router.select(has_image=True,complexity="standard")["model"],"wan/v2.6/image-to-video")
    def test_multishot(self):
        self.assertEqual(router.select(has_image=True,multi_shot=True)["model"],"wan/v2.6/image-to-video")
    def test_cinematic_requires_frame_pair(self):
        self.assertEqual(router.select(has_image=True,complexity="cinematic",duration=8,max_usd=4,first_last=True)["estimated_usd"],1.6)
    def test_budget_failure_no_downgrade(self):
        self.assertEqual(router.select(has_image=True,complexity="cinematic",duration=8,max_usd=1,first_last=True)["blocker"],"VIDEO_BUDGET_EXCEEDED")
    def test_invalid_reference(self):
        with self.assertRaises(ValueError):
            source_image("/path/which/does/not/exist.png")
        with self.assertRaises(ValueError):
            source_image("http://example.com/still.png")
if __name__=="__main__":unittest.main()
