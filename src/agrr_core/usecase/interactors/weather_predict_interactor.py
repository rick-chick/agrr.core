"""Use case interactor for weather prediction from data."""

from typing import List
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast
from agrr_core.entity.validators.weather_validator import WeatherValidator
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.gateways.prediction_gateway import PredictionGateway
from agrr_core.framework.validation.output_validator import OutputValidator, OutputValidationError


class WeatherPredictInteractor:
    """Use case interactor for weather prediction from data."""
    
    def __init__(
        self,
        weather_gateway: WeatherGateway,
        prediction_gateway: PredictionGateway
    ):
        """Initialize weather prediction from data interactor."""
        self.weather_gateway = weather_gateway
        self.prediction_gateway = prediction_gateway
    
    def execute(
        self,
        input_source: str,
        output_destination: str,
        prediction_days: int,
        predict_all_temperature_metrics: bool = True
    ) -> List[Forecast]:
        """
        Execute weather prediction from data.
        
        Args:
            input_source: Input data source (file path, database connection, etc.)
            output_destination: Output destination (file path, database, etc.)
            prediction_days: Number of days to predict
            predict_all_temperature_metrics: If True, predict temperature, temperature_max, temperature_min
                                            (default: True for avoiding saturation)
            
        Returns:
            List of forecast predictions (temperature)
            
        Raises:
            ValueError: If validation fails
            FileError: If operations fail
        """
        # Validate input data source
        if not WeatherValidator.validate_source_format(input_source):
            raise ValueError("Invalid input data source format")
        
        # Validate output destination
        if not WeatherValidator.validate_destination_format(output_destination):
            raise ValueError("Invalid output destination format")
        
        # Get weather data from input source
        historical_data = self.prediction_gateway.read_historical_data(input_source)
        
        # Validate weather data quality with detailed error information
        is_valid, error_message = WeatherValidator.validate_weather_data_detailed(historical_data)
        if not is_valid:
            raise ValueError(error_message)
        
        # Generate predictions
        # デフォルトで全ての気温メトリックを予測（飽和問題の解決）
        if predict_all_temperature_metrics:
            # 複数メトリック予測（temperature, temperature_max, temperature_min）
            all_predictions = self.prediction_gateway.predict_multiple_metrics(
                historical_data,
                ['temperature', 'temperature_max', 'temperature_min'],
                {'prediction_days': prediction_days}
            )
            
            # モックモードの場合は、PredictionMockGatewayのcreateメソッドを使用
            if hasattr(self.prediction_gateway, 'mock_data_file') or type(self.prediction_gateway).__name__ == 'PredictionMockGateway':
                # モックモード: 複数メトリックの予測結果を統合して保存
                self._create_multi_metric_predictions_mock(all_predictions, output_destination)
            else:
                # 通常モード: 複数メトリックの予測結果を統合して保存
                self._create_multi_metric_predictions(all_predictions, output_destination)
            
            # temperatureの予測結果を返す（後方互換性）
            predictions = all_predictions['temperature']
        else:
            # 単一メトリック予測（従来の動作）
            predictions = self.prediction_gateway.predict(
                historical_data, 
                'temperature', 
                {'prediction_days': prediction_days}
            )
            
            # Create predictions
            self.prediction_gateway.create(predictions, output_destination)
        
        return predictions
    
    def _create_multi_metric_predictions(
        self,
        all_predictions: dict,
        destination: str
    ) -> None:
        """Create multi-metric predictions file.
        
        Args:
            all_predictions: Dictionary of predictions for each metric
            destination: Output file path
        """
        import json
        from pathlib import Path
        
        # 複数メトリックの予測を統合したJSONを作成
        predictions_data = []
        prediction_count = len(all_predictions['temperature'])
        
        for i in range(prediction_count):
            temp_pred = all_predictions['temperature'][i]
            temp_max_pred = all_predictions['temperature_max'][i]
            temp_min_pred = all_predictions['temperature_min'][i]
            
            prediction_dict = {
                'date': temp_pred.date.isoformat(),
                'temperature': temp_pred.predicted_value,
                'temperature_max': temp_max_pred.predicted_value,
                'temperature_min': temp_min_pred.predicted_value,
                'temperature_confidence_lower': temp_pred.confidence_lower,
                'temperature_confidence_upper': temp_pred.confidence_upper,
                'temperature_max_confidence_lower': temp_max_pred.confidence_lower,
                'temperature_max_confidence_upper': temp_max_pred.confidence_upper,
                'temperature_min_confidence_lower': temp_min_pred.confidence_lower,
                'temperature_min_confidence_upper': temp_min_pred.confidence_upper,
            }
            predictions_data.append(prediction_dict)
        
        # JSONファイルに書き込み
        output_data = {
            'predictions': predictions_data,
            'model_type': 'LightGBM',
            'prediction_days': prediction_count,
            'metrics': ['temperature', 'temperature_max', 'temperature_min']
        }
        
        # 厳密なIFバリデーション
        try:
            OutputValidator.validate_lightgbm_output(output_data)
        except OutputValidationError as e:
            raise PredictionError(f"Output validation failed: {e}")
        
        Path(destination).write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
    
    def _create_multi_metric_predictions_mock(
        self,
        all_predictions: dict,
        destination: str
    ) -> None:
        """Create multi-metric predictions file for mock mode.
        
        Args:
            all_predictions: Dictionary of predictions for each metric
            destination: Output file path
        """
        import json
        from pathlib import Path
        
        # 複数メトリックの予測を統合したJSONを作成
        predictions_data = []
        prediction_count = len(all_predictions['temperature'])
        
        for i in range(prediction_count):
            temp_pred = all_predictions['temperature'][i]
            temp_max_pred = all_predictions['temperature_max'][i]
            temp_min_pred = all_predictions['temperature_min'][i]
            
            prediction_dict = {
                'date': temp_pred.date.isoformat(),
                'temperature': temp_pred.predicted_value,
                'temperature_max': temp_max_pred.predicted_value,
                'temperature_min': temp_min_pred.predicted_value,
                'temperature_confidence_lower': temp_pred.confidence_lower,
                'temperature_confidence_upper': temp_pred.confidence_upper,
                'temperature_max_confidence_lower': temp_max_pred.confidence_lower,
                'temperature_max_confidence_upper': temp_max_pred.confidence_upper,
                'temperature_min_confidence_lower': temp_min_pred.confidence_lower,
                'temperature_min_confidence_upper': temp_min_pred.confidence_upper,
            }
            predictions_data.append(prediction_dict)
        
        # JSONファイルに書き込み
        output_data = {
            'predictions': predictions_data,
            'model_type': 'Mock',
            'prediction_days': prediction_count,
            'metrics': ['temperature', 'temperature_max', 'temperature_min']
        }
        
        Path(destination).write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
