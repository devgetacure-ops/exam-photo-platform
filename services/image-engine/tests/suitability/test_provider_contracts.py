from PIL import Image
from tests.fakes.fake_face_detector import FakeFaceDetector
from tests.fakes.fake_head_estimator import FakeHeadEstimator

from exam_photo.providers.capabilities import ProviderCapabilities
from exam_photo.providers.face_detection import FaceDetectionProvider
from exam_photo.providers.head_estimation import HeadEstimationProvider


def test_face_provider_contract() -> None:
    fake_face = FakeFaceDetector()
    assert isinstance(fake_face, FaceDetectionProvider)

    dummy_img = Image.new("RGB", (10, 10))
    res = fake_face.detect_faces(dummy_img)
    assert res.provider_name == "FakeFaceDetector"
    assert isinstance(res.capabilities, ProviderCapabilities)


def test_head_provider_contract() -> None:
    fake_head = FakeHeadEstimator()
    assert isinstance(fake_head, HeadEstimationProvider)
