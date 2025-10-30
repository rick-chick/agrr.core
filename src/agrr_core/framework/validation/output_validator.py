"""
Output validation for agrr.core predictions.
Strict interface validation to prevent backward compatibility issues.
"""

from typing import Dict, List, Any
from agrr_core.entity.entities.prediction_forecast_entity import Forecast

class OutputValidationError(Exception):
    """Raised when output format violates interface specification."""
    pass

class OutputValidator:
    """Validates prediction output against strict interface specification."""
    
    @staticmethod
    def validate_lightgbm_output(output_data: Dict[str, Any]) -> None:
        """
        Validate LightGBM output format.
        
        Args:
            output_data: Output dictionary to validate
            
        Raises:
            OutputValidationError: If format is invalid
        """
        # Check required top-level fields
        required_fields = ['predictions', 'model_type', 'prediction_days', 'metrics']
        for field in required_fields:
            if field not in output_data:
                raise OutputValidationError(f"Missing required field: {field}")
        
        # Check model_type
        if output_data['model_type'] != 'LightGBM':
            raise OutputValidationError(f"Invalid model_type: {output_data['model_type']}")
        
        # Check metrics
        expected_metrics = ['temperature', 'temperature_max', 'temperature_min']
        if set(output_data['metrics']) != set(expected_metrics):
            raise OutputValidationError(f"Invalid metrics: {output_data['metrics']}")
        
        # Validate each prediction
        predictions = output_data['predictions']
        if not isinstance(predictions, list):
            raise OutputValidationError("predictions must be a list")
        
        for i, prediction in enumerate(predictions):
            OutputValidator._validate_lightgbm_prediction(prediction, i)
    
    @staticmethod
    def validate_arima_output(output_data: Dict[str, Any]) -> None:
        """
        Validate ARIMA output format.
        
        Args:
            output_data: Output dictionary to validate
            
        Raises:
            OutputValidationError: If format is invalid
        """
        # Check required top-level fields
        required_fields = ['predictions', 'model_type', 'prediction_days']
        for field in required_fields:
            if field not in output_data:
                raise OutputValidationError(f"Missing required field: {field}")
        
        # Check model_type
        if output_data['model_type'] != 'ARIMA':
            raise OutputValidationError(f"Invalid model_type: {output_data['model_type']}")
        
        # Check that metrics field is NOT present (ARIMA is single-metric)
        if 'metrics' in output_data:
            raise OutputValidationError("ARIMA output must not contain 'metrics' field")
        
        # Validate each prediction
        predictions = output_data['predictions']
        if not isinstance(predictions, list):
            raise OutputValidationError("predictions must be a list")
        
        for i, prediction in enumerate(predictions):
            OutputValidator._validate_arima_prediction(prediction, i)
    
    @staticmethod
    def _validate_lightgbm_prediction(prediction: Dict[str, Any], index: int) -> None:
        """Validate single LightGBM prediction."""
        # Required fields for LightGBM
        required_fields = [
            'date', 'temperature', 'temperature_max', 'temperature_min',
            'temperature_confidence_lower', 'temperature_confidence_upper',
            'temperature_max_confidence_lower', 'temperature_max_confidence_upper',
            'temperature_min_confidence_lower', 'temperature_min_confidence_upper'
        ]
        
        for field in required_fields:
            if field not in prediction:
                raise OutputValidationError(f"Missing field '{field}' in prediction[{index}]")
        
        # FORBIDDEN: predicted_value must not exist in LightGBM output
        if 'predicted_value' in prediction:
            raise OutputValidationError(
                f"FORBIDDEN: 'predicted_value' field found in LightGBM prediction[{index}]. "
                "LightGBM must use specific temperature fields only."
            )
        
        # FORBIDDEN: confidence_lower/upper must not exist in LightGBM output
        forbidden_fields = ['confidence_lower', 'confidence_upper']
        for field in forbidden_fields:
            if field in prediction:
                raise OutputValidationError(
                    f"FORBIDDEN: '{field}' field found in LightGBM prediction[{index}]. "
                    "LightGBM must use metric-specific confidence fields only."
                )
        
        # Validate temperature relationships
        temp = prediction['temperature']
        temp_max = prediction['temperature_max']
        temp_min = prediction['temperature_min']
        
        if not (temp_min <= temp <= temp_max):
            raise OutputValidationError(
                f"Invalid temperature relationship in prediction[{index}]: "
                f"temp_min({temp_min}) <= temp({temp}) <= temp_max({temp_max})"
            )
    
    @staticmethod
    def _validate_arima_prediction(prediction: Dict[str, Any], index: int) -> None:
        """Validate single ARIMA prediction."""
        # Required fields for ARIMA
        required_fields = ['date', 'predicted_value', 'confidence_lower', 'confidence_upper']
        
        for field in required_fields:
            if field not in prediction:
                raise OutputValidationError(f"Missing field '{field}' in prediction[{index}]")
        
        # FORBIDDEN: temperature_max/temperature_min must not exist in ARIMA output
        forbidden_fields = ['temperature', 'temperature_max', 'temperature_min']
        for field in forbidden_fields:
            if field in prediction:
                raise OutputValidationError(
                    f"FORBIDDEN: '{field}' field found in ARIMA prediction[{index}]. "
                    "ARIMA must use 'predicted_value' field only."
                )
        
        # FORBIDDEN: metric-specific confidence fields must not exist in ARIMA output
        forbidden_confidence = [
            'temperature_confidence_lower', 'temperature_confidence_upper',
            'temperature_max_confidence_lower', 'temperature_max_confidence_upper',
            'temperature_min_confidence_lower', 'temperature_min_confidence_upper'
        ]
        for field in forbidden_confidence:
            if field in prediction:
                raise OutputValidationError(
                    f"FORBIDDEN: '{field}' field found in ARIMA prediction[{index}]. "
                    "ARIMA must use generic confidence fields only."
                )
    
    @staticmethod
    def validate_input_metrics(metrics: List[str], model_type: str) -> None:
        """
        Validate input metrics against model type.
        
        Args:
            metrics: List of metrics to predict
            model_type: Model type ('lightgbm' or 'arima')
            
        Raises:
            OutputValidationError: If metrics are invalid for model type
        """
        if model_type.lower() == 'lightgbm':
            # LightGBM must predict all 3 temperature metrics
            expected_metrics = ['temperature', 'temperature_max', 'temperature_min']
            if set(metrics) != set(expected_metrics):
                raise OutputValidationError(
                    f"LightGBM must predict exactly: {expected_metrics}, got: {metrics}"
                )
        elif model_type.lower() == 'arima':
            # ARIMA can only predict single metric
            if len(metrics) != 1:
                raise OutputValidationError(f"ARIMA can only predict 1 metric, got {len(metrics)}: {metrics}")
            if metrics[0] not in ['temperature', 'precipitation', 'sunshine']:
                raise OutputValidationError(f"ARIMA cannot predict {metrics[0]}, only: temperature, precipitation, sunshine")
        elif model_type.lower() == 'mock':
            # Mock model supports all temperature metrics
            valid_metrics = ['temperature', 'temperature_max', 'temperature_min']
            for metric in metrics:
                if metric not in valid_metrics:
                    raise OutputValidationError(f"Mock model cannot predict {metric}, only: {valid_metrics}")
        else:
            raise OutputValidationError(f"Unknown model type: {model_type}")
