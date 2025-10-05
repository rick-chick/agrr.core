"""Tests for weather mapper."""

import pytest
import pandas as pd
from datetime import datetime

from agrr_core.adapter.mappers.weather_mapper import WeatherMapper
from agrr_core.entity import WeatherData
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO


class TestWeatherMapper:
    """Test WeatherMapper."""
    
    def test_entity_to_dto(self):
        """Test converting WeatherData entity to DTO."""
        weather_data = WeatherData(
            time=datetime(2023, 1, 1),
            temperature_2m_max=25.0,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
        )
        
        dto = WeatherMapper.entity_to_dto(weather_data)
        
        assert isinstance(dto, WeatherDataResponseDTO)
        assert dto.time == "2023-01-01T00:00:00"
        assert dto.temperature_2m_max == 25.0
        assert dto.temperature_2m_min == 15.0
        assert dto.temperature_2m_mean == 20.0
        assert dto.precipitation_sum == 5.0
        assert dto.sunshine_duration == 28800.0
        assert dto.sunshine_hours == 8.0
    
    def test_entity_to_dto_with_none_values(self):
        """Test converting WeatherData entity with None values to DTO."""
        weather_data = WeatherData(
            time=datetime(2023, 1, 1),
            temperature_2m_max=None,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=None,
            sunshine_duration=None,
        )
        
        dto = WeatherMapper.entity_to_dto(weather_data)
        
        assert dto.time == "2023-01-01T00:00:00"
        assert dto.temperature_2m_max is None
        assert dto.temperature_2m_min == 15.0
        assert dto.temperature_2m_mean == 20.0
        assert dto.precipitation_sum is None
        assert dto.sunshine_duration is None
        assert dto.sunshine_hours is None
    
    def test_entities_to_dtos(self):
        """Test converting list of WeatherData entities to DTOs."""
        weather_data_list = [
            WeatherData(
                time=datetime(2023, 1, 1),
                temperature_2m_mean=20.0,
                sunshine_duration=28800.0,
            ),
            WeatherData(
                time=datetime(2023, 1, 2),
                temperature_2m_mean=21.0,
                sunshine_duration=25200.0,
            ),
        ]
        
        dtos = WeatherMapper.entities_to_dtos(weather_data_list)
        
        assert len(dtos) == 2
        assert isinstance(dtos[0], WeatherDataResponseDTO)
        assert dtos[0].time == "2023-01-01T00:00:00"
        assert dtos[0].temperature_2m_mean == 20.0
        assert dtos[0].sunshine_hours == 8.0
        
        assert isinstance(dtos[1], WeatherDataResponseDTO)
        assert dtos[1].time == "2023-01-02T00:00:00"
        assert dtos[1].temperature_2m_mean == 21.0
        assert dtos[1].sunshine_hours == 7.0
    
    def test_entities_to_dataframe(self):
        """Test converting list of WeatherData entities to DataFrame."""
        weather_data_list = [
            WeatherData(
                time=datetime(2023, 1, 1),
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
                temperature_2m_mean=20.0,
                precipitation_sum=5.0,
                sunshine_duration=28800.0,
            ),
            WeatherData(
                time=datetime(2023, 1, 2),
                temperature_2m_max=26.0,
                temperature_2m_min=16.0,
                temperature_2m_mean=21.0,
                precipitation_sum=3.0,
                sunshine_duration=25200.0,
            ),
        ]
        
        df = WeatherMapper.entities_to_dataframe(weather_data_list)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == [
            'time', 'temperature_2m_max', 'temperature_2m_min', 
            'temperature_2m_mean', 'precipitation_sum', 'sunshine_duration', 'sunshine_hours'
        ]
        
        assert df.iloc[0]['time'] == datetime(2023, 1, 1)
        assert df.iloc[0]['temperature_2m_max'] == 25.0
        assert df.iloc[0]['temperature_2m_mean'] == 20.0
        assert df.iloc[0]['sunshine_hours'] == 8.0
        
        assert df.iloc[1]['time'] == datetime(2023, 1, 2)
        assert df.iloc[1]['temperature_2m_max'] == 26.0
        assert df.iloc[1]['temperature_2m_mean'] == 21.0
        assert df.iloc[1]['sunshine_hours'] == 7.0
    
    def test_entities_to_dataframe_with_none_values(self):
        """Test converting entities with None values to DataFrame."""
        weather_data_list = [
            WeatherData(
                time=datetime(2023, 1, 1),
                temperature_2m_max=None,
                temperature_2m_min=15.0,
                temperature_2m_mean=20.0,
                precipitation_sum=None,
                sunshine_duration=None,
            ),
        ]
        
        df = WeatherMapper.entities_to_dataframe(weather_data_list)
        
        assert len(df) == 1
        assert pd.isna(df.iloc[0]['temperature_2m_max'])
        assert df.iloc[0]['temperature_2m_min'] == 15.0
        assert df.iloc[0]['temperature_2m_mean'] == 20.0
        assert pd.isna(df.iloc[0]['precipitation_sum'])
        assert pd.isna(df.iloc[0]['sunshine_duration'])
    
    def test_dataframe_to_entities(self):
        """Test converting DataFrame to list of WeatherData entities."""
        df = pd.DataFrame({
            'time': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
            'temperature_2m_max': [25.0, 26.0],
            'temperature_2m_min': [15.0, 16.0],
            'temperature_2m_mean': [20.0, 21.0],
            'precipitation_sum': [5.0, 3.0],
            'sunshine_duration': [28800.0, 25200.0],
        })
        
        entities = WeatherMapper.dataframe_to_entities(df)
        
        assert len(entities) == 2
        assert isinstance(entities[0], WeatherData)
        
        assert entities[0].time == datetime(2023, 1, 1)
        assert entities[0].temperature_2m_max == 25.0
        assert entities[0].temperature_2m_min == 15.0
        assert entities[0].temperature_2m_mean == 20.0
        assert entities[0].precipitation_sum == 5.0
        assert entities[0].sunshine_duration == 28800.0
        assert entities[0].sunshine_hours == 8.0
        
        assert entities[1].time == datetime(2023, 1, 2)
        assert entities[1].temperature_2m_max == 26.0
        assert entities[1].temperature_2m_mean == 21.0
        assert entities[1].sunshine_hours == 7.0
    
    def test_dataframe_to_entities_with_missing_columns(self):
        """Test converting DataFrame with missing columns to entities."""
        df = pd.DataFrame({
            'time': [datetime(2023, 1, 1)],
            'temperature_2m_mean': [20.0],
            # Missing other columns
        })
        
        entities = WeatherMapper.dataframe_to_entities(df)
        
        assert len(entities) == 1
        assert entities[0].time == datetime(2023, 1, 1)
        assert entities[0].temperature_2m_mean == 20.0
        assert entities[0].temperature_2m_max is None
        assert entities[0].temperature_2m_min is None
        assert entities[0].precipitation_sum is None
        assert entities[0].sunshine_duration is None
    
    def test_empty_dataframe_to_entities(self):
        """Test converting empty DataFrame to entities."""
        df = pd.DataFrame({
            'time': [],
            'temperature_2m_max': [],
            'temperature_2m_min': [],
            'temperature_2m_mean': [],
            'precipitation_sum': [],
            'sunshine_duration': [],
        })
        
        entities = WeatherMapper.dataframe_to_entities(df)
        
        assert len(entities) == 0
    
    def test_empty_entities_to_dataframe(self):
        """Test converting empty entities list to DataFrame."""
        weather_data_list = []
        
        df = WeatherMapper.entities_to_dataframe(weather_data_list)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert list(df.columns) == [
            'time', 'temperature_2m_max', 'temperature_2m_min', 
            'temperature_2m_mean', 'precipitation_sum', 'sunshine_duration', 'sunshine_hours'
        ]
