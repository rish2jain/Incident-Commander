"""
DynamoDB Helper Functions
Utilities for handling DynamoDB data type conversions
"""

from decimal import Decimal
from typing import Any, Dict, List, Union


def convert_floats_to_decimal(obj: Any) -> Any:
    """
    Recursively convert Python floats to Decimal for DynamoDB compatibility.
    
    Args:
        obj: The object to convert (dict, list, or primitive)
        
    Returns:
        The object with all floats converted to Decimal
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    else:
        return obj


def prepare_item_for_dynamodb(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare an item for DynamoDB storage by converting floats to Decimal.
    
    Args:
        item: Dictionary to prepare for DynamoDB
        
    Returns:
        Dictionary with floats converted to Decimal
    """
    return convert_floats_to_decimal(item)


def convert_decimal_to_float(obj: Any) -> Any:
    """
    Recursively convert Decimal back to float for JSON serialization.
    
    Args:
        obj: The object to convert (dict, list, or primitive)
        
    Returns:
        The object with all Decimals converted to float
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    else:
        return obj