"""Linear interpolation service (Framework layer).

This module provides shared linear interpolation functionality
used by multiple services in the application.

Design:
- DRY (Don't Repeat Yourself) principle
- Single source of truth for interpolation logic
- Reusable across different services
"""

import numpy as np
from typing import List

class InterpolationService:
    """Service providing linear interpolation for missing values.
    
    This service implements linear interpolation with the following strategy:
    1. Forward fill: Missing values at the beginning use first valid value
    2. Backward fill: Missing values at the end use last valid value
    3. Linear interpolation: Missing values in the middle are interpolated
    
    Mathematical formula for linear interpolation:
        value[i] = value[prev] + weight × (value[next] - value[prev])
        where weight = (i - prev) / (next - prev)
    
    This service is used by:
    - ARIMAPredictionService: For time series data
    - WeatherLinearInterpolator: For weather temperature data
    """
    
    @staticmethod
    def interpolate_missing_values(data: List[float]) -> List[float]:
        """Apply linear interpolation to fill missing values.
        
        Strategy:
        1. Forward fill for missing values at beginning
        2. Backward fill for missing values at end
        3. Linear interpolation for missing values in middle
        
        Args:
            data: List of float values (may contain np.nan for missing values)
            
        Returns:
            List with interpolated values
            
        Raises:
            ValueError: If all values are missing
            
        Examples:
            >>> InterpolationService.interpolate_missing_values([10.0, np.nan, 20.0])
            [10.0, 15.0, 20.0]
            
            >>> InterpolationService.interpolate_missing_values([np.nan, 15.0, 20.0])
            [15.0, 15.0, 20.0]
            
            >>> InterpolationService.interpolate_missing_values([10.0, 15.0, np.nan])
            [10.0, 15.0, 15.0]
        """
        if not data:
            return data
        
        # Convert to numpy array for easier manipulation
        arr = np.array(data, dtype=float)
        
        # Find indices of non-null values
        valid_indices = np.where(~np.isnan(arr))[0]
        
        if len(valid_indices) == 0:
            raise ValueError("All values are missing. Cannot perform interpolation.")
        
        # Forward fill: If there are missing values at the beginning, use the first valid value
        if valid_indices[0] > 0:
            arr[:valid_indices[0]] = arr[valid_indices[0]]
        
        # Backward fill: If there are missing values at the end, use the last valid value
        if valid_indices[-1] < len(arr) - 1:
            arr[valid_indices[-1] + 1:] = arr[valid_indices[-1]]
        
        # Linear interpolation: Interpolate missing values in the middle
        for i in range(len(arr)):
            if np.isnan(arr[i]):
                # Find the nearest non-null values before and after
                prev_idx = None
                next_idx = None
                
                # Search backward for previous valid value
                for j in range(i - 1, -1, -1):
                    if not np.isnan(arr[j]):
                        prev_idx = j
                        break
                
                # Search forward for next valid value
                for j in range(i + 1, len(arr)):
                    if not np.isnan(arr[j]):
                        next_idx = j
                        break
                
                # Perform linear interpolation
                if prev_idx is not None and next_idx is not None:
                    # Linear interpolation formula
                    weight = (i - prev_idx) / (next_idx - prev_idx)
                    arr[i] = arr[prev_idx] + weight * (arr[next_idx] - arr[prev_idx])
        
        return arr.tolist()

