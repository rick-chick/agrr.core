"""Model evaluation interactor."""

from datetime import datetime

from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.gateways.weather_data_gateway import WeatherDataGateway
from agrr_core.usecase.gateways.weather_data_repository_gateway import WeatherDataRepositoryGateway
from agrr_core.usecase.gateways.prediction_service_gateway import PredictionServiceGateway
from agrr_core.usecase.ports.input.model_evaluation_input_port import ModelEvaluationInputPort
from agrr_core.usecase.dto.model_evaluation_request_dto import ModelEvaluationRequestDTO
from agrr_core.usecase.dto.model_accuracy_dto import ModelAccuracyDTO


class ModelEvaluationInteractor(ModelEvaluationInputPort):
    """Interactor for model evaluation."""
    
    def __init__(
        self, 
        weather_data_gateway: WeatherDataGateway,
        weather_data_repository_gateway: WeatherDataRepositoryGateway,
        prediction_service_gateway: PredictionServiceGateway
    ):
        self.weather_data_gateway = weather_data_gateway
        self.weather_data_repository_gateway = weather_data_repository_gateway
        self.prediction_service_gateway = prediction_service_gateway
    
    async def execute(self, request: ModelEvaluationRequestDTO) -> ModelAccuracyDTO:
        """Execute model evaluation."""
        try:
            # Get test data
            test_data, _ = await self.weather_data_gateway.get_weather_data_by_location_and_date_range(
                0.0, 0.0,  # Dummy location - should be passed in request
                request.test_data_start_date,
                request.test_data_end_date
            )
            
            # Get training data (before test period)
            training_data, _ = await self.weather_data_gateway.get_weather_data_by_location_and_date_range(
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
                forecasts_dict = await self.prediction_service_gateway.predict_multiple_metrics(
                    training_data, [metric], model_config
                )
                
                if metric in forecasts_dict:
                    # Evaluate accuracy
                    accuracy = await self.prediction_service_gateway.evaluate_model_accuracy(
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
            
            await self.weather_data_repository_gateway.save_model_evaluation(
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
