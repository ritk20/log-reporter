import numpy as np
from typing import List, Dict, Union

class MathHelpers:
    @staticmethod
    def round_to_decimal(value: Union[int, float], decimals: int = 2) -> float:
        """Round a value to specified decimal places."""
        return round(float(value), decimals)
    
    @staticmethod
    def compute_statistics(values: List[Union[int, float]], prefix: str) -> Dict[str, float]:
        """Compute basic statistics for a list of values."""
        if not values:
            return {
                f"average{prefix}": 0.0,
                f"min{prefix}": 0.0,
                f"max{prefix}": 0.0,
            }
        
        np_values = np.array(values)
        return {
            f"average{prefix}": MathHelpers.round_to_decimal(float(np.mean(np_values))),
            f"min{prefix}": MathHelpers.round_to_decimal(float(np.min(np_values))),
            f"max{prefix}": MathHelpers.round_to_decimal(float(np.max(np_values))),
        }
