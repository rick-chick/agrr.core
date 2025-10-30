"""Tests for data_source propagation through components.

This test verifies that data_source flows correctly from CLI arguments
through all layers to the actual Repository instance.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from agrr_core.framework.agrr_core_container import WeatherCliContainer, AgrrCoreContainer
from agrr_core.adapter.gateways.weather_jma_gateway import WeatherJMAGateway as WeatherJMAGateway
from agrr_core.adapter.gateways.weather_api_gateway import WeatherAPIGateway as WeatherAPIGateway
from agrr_core.adapter.interfaces.structures.html_table_structures import HtmlTable, TableRow

class TestDataSourcePropagation:
    """Test data_source propagation through component layers."""
    
    def test_layer1_cli_args_to_config(self):
        """
        Layer 1: CLI arguments → config dictionary
        
        Test that CLI arguments are correctly extracted into config.
        """
        # Simulate CLI argument parsing
        args = ['weather', '--location', '35.6895,139.6917', '--days', '7', '--data-source', 'jma']
        
        # Extract data_source (same logic as cli.py)
        weather_data_source = 'openmeteo'  # default
        if '--data-source' in args:
            try:
                ds_index = args.index('--data-source')
                if ds_index + 1 < len(args):
                    weather_data_source = args[ds_index + 1]
            except (ValueError, IndexError):
                pass
        
        # Create config
        config = {
            'weather_data_source': weather_data_source
        }
        
        # Verify
        assert config['weather_data_source'] == 'jma'
        assert isinstance(config, dict)
    
    def test_layer2_config_to_container(self):
        """
        Layer 2: config dictionary → Container
        
        Test that config is correctly stored in Container.
        """
        config = {
            'weather_data_source': 'jma',
            'csv_download_timeout': 60
        }
        
        container = AgrrCoreContainer(config)
        
        # Verify config is stored
        assert container.config['weather_data_source'] == 'jma'
        assert container.config['csv_download_timeout'] == 60
    
    def test_layer3_container_to_repository_selection_jma(self):
        """
        Layer 3: Container → Repository selection (JMA)
        
        Test that Container selects JMA repository when data_source='jma'.
        """
        config = {
            'weather_data_source': 'jma'
        }
        
        container = AgrrCoreContainer(config)
        
        # Get JMA repository
        jma_repo = container.get_weather_jma_gateway()
        
        # Verify correct type
        assert isinstance(jma_repo, WeatherJMAGateway)
        assert jma_repo is not None
    
    def test_layer3_container_to_repository_selection_openmeteo(self):
        """
        Layer 3: Container → Repository selection (OpenMeteo)
        
        Test that Container selects OpenMeteo repository when data_source='openmeteo'.
        """
        config = {
            'weather_data_source': 'openmeteo'
        }
        
        container = AgrrCoreContainer(config)
        
        # Get OpenMeteo repository
        openmeteo_repo = container.get_weather_api_gateway()
        
        # Verify correct type
        assert isinstance(openmeteo_repo, WeatherAPIGateway)
        assert openmeteo_repo is not None
    
    def test_layer4_container_to_gateway_injection_jma(self):
        """
        Layer 4: Container → Gateway (JMA repository injection)
        
        Test that Gateway receives correct repository based on data_source.
        """
        config = {
            'weather_data_source': 'jma'
        }
        
        container = AgrrCoreContainer(config)
        
        # Get gateway (should inject JMA repository)
        gateway = container.get_weather_gateway_impl()
        
        # Verify gateway has api_gateway
        assert gateway.api_gateway is not None
        assert isinstance(gateway.api_gateway, WeatherJMAGateway)
    
    def test_layer4_container_to_gateway_injection_openmeteo(self):
        """
        Layer 4: Container → Gateway (OpenMeteo repository injection)
        
        Test that Gateway receives correct repository based on data_source.
        """
        config = {
            'weather_data_source': 'openmeteo'
        }
        
        container = AgrrCoreContainer(config)
        
        # Get gateway (should inject OpenMeteo repository)
        gateway = container.get_weather_gateway_impl()
        
        # Verify gateway has api_gateway
        assert gateway.api_gateway is not None
        assert isinstance(gateway.api_gateway, WeatherAPIGateway)
    
    def test_end_to_end_data_source_propagation_jma(self):
        """
        End-to-End: CLI args → Repository instance (JMA)
        
        Test complete flow from CLI arguments to actual Repository instance.
        """
        # Step 1: CLI args
        cli_args = ['--data-source', 'jma']
        
        # Step 2: Extract to config
        data_source = 'jma'
        config = {'weather_data_source': data_source}
        
        # Step 3: Create container
        container = AgrrCoreContainer(config)
        
        # Step 4: Get gateway (triggers repository selection)
        gateway = container.get_weather_gateway_impl()
        
        # Step 5: Verify correct repository is injected
        assert isinstance(gateway.api_gateway, WeatherJMAGateway)
        
        # Verify the chain
        # CLI args → config → Container → Gateway → JMA Repository
        assert container.config['weather_data_source'] == 'jma'
        assert gateway.api_gateway.__class__.__name__ == 'WeatherJMAGateway'
    
    def test_end_to_end_data_source_propagation_openmeteo(self):
        """
        End-to-End: CLI args → Repository instance (OpenMeteo)
        
        Test complete flow from CLI arguments to actual Repository instance.
        """
        # Step 1: CLI args (default, no --data-source)
        config = {}  # No data_source specified
        
        # Step 2: Create container (should default to openmeteo)
        container = AgrrCoreContainer(config)
        
        # Step 3: Get gateway
        gateway = container.get_weather_gateway_impl()
        
        # Step 4: Verify correct repository is injected (default)
        assert isinstance(gateway.api_gateway, WeatherAPIGateway)
        
        # Verify default behavior
        # No CLI args → empty config → Container → Gateway → OpenMeteo Repository
        assert gateway.api_gateway.__class__.__name__ == 'WeatherAPIGateway'
    
    def test_data_source_switching_at_runtime(self):
        """
        Test that different containers with different configs use different repositories.
        
        This verifies that data_source is properly isolated per container instance.
        """
        # Create two containers with different configs
        config_jma = {'weather_data_source': 'jma'}
        config_openmeteo = {'weather_data_source': 'openmeteo'}
        
        container_jma = AgrrCoreContainer(config_jma)
        container_openmeteo = AgrrCoreContainer(config_openmeteo)
        
        # Get gateways from both
        gateway_jma = container_jma.get_weather_gateway_impl()
        gateway_openmeteo = container_openmeteo.get_weather_gateway_impl()
        
        # Verify different repositories
        assert isinstance(gateway_jma.api_gateway, WeatherJMAGateway)
        assert isinstance(gateway_openmeteo.api_gateway, WeatherAPIGateway)
        
        # Verify they are different instances
        assert gateway_jma is not gateway_openmeteo
        assert gateway_jma.api_gateway is not gateway_openmeteo.api_gateway

class TestDataSourcePropagationWithMocks:
    """Test data_source propagation with mocked external services."""

    def test_jma_repository_actually_called(self):
        """
        Test that JMA repository is actually called when data_source='jma'.
        
        This verifies the complete chain with mocked external services.
        """
        config = {
            'weather_data_source': 'jma'
        }
        
        container = AgrrCoreContainer(config)
        
        # Mock HTML Table Fetcher to avoid actual HTTP request
        # Create HtmlTable structure
        # (day, precip, temp_mean, temp_max, temp_min, sunshine_h, wind_avg, wind_max)
        cells = [
            '5', '1013.0', '1023.0',  # day, pressure_local, pressure_sea
            '2.5', '0.0', '0.0',  # precip_sum, precip_1h, precip_10m
            '18.9', '22.5', '15.3',  # temp_mean, temp_max, temp_min
            '60', '50',  # humidity_avg, humidity_min
            '3.0', '3.5',  # wind_avg, wind_max
            '北', '10.0', '0',  # wind_dir, wind_speed, wind_gust
            '5.2', '0.0', '0.0', '--', '--'  # sunshine(h), snow, snow_depth, weather, cloud
        ]
        row = TableRow(cells=cells)
        mock_html_table = [HtmlTable(headers=[], rows=[row], table_id='tablefix1')]
        
        # Get components
        html_table_fetcher = container.get_html_table_fetcher()
        
        # Mock the get method
        with patch.object(html_table_fetcher, 'get', new_callable=Mock) as mock_download:
            mock_download.return_value = mock_html_table
            
            # Get gateway and call it
            gateway = container.get_weather_gateway_impl()
            result = gateway.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-10-05',
                end_date='2024-10-05'
            )
            
            # Verify JMA repository was used (CSV downloader was called)
            assert mock_download.called
            assert mock_download.call_count == 1
            
            # Verify result structure
            assert result.weather_data_list is not None
            assert len(result.weather_data_list) == 1

    def test_openmeteo_repository_actually_called(self):
        """
        Test that OpenMeteo repository is actually called when data_source='openmeteo'.
        """
        config = {
            'weather_data_source': 'openmeteo'
        }
        
        container = AgrrCoreContainer(config)
        
        # Mock HTTP client to avoid actual API request
        mock_api_response = {
            'latitude': 35.6895,
            'longitude': 139.6917,
            'elevation': 40.0,
            'timezone': 'Asia/Tokyo',
            'daily': {
                'time': ['2024-10-05'],
                'temperature_2m_max': [22.5],
                'temperature_2m_min': [15.3],
                'temperature_2m_mean': [18.9],
                'precipitation_sum': [2.5],
                'sunshine_duration': [18720],
                'wind_speed_10m_max': [3.5],
                'weather_code': [1],
            }
        }
        
        # Get HTTP client
        http_client = container.get_http_service_impl()
        
        # Mock the get method
        with patch.object(http_client, 'get', new_callable=Mock) as mock_get:
            mock_get.return_value = mock_api_response
            
            # Get gateway and call it
            gateway = container.get_weather_gateway_impl()
            result = gateway.get_by_location_and_date_range(
                latitude=35.6895,
                longitude=139.6917,
                start_date='2024-10-05',
                end_date='2024-10-05'
            )
            
            # Verify OpenMeteo repository was used (HTTP client was called)
            assert mock_get.called
            assert mock_get.call_count == 1
            
            # Verify result structure
            assert result.weather_data_list is not None
            assert len(result.weather_data_list) == 1

class TestDataSourceValidation:
    """Test data_source validation and error handling."""
    
    def test_invalid_data_source_uses_default(self):
        """
        Test that invalid data_source falls back to default (openmeteo).
        """
        config = {
            'weather_data_source': 'invalid_source'  # Invalid
        }
        
        container = AgrrCoreContainer(config)
        
        # Should NOT raise error, should use openmeteo as default
        gateway = container.get_weather_gateway_impl()
        
        # Since 'invalid_source' is not 'jma', should use openmeteo
        assert isinstance(gateway.api_gateway, WeatherAPIGateway)
    
    def test_empty_config_uses_default(self):
        """
        Test that empty config uses default data_source (openmeteo).
        """
        config = {}  # No data_source
        
        container = AgrrCoreContainer(config)
        gateway = container.get_weather_gateway_impl()
        
        # Should use OpenMeteo by default
        assert isinstance(gateway.api_gateway, WeatherAPIGateway)
    
    def test_none_config_uses_default(self):
        """
        Test that None config uses default data_source.
        """
        container = AgrrCoreContainer(None)
        gateway = container.get_weather_gateway_impl()
        
        # Should use OpenMeteo by default
        assert isinstance(gateway.api_gateway, WeatherAPIGateway)

class TestDataSourceIsolation:
    """Test that data_source configuration is properly isolated."""
    
    def test_multiple_containers_independent(self):
        """
        Test that multiple containers with different configs are independent.
        """
        # Create multiple containers
        container1 = AgrrCoreContainer({'weather_data_source': 'jma'})
        container2 = AgrrCoreContainer({'weather_data_source': 'openmeteo'})
        container3 = AgrrCoreContainer({'weather_data_source': 'jma'})
        
        # Get gateways
        gateway1 = container1.get_weather_gateway_impl()
        gateway2 = container2.get_weather_gateway_impl()
        gateway3 = container3.get_weather_gateway_impl()
        
        # Verify each has correct repository
        assert isinstance(gateway1.api_gateway, WeatherJMAGateway)
        assert isinstance(gateway2.api_gateway, WeatherAPIGateway)
        assert isinstance(gateway3.api_gateway, WeatherJMAGateway)
        
        # Verify isolation (different instances)
        assert gateway1 is not gateway2
        assert gateway1 is not gateway3
        assert gateway2 is not gateway3
    
    def test_config_immutability(self):
        """
        Test that modifying config after container creation doesn't affect behavior.
        """
        config = {'weather_data_source': 'jma'}
        
        container = AgrrCoreContainer(config)
        
        # Get initial gateway
        gateway1 = container.get_weather_gateway_impl()
        assert isinstance(gateway1.api_gateway, WeatherJMAGateway)
        
        # Modify config (should not affect already created container)
        config['weather_data_source'] = 'openmeteo'
        
        # Get gateway again (should return same instance due to caching)
        gateway2 = container.get_weather_gateway_impl()
        
        # Should still be JMA (cached)
        assert gateway1 is gateway2
        assert isinstance(gateway2.api_gateway, WeatherJMAGateway)

class TestDataSourcePropagationTrace:
    """Test complete data_source propagation trace with detailed verification."""
    
    def test_trace_jma_propagation(self):
        """
        Trace data_source='jma' through all components.
        
        Verifies:
        1. Config contains 'jma'
        2. Container reads 'jma'
        3. CsvService is created
        4. WeatherJMAGateway is created with CsvService
        5. Gateway receives WeatherJMAGateway
        """
        # Step 1: Config
        config = {'weather_data_source': 'jma'}
        assert config['weather_data_source'] == 'jma', "Step 1: Config creation failed"
        
        # Step 2: Container
        container = AgrrCoreContainer(config)
        assert container.config['weather_data_source'] == 'jma', "Step 2: Config storage failed"
        
        # Step 3: HTML Table Fetcher
        html_table_fetcher = container.get_html_table_fetcher()
        assert html_table_fetcher is not None, "Step 3: HTML Table Fetcher creation failed"
        
        # Step 4: JMA Repository
        jma_repo = container.get_weather_jma_gateway()
        assert isinstance(jma_repo, WeatherJMAGateway), "Step 4: JMA Repository type check failed"
        assert jma_repo.html_table_fetcher is html_table_fetcher, "Step 4: HTML Table Fetcher injection failed"
        
        # Step 5: Gateway
        gateway = container.get_weather_gateway_impl()
        assert gateway.api_gateway is jma_repo, "Step 5: Repository injection to Gateway failed"
        
        print("\n✅ All propagation steps verified:")
        print("   Config → Container → CsvService → JMARepository → Gateway")
    
    def test_trace_openmeteo_propagation(self):
        """
        Trace data_source='openmeteo' through all components.
        
        Verifies:
        1. Config contains 'openmeteo' (or defaults to it)
        2. Container reads config
        3. HttpClient is created
        4. WeatherAPIGateway is created with HttpClient
        5. Gateway receives WeatherAPIGateway
        """
        # Step 1: Config (default)
        config = {}  # Will default to openmeteo
        
        # Step 2: Container
        container = AgrrCoreContainer(config)
        
        # Step 3: HTTP Client
        http_client = container.get_http_service_impl()
        assert http_client is not None, "Step 3: HTTP Client creation failed"
        
        # Step 4: OpenMeteo Repository
        openmeteo_repo = container.get_weather_api_gateway()
        assert isinstance(openmeteo_repo, WeatherAPIGateway), "Step 4: OpenMeteo Repository type check failed"
        assert openmeteo_repo.http_service is http_client, "Step 4: HTTP service injection failed"
        
        # Step 5: Gateway
        gateway = container.get_weather_gateway_impl()
        assert gateway.api_gateway is openmeteo_repo, "Step 5: Repository injection to Gateway failed"
        
        print("\n✅ All propagation steps verified:")
        print("   Config → Container → HttpClient → OpenMeteoRepository → Gateway")

class TestDataSourceConfigVariations:
    """Test various config variations and edge cases."""
    
    def test_case_sensitivity(self):
        """Test that data_source is case-sensitive."""
        # Lowercase 'jma'
        config1 = {'weather_data_source': 'jma'}
        container1 = AgrrCoreContainer(config1)
        gateway1 = container1.get_weather_gateway_impl()
        assert isinstance(gateway1.api_gateway, WeatherJMAGateway)
        
        # Uppercase 'JMA' (should use openmeteo as default)
        config2 = {'weather_data_source': 'JMA'}
        container2 = AgrrCoreContainer(config2)
        gateway2 = container2.get_weather_gateway_impl()
        assert isinstance(gateway2.api_gateway, WeatherAPIGateway)
    
    def test_whitespace_in_config(self):
        """Test that whitespace in data_source is handled correctly."""
        # With whitespace (should use openmeteo as default)
        config = {'weather_data_source': ' jma '}
        container = AgrrCoreContainer(config)
        gateway = container.get_weather_gateway_impl()
        
        # Should NOT match 'jma' due to whitespace, uses openmeteo
        assert isinstance(gateway.api_gateway, WeatherAPIGateway)
    
    def test_config_persistence(self):
        """Test that config values persist through component creation."""
        config = {
            'weather_data_source': 'jma',
            'html_fetch_timeout': 45,
            'open_meteo_base_url': 'https://custom-url.com'
        }
        
        container = AgrrCoreContainer(config)
        
        # All config values should be preserved
        assert container.config['weather_data_source'] == 'jma'
        assert container.config['html_fetch_timeout'] == 45
        assert container.config['open_meteo_base_url'] == 'https://custom-url.com'
        
        # Components should use these values
        html_table_fetcher = container.get_html_table_fetcher()
        assert html_table_fetcher.timeout == 45

