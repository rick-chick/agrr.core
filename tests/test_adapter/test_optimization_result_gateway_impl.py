"""Tests for OptimizationResultGatewayImpl."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from agrr_core.adapter.gateways.optimization_result_gateway_impl import (
    OptimizationResultGatewayImpl,
)
from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)


@pytest.mark.asyncio
class TestOptimizationResultGatewayImpl:
    """Test cases for OptimizationResultGatewayImpl."""

    async def test_save(self):
        """Test saving optimization results through gateway."""
        mock_repository = AsyncMock()
        gateway = OptimizationResultGatewayImpl(mock_repository)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                total_cost=530000.0,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        
        optimization_id = "test_opt"
        await gateway.save(optimization_id, results)
        
        mock_repository.save.assert_called_once_with(optimization_id, results)

    async def test_get(self):
        """Test retrieving optimization results through gateway."""
        mock_repository = AsyncMock()
        expected_results = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                total_cost=530000.0,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        mock_repository.get.return_value = expected_results
        
        gateway = OptimizationResultGatewayImpl(mock_repository)
        
        optimization_id = "test_opt"
        results = await gateway.get(optimization_id)
        
        mock_repository.get.assert_called_once_with(optimization_id)
        assert results == expected_results

    async def test_get_all(self):
        """Test retrieving all optimization results through gateway."""
        mock_repository = AsyncMock()
        expected_all = [
            ("opt_1", [OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                total_cost=530000.0,
                is_optimal=True,
                base_temperature=10.0,
            )]),
            ("opt_2", [OptimizationIntermediateResult(
                start_date=datetime(2024, 5, 1),
                completion_date=datetime(2024, 8, 15),
                growth_days=107,
                accumulated_gdd=1600.0,
                total_cost=535000.0,
                is_optimal=False,
                base_temperature=10.0,
            )])
        ]
        mock_repository.get_all.return_value = expected_all
        
        gateway = OptimizationResultGatewayImpl(mock_repository)
        
        all_results = await gateway.get_all()
        
        mock_repository.get_all.assert_called_once()
        assert all_results == expected_all

    async def test_delete(self):
        """Test deleting optimization results through gateway."""
        mock_repository = AsyncMock()
        mock_repository.delete.return_value = True
        
        gateway = OptimizationResultGatewayImpl(mock_repository)
        
        optimization_id = "test_opt"
        deleted = await gateway.delete(optimization_id)
        
        mock_repository.delete.assert_called_once_with(optimization_id)
        assert deleted is True

    async def test_clear(self):
        """Test clearing all optimization results through gateway."""
        mock_repository = AsyncMock()
        gateway = OptimizationResultGatewayImpl(mock_repository)
        
        await gateway.clear()
        
        mock_repository.clear.assert_called_once()

