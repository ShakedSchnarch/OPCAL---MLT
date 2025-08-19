"""
This module defines data models for the OPCAL-Labeler tool using Pydantic.
It provides schemas for preprocessing configuration and labeled electrophysiology records,
enabling robust data validation and serialization throughout the labeling and analysis pipeline.

Type hints are included in docstrings for clarity, even though Pydantic enforces types at runtime.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

# LabelName is the controlled vocabulary of allowed label categories for cell activity.
LabelName = Literal["High-flat", "High-oscillatory", "Oscillatory", "Low-activity", "Drifting"]

class PreprocessConfig(BaseModel):
    """
    Configuration for preprocessing electrophysiological data.

    Fields:
        filter (Dict[str, Any]): Parameters for signal filtering.
            Default: {"type": "savgol", "window": 31, "polyorder": 3}
        baseline (Dict[str, Any]): Parameters for baseline correction.
            Default: {"method": "rolling_median", "window_s": 20.0}
        sd_method (str): Standard deviation estimation method. Default: "MAD"
        threshold_k (float): Threshold multiplier for event detection. Default: 3.0
    """
    filter: Dict[str, Any] = Field(default_factory=lambda: {"type":"savgol","window":31,"polyorder":3})
    baseline: Dict[str, Any] = Field(default_factory=lambda: {"method":"rolling_median","window_s":20.0})
    sd_method: str = "MAD"
    threshold_k: float = 3.0

class LabelRecord(BaseModel):
    """
    A labeled record for a single cell in a recording, including metadata, label, and preprocessing details.

    Fields:
        recording_id (str): Unique identifier for the recording.
        cell_id (str): Identifier for the cell within the recording.
        fs_hz (float): Sampling frequency in Hz.
        label (LabelName): Assigned label from the controlled vocabulary.
        uncertain (bool): If True, label is flagged as uncertain. Default: False
        notes (str): Optional notes or comments about the record. Default: ""
        preprocess (PreprocessConfig): Preprocessing configuration applied to the data. Default: PreprocessConfig()
        features (Dict[str, float]): Extracted numeric features for analysis. Default: empty dict
        peaks (List[int]): List of detected peak indices. Default: empty list
        version (str): Schema or tool version. Default: "mlt-0.1.0"
    """
    recording_id: str
    cell_id: str
    fs_hz: float
    label: LabelName
    uncertain: bool = False
    notes: str = ""
    preprocess: PreprocessConfig = PreprocessConfig()
    features: Dict[str, float] = Field(default_factory=dict)
    peaks: List[int] = Field(default_factory=list)
    version: str = "mlt-0.1.0"
