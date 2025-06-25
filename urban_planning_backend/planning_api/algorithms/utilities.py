# planning_api/algorithms/utilities.py
"""
Python implementation of C# utility functions and extensions
Converted from Extension.cs, Statistics.cs
"""

import random
import math
from typing import List, TypeVar, Generic, Optional, Callable, Tuple, Any, Dict
from abc import ABC, abstractmethod
import numpy as np
from dataclasses import dataclass


T = TypeVar('T')


class ListExtensions:
    """Extension methods for lists - equivalent to C# Extension class"""
    
    @staticmethod
    def swap(lst: List[T], first_index: int, second_index: int):
        """Swap two values in a list given their indexes"""
        if len(lst) < 2 or first_index == second_index:
            return
        
        if 0 <= first_index < len(lst) and 0 <= second_index < len(lst):
            lst[first_index], lst[second_index] = lst[second_index], lst[first_index]
    
    @staticmethod
    def populate(lst: List[T], value: T):
        """Populate a list with a specific value"""
        if lst is None:
            return
        
        for i in range(len(lst)):
            lst[i] = value
    
    @staticmethod
    def populate_2d(array: List[List[T]], rows: int, columns: int, default_value: T = None):
        """Populate a 2D array with a default value"""
        for i in range(rows):
            for j in range(columns):
                if i < len(array) and j < len(array[i]):
                    array[i][j] = default_value
    
    @staticmethod
    def shuffle(lst: List[T]):
        """Shuffle the list in place using Fisher-Yates algorithm"""
        n = len(lst)
        for i in range(n - 1):
            # Random index from i to n-1
            r = i + random.randint(0, n - i - 1)
            lst[i], lst[r] = lst[r], lst[i]
    
    @staticmethod
    def try_find_first(lst: List[T], predicate: Callable[[T], bool]) -> Tuple[bool, Optional[T]]:
        """
        Try to find the first element that matches the predicate
        Returns: (found, element)
        """
        if not lst:
            return False, None
        
        try:
            for item in lst:
                if predicate(item):
                    return True, item
            return False, None
        except Exception:
            return False, None


class StringExtensions:
    """String utility extensions"""
    
    @staticmethod
    def pad_center(text: str, new_width: int, filler_character: str = ' ') -> str:
        """Center text within a specified width using filler character"""
        if not text:
            return text
        
        length = len(text)
        characters_to_pad = new_width - length
        
        if characters_to_pad < 0:
            raise ValueError("New width must be greater than string length")
        
        pad_left = characters_to_pad // 2 + characters_to_pad % 2
        pad_right = characters_to_pad // 2
        
        return filler_character * pad_left + text + filler_character * pad_right


class LinkedListNode(Generic[T]):
    """Generic linked list node"""
    
    def __init__(self, value: T):
        self.value = value
        self.next: Optional['LinkedListNode[T]'] = None
        self.previous: Optional['LinkedListNode[T]'] = None
        self.list: Optional['LinkedList[T]'] = None


class LinkedList(Generic[T]):
    """Generic doubly-linked list implementation"""
    
    def __init__(self):
        self.first: Optional[LinkedListNode[T]] = None
        self.last: Optional[LinkedListNode[T]] = None
        self.count = 0
    
    def add_first(self, value: T) -> LinkedListNode[T]:
        """Add value to the beginning of the list"""
        node = LinkedListNode(value)
        node.list = self
        
        if self.first is None:
            self.first = self.last = node
        else:
            node.next = self.first
            self.first.previous = node
            self.first = node
        
        self.count += 1
        return node
    
    def add_last(self, value: T) -> LinkedListNode[T]:
        """Add value to the end of the list"""
        node = LinkedListNode(value)
        node.list = self
        
        if self.last is None:
            self.first = self.last = node
        else:
            node.previous = self.last
            self.last.next = node
            self.last = node
        
        self.count += 1
        return node
    
    def remove(self, node: LinkedListNode[T]) -> bool:
        """Remove a specific node from the list"""
        if node.list != self:
            return False
        
        if node.previous:
            node.previous.next = node.next
        else:
            self.first = node.next
        
        if node.next:
            node.next.previous = node.previous
        else:
            self.last = node.previous
        
        node.list = None
        node.next = None
        node.previous = None
        self.count -= 1
        return True
    
    def clear(self):
        """Clear all nodes from the list"""
        current = self.first
        while current:
            next_node = current.next
            current.list = None
            current.next = None
            current.previous = None
            current = next_node
        
        self.first = None
        self.last = None
        self.count = 0


class CircularLinkedListExtensions:
    """Extensions for circular linked list operations"""
    
    @staticmethod
    def next_or_first(node: LinkedListNode[T]) -> Optional[LinkedListNode[T]]:
        """Get next node or first node if at end (circular behavior)"""
        if node.next:
            return node.next
        return node.list.first if node.list else None
    
    @staticmethod
    def previous_or_last(node: LinkedListNode[T]) -> Optional[LinkedListNode[T]]:
        """Get previous node or last node if at beginning (circular behavior)"""
        if node.previous:
            return node.previous
        return node.list.last if node.list else None


class Statistics:
    """Statistical analysis functions - equivalent to C# Statistics class"""
    
    @staticmethod
    def linear_regression(x_vals: List[float], y_vals: List[float]) -> Tuple[float, float, float]:
        """
        Perform linear regression
        Returns: (r_squared, y_intercept, slope)
        """
        if len(x_vals) != len(y_vals):
            raise ValueError("x_vals and y_vals should have the same length")
        
        n = len(x_vals)
        if n == 0:
            return 0.0, 0.0, 0.0
        
        # Calculate sums
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_x2 = sum(x * x for x in x_vals)
        sum_y2 = sum(y * y for y in y_vals)
        
        # Calculate slope and intercept
        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return 0.0, sum_y / n if n > 0 else 0.0, 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        y_intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R-squared
        y_denominator = n * sum_y2 - sum_y * sum_y
        if abs(y_denominator) < 1e-10:
            r_squared = 0.0
        else:
            r_squared = slope * ((n * sum_xy - sum_x * sum_y) / y_denominator)
        
        return r_squared, y_intercept, slope
    
    @staticmethod
    def power_regression(x_vals: List[float], y_vals: List[float]) -> Tuple[float, float, float]:
        """
        Perform power regression: y = a * x^b
        Returns: (R2, a, b)
        """
        if len(x_vals) != len(y_vals):
            raise ValueError("x_vals and y_vals should have the same length")
        
        n = len(x_vals)
        if n == 0:
            return 0.0, 0.0, 0.0
        
        # Check for non-positive values
        if any(x <= 0 for x in x_vals) or any(y <= 0 for y in y_vals):
            raise ValueError("All values must be positive for power regression")
        
        # Transform to logarithmic space
        ln_x_vals = [math.log(x) for x in x_vals]
        ln_y_vals = [math.log(y) for y in y_vals]
        
        # Calculate sums in log space
        ln_x_sum = sum(ln_x_vals)
        ln_y_sum = sum(ln_y_vals)
        ln_x2_sum = sum(ln_x * ln_x for ln_x in ln_x_vals)
        ln_y2_sum = sum(ln_y * ln_y for ln_y in ln_y_vals)
        ln_x_ln_y_sum = sum(ln_x * ln_y for ln_x, ln_y in zip(ln_x_vals, ln_y_vals))
        
        ln_x_mean = ln_x_sum / n
        ln_y_mean = ln_y_sum / n
        
        # Calculate regression coefficients
        sxx = ln_x2_sum - ln_x_mean * ln_x_mean * n
        syy = ln_y2_sum - ln_y_mean * ln_y_mean * n
        sxy = ln_x_ln_y_sum - n * ln_x_mean * ln_y_mean
        
        if abs(sxx) < 1e-10 or abs(syy) < 1e-10:
            return 0.0, 1.0, 0.0
        
        r2 = (sxy * sxy) / (sxx * syy)
        b = sxy / sxx
        a = math.exp(ln_y_mean - b * ln_x_mean)
        
        return r2, a, b
    
    @staticmethod
    def power_estimate(a: float, b: float, x: float) -> float:
        """Estimate y value using power regression parameters"""
        if x <= 0:
            return 0.0
        return a * (x ** b)
    
    @staticmethod
    def exponential_regression(x_vals: List[float], y_vals: List[float]) -> Tuple[float, float, float]:
        """
        Perform exponential regression: y = a * b^x
        Returns: (R2, a, b)
        """
        if len(x_vals) != len(y_vals):
            raise ValueError("x_vals and y_vals should have the same length")
        
        n = len(x_vals)
        if n == 0:
            return 0.0, 0.0, 0.0
        
        # Check for non-positive y values
        if any(y <= 0 for y in y_vals):
            raise ValueError("All y values must be positive for exponential regression")
        
        # Transform y values to logarithmic space
        ln_y_vals = [math.log(y) for y in y_vals]
        
        # Calculate sums
        x_sum = sum(x_vals)
        ln_y_sum = sum(ln_y_vals)
        x2_sum = sum(x * x for x in x_vals)
        ln_y2_sum = sum(ln_y * ln_y for ln_y in ln_y_vals)
        x_ln_y_sum = sum(x * ln_y for x, ln_y in zip(x_vals, ln_y_vals))
        
        x_mean = x_sum / n
        ln_y_mean = ln_y_sum / n
        
        # Calculate regression coefficients
        sxx = x2_sum - x_mean * x_mean * n
        syy = ln_y2_sum - ln_y_mean * ln_y_mean * n
        sxy = x_ln_y_sum - n * x_mean * ln_y_mean
        
        if abs(sxx) < 1e-10 or abs(syy) < 1e-10:
            return 0.0, 1.0, 1.0
        
        r2 = (sxy * sxy) / (sxx * syy)
        b = math.exp(sxy / sxx)
        a = math.exp(ln_y_mean - x_mean * math.log(b))
        
        return r2, a, b
    
    @staticmethod
    def exponential_estimate(a: float, b: float, x: float) -> float:
        """Estimate y value using exponential regression parameters"""
        return a * (b ** x)
    
    @staticmethod
    def mean(values: List[float]) -> float:
        """Calculate arithmetic mean"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    @staticmethod
    def median(values: List[float]) -> float:
        """Calculate median"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]
    
    @staticmethod
    def mode(values: List[float]) -> float:
        """Calculate mode (most frequent value)"""
        if not values:
            return 0.0
        
        frequency = {}
        for value in values:
            frequency[value] = frequency.get(value, 0) + 1
        
        return max(frequency, key=frequency.get)
    
    @staticmethod
    def variance(values: List[float], population: bool = False) -> float:
        """Calculate variance (sample or population)"""
        if len(values) < 2:
            return 0.0
        
        mean_val = Statistics.mean(values)
        sum_squared_diff = sum((x - mean_val) ** 2 for x in values)
        
        divisor = len(values) if population else len(values) - 1
        return sum_squared_diff / divisor
    
    @staticmethod
    def standard_deviation(values: List[float], population: bool = False) -> float:
        """Calculate standard deviation (sample or population)"""
        return math.sqrt(Statistics.variance(values, population))
    
    @staticmethod
    def correlation_coefficient(x_vals: List[float], y_vals: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x_vals) != len(y_vals) or len(x_vals) < 2:
            return 0.0
        
        n = len(x_vals)
        
        # Calculate means
        x_mean = Statistics.mean(x_vals)
        y_mean = Statistics.mean(y_vals)
        
        # Calculate correlation components
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        sum_x_squared = sum((x - x_mean) ** 2 for x in x_vals)
        sum_y_squared = sum((y - y_mean) ** 2 for y in y_vals)
        
        denominator = math.sqrt(sum_x_squared * sum_y_squared)
        
        if abs(denominator) < 1e-10:
            return 0.0
        
        return numerator / denominator
    
    @staticmethod
    def quartiles(values: List[float]) -> Tuple[float, float, float]:
        """
        Calculate quartiles (Q1, Q2/median, Q3)
        Returns: (Q1, Q2, Q3)
        """
        if not values:
            return 0.0, 0.0, 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Q2 (median)
        q2 = Statistics.median(sorted_values)
        
        # Q1 (median of lower half)
        lower_half = sorted_values[:n//2]
        q1 = Statistics.median(lower_half) if lower_half else sorted_values[0]
        
        # Q3 (median of upper half)
        upper_half = sorted_values[(n+1)//2:] if n % 2 == 1 else sorted_values[n//2:]
        q3 = Statistics.median(upper_half) if upper_half else sorted_values[-1]
        
        return q1, q2, q3
    
    @staticmethod
    def interquartile_range(values: List[float]) -> float:
        """Calculate interquartile range (Q3 - Q1)"""
        q1, _, q3 = Statistics.quartiles(values)
        return q3 - q1


class MathUtilities:
    """Additional mathematical utility functions"""
    
    @staticmethod
    def clamp(value: float, min_value: float, max_value: float) -> float:
        """Clamp value between min and max"""
        return max(min_value, min(max_value, value))
    
    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        """Linear interpolation between a and b"""
        return a + t * (b - a)
    
    @staticmethod
    def inverse_lerp(a: float, b: float, value: float) -> float:
        """Inverse linear interpolation - find t where lerp(a, b, t) = value"""
        if abs(b - a) < 1e-10:
            return 0.0
        return (value - a) / (b - a)
    
    @staticmethod
    def remap(value: float, from_min: float, from_max: float, 
              to_min: float, to_max: float) -> float:
        """Remap value from one range to another"""
        t = MathUtilities.inverse_lerp(from_min, from_max, value)
        return MathUtilities.lerp(to_min, to_max, t)
    
    @staticmethod
    def smooth_step(edge0: float, edge1: float, x: float) -> float:
        """Smooth step function (Hermite interpolation)"""
        t = MathUtilities.clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)
    
    @staticmethod
    def approx_equal(a: float, b: float, tolerance: float = 1e-9) -> bool:
        """Check if two floats are approximately equal"""
        return abs(a - b) <= tolerance
    
    @staticmethod
    def sign(value: float) -> int:
        """Get sign of value (-1, 0, or 1)"""
        if value > 0:
            return 1
        elif value < 0:
            return -1
        else:
            return 0
    
    @staticmethod
    def factorial(n: int) -> int:
        """Calculate factorial"""
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n <= 1:
            return 1
        
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
    
    @staticmethod
    def combination(n: int, r: int) -> int:
        """Calculate combination C(n,r) = n! / (r! * (n-r)!)"""
        if r > n or r < 0:
            return 0
        if r == 0 or r == n:
            return 1
        
        # Use more efficient calculation to avoid large factorials
        r = min(r, n - r)  # Take advantage of symmetry
        result = 1
        
        for i in range(r):
            result = result * (n - i) // (i + 1)
        
        return result
    
    @staticmethod
    def permutation(n: int, r: int) -> int:
        """Calculate permutation P(n,r) = n! / (n-r)!"""
        if r > n or r < 0:
            return 0
        if r == 0:
            return 1
        
        result = 1
        for i in range(n, n - r, -1):
            result *= i
        
        return result


class CollectionUtilities:
    """Utility functions for working with collections"""
    
    @staticmethod
    def chunk(lst: List[T], chunk_size: int) -> List[List[T]]:
        """Split list into chunks of specified size"""
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def flatten(nested_list: List[List[T]]) -> List[T]:
        """Flatten a nested list"""
        result = []
        for sublist in nested_list:
            result.extend(sublist)
        return result
    
    @staticmethod
    def unique(lst: List[T]) -> List[T]:
        """Get unique elements while preserving order"""
        seen = set()
        result = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    
    @staticmethod
    def group_by(lst: List[T], key_func: Callable[[T], Any]) -> Dict[Any, List[T]]:
        """Group list elements by a key function"""
        groups = {}
        for item in lst:
            key = key_func(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups
    
    @staticmethod
    def partition(lst: List[T], predicate: Callable[[T], bool]) -> Tuple[List[T], List[T]]:
        """Partition list into two lists based on predicate"""
        true_list = []
        false_list = []
        
        for item in lst:
            if predicate(item):
                true_list.append(item)
            else:
                false_list.append(item)
        
        return true_list, false_list
    
    @staticmethod
    def take_while(lst: List[T], predicate: Callable[[T], bool]) -> List[T]:
        """Take elements while predicate is true"""
        result = []
        for item in lst:
            if predicate(item):
                result.append(item)
            else:
                break
        return result
    
    @staticmethod
    def skip_while(lst: List[T], predicate: Callable[[T], bool]) -> List[T]:
        """Skip elements while predicate is true"""
        result = []
        skipping = True
        
        for item in lst:
            if skipping and predicate(item):
                continue
            else:
                skipping = False
                result.append(item)
        
        return result


@dataclass
class ValidationResult:
    """Result of a validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.is_valid = self.is_valid and other.is_valid


class Validators:
    """Common validation functions"""
    
    @staticmethod
    def validate_range(value: float, min_value: float, max_value: float, 
                      name: str = "Value") -> ValidationResult:
        """Validate that value is within range"""
        result = ValidationResult(True, [], [])
        
        if value < min_value:
            result.add_error(f"{name} ({value}) is below minimum ({min_value})")
        elif value > max_value:
            result.add_error(f"{name} ({value}) is above maximum ({max_value})")
        
        return result
    
    @staticmethod
    def validate_not_none(value: Any, name: str = "Value") -> ValidationResult:
        """Validate that value is not None"""
        result = ValidationResult(True, [], [])
        
        if value is None:
            result.add_error(f"{name} cannot be None")
        
        return result
    
    @staticmethod
    def validate_list_not_empty(lst: List[Any], name: str = "List") -> ValidationResult:
        """Validate that list is not empty"""
        result = ValidationResult(True, [], [])
        
        if not lst:
            result.add_error(f"{name} cannot be empty")
        
        return result
    
    @staticmethod
    def validate_positive(value: float, name: str = "Value") -> ValidationResult:
        """Validate that value is positive"""
        result = ValidationResult(True, [], [])
        
        if value <= 0:
            result.add_error(f"{name} ({value}) must be positive")
        
        return result
    
    @staticmethod
    def validate_non_negative(value: float, name: str = "Value") -> ValidationResult:
        """Validate that value is non-negative"""
        result = ValidationResult(True, [], [])
        
        if value < 0:
            result.add_error(f"{name} ({value}) cannot be negative")
        
        return result


# Example usage and testing functions
def test_list_extensions():
    """Test list extension functions"""
    print("Testing List Extensions:")
    
    # Test swap
    test_list = [1, 2, 3, 4, 5]
    ListExtensions.swap(test_list, 1, 3)
    print(f"  After swap(1,3): {test_list}")
    
    # Test shuffle
    test_list = list(range(10))
    original = test_list.copy()
    ListExtensions.shuffle(test_list)
    print(f"  Original: {original}")
    print(f"  Shuffled: {test_list}")
    
    # Test try_find_first
    found, result = ListExtensions.try_find_first(test_list, lambda x: x > 5)
    print(f"  First > 5: Found={found}, Value={result}")


def test_statistics():
    """Test statistical functions"""
    print("\nTesting Statistics:")
    
    # Test data
    x_data = [1, 2, 3, 4, 5]
    y_data = [2, 4, 6, 8, 10]  # Perfect linear relationship
    
    # Linear regression
    r2, intercept, slope = Statistics.linear_regression(x_data, y_data)
    print(f"  Linear regression: R²={r2:.3f}, slope={slope:.3f}, intercept={intercept:.3f}")
    
    # Basic statistics
    values = [1, 2, 3, 4, 5, 5, 6, 7, 8, 9]
    print(f"  Mean: {Statistics.mean(values):.2f}")
    print(f"  Median: {Statistics.median(values):.2f}")
    print(f"  Standard deviation: {Statistics.standard_deviation(values):.2f}")
    
    # Quartiles
    q1, q2, q3 = Statistics.quartiles(values)
    print(f"  Quartiles: Q1={q1:.2f}, Q2={q2:.2f}, Q3={q3:.2f}")


def test_math_utilities():
    """Test mathematical utility functions"""
    print("\nTesting Math Utilities:")
    
    # Test clamp
    print(f"  Clamp 15 to [0,10]: {MathUtilities.clamp(15, 0, 10)}")
    
    # Test lerp
    print(f"  Lerp from 0 to 10 at t=0.5: {MathUtilities.lerp(0, 10, 0.5)}")
    
    # Test remap
    remapped = MathUtilities.remap(5, 0, 10, 100, 200)
    print(f"  Remap 5 from [0,10] to [100,200]: {remapped}")
    
    # Test combinations
    print(f"  C(10,3): {MathUtilities.combination(10, 3)}")
    print(f"  P(10,3): {MathUtilities.permutation(10, 3)}")


def test_collection_utilities():
    """Test collection utility functions"""
    print("\nTesting Collection Utilities:")
    
    # Test chunk
    data = list(range(10))
    chunks = CollectionUtilities.chunk(data, 3)
    print(f"  Chunks of 3: {chunks}")
    
    # Test unique
    with_duplicates = [1, 2, 2, 3, 3, 3, 4]
    unique_values = CollectionUtilities.unique(with_duplicates)
    print(f"  Unique values: {unique_values}")
    
    # Test group_by
    words = ["apple", "banana", "apricot", "blueberry", "cherry"]
    grouped = CollectionUtilities.group_by(words, lambda x: x[0])
    print(f"  Grouped by first letter: {grouped}")


if __name__ == "__main__":
    test_list_extensions()
    test_statistics()
    test_math_utilities()
    test_collection_utilities()