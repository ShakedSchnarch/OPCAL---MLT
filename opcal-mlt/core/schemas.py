from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

LabelName = Literal["High-flat", "High-oscillatory", "Oscillatory", "Low-activity"]

class PreprocessConfig(BaseModel):
    filter: Dict[str, Any] = Field(default_factory=lambda: {"type":"savgol","window":31,"polyorder":3})
    baseline: Dict[str, Any] = Field(default_factory=lambda: {"method":"rolling_median","window_s":20.0})
    sd_method: str = "MAD"
    threshold_k: float = 3.0

class LabelRecord(BaseModel):
    recording_id: str
    cell_id: str
    fs_hz: float
    label: LabelName
    is_uncertain: bool = False
    notes: str = ""
    preprocess: PreprocessConfig = PreprocessConfig()
    features: Dict[str, float] = Field(default_factory=dict)
    peaks: List[int] = Field(default_factory=list)
    version: str = "mlt-0.1.0"
