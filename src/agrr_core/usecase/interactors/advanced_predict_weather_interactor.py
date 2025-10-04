"""Advanced weather prediction interactor with multiple models and metrics support."""

from typing import Dict, Any, List
from datetime import datetime

from agrr_core.entity import Location, DateRange
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.ports.input.weather_data_input_port import WeatherDataInputPort
from agrr_core.usecase.ports.input.advanced_prediction_input_port import AdvancedPredictionInputPort
from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort
from agrr_core.usecase.dto.prediction_config_dto import (
    MultiMetricPredictionRequestDTO, 
    ModelEvaluationRequestDTO,
    BatchPredictionRequestDTO
)
from agrr_core.usecase.dto.advanced_prediction_response_dto import (
    AdvancedPredictionResponseDTO,
    ModelAccuracyDTO,
    ModelPerformanceDTO,
    BatchPredictionResponseDTO
)
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.forecast_response_dto import ForecastResponseDTO


class AdvancedPredictWeatherInteractor:
    """Advanced interactor for weather prediction with multiple models and metrics."""
    
    def __init__(
        self, 
        weather_data_input_port: WeatherDataInputPort,
        advanced_prediction_input_port: AdvancedPredictionInputPort,
        advanced_prediction_output_port: AdvancedPredictionOutputPort,
        prediction_presenter_output_port: PredictionPresenterOutputPort
    ):
        self.weather_data_input_port = weather_data_input_port
        self.advanced_prediction_input_port = advanced_prediction_input_port
        self.advanced_prediction_output_port = advanced_prediction_output_port
        self.prediction_presenter_output_port = prediction_presenter_output_port
    
    async def execute_multi_metric_prediction(self, request: MultiMetricPredictionRequestDTO) -> AdvancedPredictionResponseDTO:
        """Execute multi-metric weather prediction."""
        try:
            # Validate location
            location = Location(request.latitude, request.longitude)
            
            # Validate date range
            date_range = DateRange(request.start_date, request.end_date)
            
            # Get historical weather data
            historical_data_list, actual_location = await self.weather_data_input_port.get_weather_data_by_location_and_date_range(
                location.latitude,
                location.longitude,
                date_range.start_date,
                date_range.end_date
            )
            
            if not historical_data_list:
                raise PredictionError("No historical data available for prediction")
            
            # Prepare model configuration
            model_config = {
                'model_type': request.config.model_type,
                'prediction_days': request.prediction_days,
                'seasonality': request.config.seasonality,
                'trend': request.config.trend,
                'custom_params': request.config.custom_params,
                'confidence_level': request.config.confidence_level,
                'validation_split': request.config.validation_split
            }
            
            # Use advanced prediction service to generate forecasts
            forecasts_dict = await self.advanced_prediction_output_port.predict_multiple_metrics(
                historical_data_list, 
                request.metrics,
                model_config
            )
            
            # Save forecasts with metadata
            metadata = {
                'model_type': request.config.model_type,
                'location': {
                    'latitude': actual_location.latitude,
                    'longitude': actual_location.longitude,
                    'name': getattr(actual_location, 'name', request.location_name)
                },
                'prediction_date': datetime.now().isoformat(),
                'metrics': request.metrics,
                'config': model_config
            }
            
            all_forecasts = []
            for metric, forecasts in forecasts_dict.items():
                all_forecasts.extend(forecasts)
            
            await self.advanced_prediction_input_port.save_forecast_with_metadata(
                all_forecasts, metadata
            )
            
            # Convert historical data to response DTOs
            historical_response = []
            for weather_data in historical_data_list:
                response_dto = WeatherDataResponseDTO(
                    time=weather_data.time.isoformat(),
                    temperature_2m_max=weather_data.temperature_2m_max,
                    temperature_2m_min=weather_data.temperature_2m_min,
                    temperature_2m_mean=weather_data.temperature_2m_mean,
                    precipitation_sum=weather_data.precipitation_sum,
                    sunshine_duration=weather_data.sunshine_duration,
                    sunshine_hours=weather_data.sunshine_hours,
                )
                historical_response.append(response_dto)
            
            # Convert forecasts to response DTOs
            forecasts_response = {}
            for metric, forecasts in forecasts_dict.items():
                forecast_list = []
                for forecast in forecasts:
                    forecast_dto = ForecastResponseDTO(
                        date=forecast.date.isoformat(),
                        predicted_value=forecast.predicted_value,
                        confidence_lower=forecast.confidence_lower,
                        confidence_upper=forecast.confidence_upper
                    )
                    forecast_list.append(forecast_dto)
                forecasts_response[metric] = forecast_list
            
            # Prepare model metrics
            model_metrics = {
                'training_data_points': len(historical_data_list),
                'prediction_days': request.prediction_days,
                'model_type': request.config.model_type,
                'metrics_predicted': request.metrics,
                'location': metadata['location']
            }
            
            response_dto = AdvancedPredictionResponseDTO(
                historical_data=historical_response,
                forecasts=forecasts_response,
                model_metrics=model_metrics,
                prediction_metadata=metadata
            )
            
            return response_dto
            
        except (ValueError, InvalidLocationError, InvalidDateRangeError) as e:
            raise PredictionError(f"Invalid request parameters: {e}")
        except Exception as e:
            raise PredictionError(f"Prediction failed: {e}")
    
    async def execute_model_evaluation(self, request: ModelEvaluationRequestDTO) -> ModelAccuracyDTO:
        """Execute model evaluation."""
        try:
            # Get test data
            test_data, _ = await self.weather_data_input_port.get_weather_data_by_location_and_date_range(
                0.0, 0.0,  # Dummy location - should be passed in request
                request.test_data_start_date,
                request.test_data_end_date
            )
            
            # Get training data (before test period)
            training_data, _ = await self.weather_data_input_port.get_weather_data_by_location_and_date_range(
                0.0, 0.0,  # Dummy location - should be passed in request
                "2020-01-01",  # Should be calculated based on test start date
                request.test_data_start_date
            )
            
            # Prepare model configuration
            model_config = {
                'model_type': request.model_type,
                'prediction_days': 30,  # Default
                'seasonality': request.config.seasonality,
                'trend': request.config.trend,
                'custom_params': request.config.custom_params,
                'validation_split': request.validation_split
            }
            
            # Train and predict for each metric
            accuracy_results = {}
            for metric in request.metrics:
                # Make predictions
                forecasts_dict = await self.advanced_prediction_output_port.predict_multiple_metrics(
                    training_data, [metric], model_config
                )
                
                if metric in forecasts_dict:
                    # Evaluate accuracy
                    accuracy = await self.advanced_prediction_output_port.evaluate_model_accuracy(
                        test_data, forecasts_dict[metric], metric
                    )
                    accuracy_results[metric] = accuracy
            
            # Save evaluation results
            evaluation_results = {
                'model_type': request.model_type,
                'test_period': {
                    'start': request.test_data_start_date,
                    'end': request.test_data_end_date
                },
                'accuracy': accuracy_results,
                'evaluation_date': datetime.now().isoformat()
            }
            
            await self.advanced_prediction_input_port.save_model_evaluation(
                request.model_type, evaluation_results
            )
            
            # Return primary metric accuracy (temperature if available)
            primary_metric = 'temperature' if 'temperature' in accuracy_results else list(accuracy_results.keys())[0]
            accuracy = accuracy_results[primary_metric]
            
            return ModelAccuracyDTO(
                model_type=request.model_type,
                metric=primary_metric,
                mae=accuracy['mae'],
                mse=accuracy['mse'],
                rmse=accuracy['rmse'],
                mape=accuracy['mape'],
                r2_score=accuracy.get('r2_score', 0.0),
                evaluation_date=datetime.now().isoformat(),
                test_data_points=len(test_data)
            )
            
        except Exception as e:
            raise PredictionError(f"Model evaluation failed: {e}")
    
    async def execute_batch_prediction(self, request: BatchPredictionRequestDTO) -> BatchPredictionResponseDTO:
        """Execute batch prediction for multiple locations."""
        import time
        start_time = time.time()
        
        results = []
        errors = []
        
        for location_data in request.locations:
            try:
                # Create single location request
                single_request = MultiMetricPredictionRequestDTO(
                    latitude=location_data['lat'],
                    longitude=location_data['lon'],
                    start_date=request.start_date,
                    end_date=request.end_date,
                    prediction_days=request.prediction_days,
                    metrics=request.metrics,
                    config=request.config,
                    location_name=location_data.get('name', 'Unknown')
                )
                
                # Execute prediction
                result = await self.execute_multi_metric_prediction(single_request)
                results.append({
                    'location': location_data,
                    'prediction': result,
                    'status': 'success'
                })
                
            except Exception as e:
                errors.append({
                    'location': location_data,
                    'error': str(e),
                    'status': 'failed'
                })
        
        processing_time = time.time() - start_time
        
        # Create summary
        summary = {
            'total_locations': len(request.locations),
            'successful_predictions': len(results),
            'failed_predictions': len(errors),
            'processing_time_seconds': processing_time,
            'model_type': request.config.model_type,
            'metrics': request.metrics
        }
        
        return BatchPredictionResponseDTO(
            results=results,
            summary=summary,
            errors=errors,
            processing_time=processing_time
        )
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available prediction models."""
        return await self.advanced_prediction_output_port.get_available_models()
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        return await self.advanced_prediction_output_port.get_model_info(model_type)
    
    async def compare_models(
        self,
        historical_data: List,
        test_data: List,
        metrics: List[str],
        model_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare performance of different models."""
        if hasattr(self.advanced_prediction_output_port, 'compare_models'):
            return await self.advanced_prediction_output_port.compare_models(
                historical_data, test_data, metrics, model_configs
            )
        else:
            raise PredictionError("Model comparison not supported by current prediction service")
