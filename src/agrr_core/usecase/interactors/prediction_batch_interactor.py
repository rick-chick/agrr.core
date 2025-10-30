"""Batch prediction interactor."""

import time

from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.ports.input.batch_prediction_input_port import BatchPredictionInputPort
from agrr_core.usecase.ports.input.multi_metric_prediction_input_port import MultiMetricPredictionInputPort
from agrr_core.usecase.dto.batch_prediction_request_dto import BatchPredictionRequestDTO
from agrr_core.usecase.dto.batch_prediction_response_dto import BatchPredictionResponseDTO
from agrr_core.usecase.dto.multi_metric_prediction_request_dto import MultiMetricPredictionRequestDTO

class BatchPredictionInteractor(BatchPredictionInputPort):
    """Interactor for batch prediction for multiple locations."""
    
    def __init__(
        self, 
        multi_metric_prediction_interactor: MultiMetricPredictionInputPort
    ):
        self.multi_metric_prediction_interactor = multi_metric_prediction_interactor
    
    def execute(self, request: BatchPredictionRequestDTO) -> BatchPredictionResponseDTO:
        """Execute batch prediction for multiple locations."""
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
                result = self.multi_metric_prediction_interactor.execute(single_request)
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
