"""Tests for fertilizer entity."""

import pytest

from agrr_core.entity.entities.fertilizer_entity import (
    FertilizerListRequest,
    FertilizerListResult,
    FertilizerDetailRequest,
    FertilizerDetail,
)

class TestFertilizerListRequest:
    """Tests for FertilizerListRequest."""
    
    def test_create_with_default_limit(self):
        """Test creating FertilizerListRequest with default limit."""
        request = FertilizerListRequest(language="ja")
        
        assert request.language == "ja"
        assert request.limit == 5
    
    def test_create_with_custom_limit(self):
        """Test creating FertilizerListRequest with custom limit."""
        request = FertilizerListRequest(language="en", limit=10)
        
        assert request.language == "en"
        assert request.limit == 10

class TestFertilizerListResult:
    """Tests for FertilizerListResult."""
    
    def test_create_with_empty_list(self):
        """Test creating FertilizerListResult with empty list."""
        result = FertilizerListResult(fertilizers=[])
        
        assert result.fertilizers == []
    
    def test_create_with_fertilizers(self):
        """Test creating FertilizerListResult with fertilizers."""
        fertilizers = ["尿素", "硝酸アンモニウム", "過リン酸石灰"]
        result = FertilizerListResult(fertilizers=fertilizers)
        
        assert result.fertilizers == fertilizers

class TestFertilizerDetailRequest:
    """Tests for FertilizerDetailRequest."""
    
    def test_create(self):
        """Test creating FertilizerDetailRequest."""
        request = FertilizerDetailRequest(fertilizer_name="尿素")
        
        assert request.fertilizer_name == "尿素"

class TestFertilizerDetail:
    """Tests for FertilizerDetail."""
    
    def test_create_minimal(self):
        """Test creating FertilizerDetail with minimal fields."""
        detail = FertilizerDetail(name="尿素", npk="0-0-0")
        
        assert detail.name == "尿素"
        assert detail.npk == "0-0-0"
        assert detail.additional_info is None
        assert detail.description == ""
        assert detail.link is None
    
    def test_create_full(self):
        """Test creating FertilizerDetail with all fields."""
        detail = FertilizerDetail(
            name="尿素",
            npk="46-0-0",
            additional_info="窒素肥料",
            description="高窒素含有量の肥料",
            link="https://example.com/urea"
        )
        
        assert detail.name == "尿素"
        assert detail.npk == "46-0-0"
        assert detail.additional_info == "窒素肥料"
        assert detail.description == "高窒素含有量の肥料"
        assert detail.link == "https://example.com/urea"

