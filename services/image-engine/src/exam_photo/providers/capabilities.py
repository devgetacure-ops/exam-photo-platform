from pydantic import BaseModel


class ProviderCapabilities(BaseModel):
    multiple_face_detection: bool = False
    landmarks: bool = False
    pose: bool = False
    eye_visibility: bool = False
    occlusion: bool = False
    head_bounds: bool = False
    hair_boundary_estimation: bool = False
    ear_visibility: bool = False
    chin_visibility: bool = False
    beard_boundary_visibility: bool = False
    confidence_values: bool = False
    cpu_execution: bool = True
    deterministic_execution: bool = True
