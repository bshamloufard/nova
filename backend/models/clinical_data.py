"""Clinical data extraction models."""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ActionItemCategory(str, Enum):
    """Categories for clinical action items."""
    PRESCRIPTION = "prescription"
    FOLLOW_UP = "follow_up"
    REFERRAL = "referral"
    TEST = "test"
    OTHER = "other"


class ActionItemPriority(str, Enum):
    """Priority levels for action items."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NumericalCategory(str, Enum):
    """Categories for numerical values."""
    VITAL = "vital"
    LAB = "lab"
    MEASUREMENT = "measurement"
    DOSAGE = "dosage"


class TimelineMarkerType(str, Enum):
    """Types of markers on the timeline."""
    ACTION_ITEM = "action_item"
    NUMERICAL_VALUE = "numerical_value"
    UNCERTAIN = "uncertain"
    ORCHESTRATOR_RESOLVED = "orchestrator_resolved"


class ActionItem(BaseModel):
    """A clinical action item extracted from the transcription."""
    
    text: str = Field(..., description="The action item text")
    category: ActionItemCategory = Field(..., description="Category of action")
    priority: ActionItemPriority = Field(default=ActionItemPriority.MEDIUM)
    timestamp_ms: int = Field(..., description="Position in audio where mentioned")
    related_segment_index: int = Field(default=0, description="Index of related transcript segment")
    keywords: List[str] = Field(default_factory=list, description="Keywords that triggered detection")


class NumericalValue(BaseModel):
    """A numerical value extracted from the transcription (vitals, labs, dosages)."""
    
    value: str = Field(..., description="The numerical value as string")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    category: NumericalCategory = Field(..., description="Type of measurement")
    label: str = Field(..., description="Human-readable label (e.g., 'blood pressure')")
    timestamp_ms: int = Field(..., description="Position in audio where mentioned")
    related_segment_index: int = Field(default=0, description="Index of related transcript segment")
    raw_text: str = Field(default="", description="Original text that was parsed")


class ClinicalExtraction(BaseModel):
    """Complete clinical data extraction from a transcription."""
    
    action_items: List[ActionItem] = Field(default_factory=list)
    numerical_values: List[NumericalValue] = Field(default_factory=list)
    important_phrases: List[str] = Field(default_factory=list)
    medical_terms: List[str] = Field(default_factory=list)
    
    @property
    def action_item_count(self) -> int:
        return len(self.action_items)
    
    @property
    def numerical_value_count(self) -> int:
        return len(self.numerical_values)
    
    def get_action_items_by_category(self, category: ActionItemCategory) -> List[ActionItem]:
        """Filter action items by category."""
        return [item for item in self.action_items if item.category == category]
    
    def get_numerical_values_by_category(self, category: NumericalCategory) -> List[NumericalValue]:
        """Filter numerical values by category."""
        return [value for value in self.numerical_values if value.category == category]


class TimelineMarker(BaseModel):
    """A marker on the audio timeline."""
    
    start_ms: int = Field(..., description="Marker start position")
    end_ms: int = Field(..., description="Marker end position")
    type: TimelineMarkerType = Field(..., description="Type of marker")
    label: Optional[str] = Field(None, description="Optional label text")
    data: Optional[dict] = Field(None, description="Additional data for this marker")


class TimelineData(BaseModel):
    """Complete timeline data for the frontend."""
    
    duration_ms: int = Field(..., description="Total audio duration")
    markers: List[TimelineMarker] = Field(default_factory=list)
    word_timestamps: List[dict] = Field(
        default_factory=list,
        description="Word-level timestamps for karaoke sync"
    )
    
    def get_markers_by_type(self, marker_type: TimelineMarkerType) -> List[TimelineMarker]:
        """Filter markers by type."""
        return [m for m in self.markers if m.type == marker_type]

