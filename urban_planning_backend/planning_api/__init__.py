# planning_api/__init__.py - Package initialization
"""
Urban Planning API Package

This package contains:
- Main planning generation algorithms
- Geometry processing and analysis
- Graph algorithms (converted from C#)
- Mathematical utilities and statistics
- Interval trees and spatial data structures
- Clustering and distribution analysis

Converted C# algorithms:
- Graph algorithms: Dijkstra, Centrality calculation, DFS
- Mathematics: Root finding, quadratic solver, parabola operations
- Trees: Interval trees with Red-Black tree implementation
- Utilities: Statistics, collection operations, extensions
"""

__version__ = '1.0.0'
__author__ = 'Urban Planning Team'


# planning_api/apps.py - Updated app configuration
from django.apps import AppConfig


class PlanningApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planning_api'
    verbose_name = 'Urban Planning API'
    
    def ready(self):
        """Initialize the app and import algorithms"""
        # Import algorithms to ensure they're available
        try:
            from . import algorithms
            print("Urban Planning algorithms loaded successfully")
        except ImportError as e:
            print(f"Warning: Could not load algorithms: {e}")


# planning_api/algorithms/__init__.py - Algorithms package initialization
"""
Algorithms package for urban planning

This package contains Python implementations of C# algorithms:
- graph_algorithms: Graph processing, shortest paths, centrality
- mathematics: Root finding, equation solving, geometry math
- trees: Interval trees, Red-Black trees
- utilities: Statistics, collection operations, validation
"""

from .graph_algorithms import (
    DijkstraShortestPaths,
    CalculateCentrality,
    DepthFirstSearch,
    GraphAdapter,
    Edge,
    DirectedEdge
)

from .mathematics import (
    RootFinding,
    SolveQuadratic,
    Parabola,
    GeometryMath,
    Point2D,
    Vector2D
)

from .trees import (
    IntervalTree,
    UInterval,
    IntervalNode,
    IntervalTreeOperations
)

from .utilities import (
    Statistics,
    MathUtilities,
    CollectionUtilities,
    ListExtensions,
    Validators
)

__all__ = [
    # Graph algorithms
    'DijkstraShortestPaths',
    'CalculateCentrality', 
    'DepthFirstSearch',
    'GraphAdapter',
    'Edge',
    'DirectedEdge',
    
    # Mathematics
    'RootFinding',
    'SolveQuadratic',
    'Parabola',
    'GeometryMath',
    'Point2D',
    'Vector2D',
    
    # Trees
    'IntervalTree',
    'UInterval', 
    'IntervalNode',
    'IntervalTreeOperations',
    
    # Utilities
    'Statistics',
    'MathUtilities',
    'CollectionUtilities',
    'ListExtensions',
    'Validators'
]
