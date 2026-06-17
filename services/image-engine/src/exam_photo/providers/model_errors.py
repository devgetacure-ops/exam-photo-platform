"""Typed exceptions for model-asset management in the face-detection provider."""


class ModelNotFoundError(RuntimeError):
    """Raised when the configured model asset file does not exist.

    The operator must acquire the model file using the provided download script
    (scripts/download_model.py) before running face detection.
    """


class ModelChecksumError(RuntimeError):
    """Raised when the SHA-256 digest of the model file does not match the
    expected value recorded in the model manifest.

    The model file may be corrupted or tampered with.  Delete it and re-acquire
    it using scripts/download_model.py.
    """
