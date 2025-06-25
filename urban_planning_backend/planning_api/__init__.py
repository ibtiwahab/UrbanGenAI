# planning_api/__init__.py - COMPLETE FIXED VERSION
"""
Urban Planning API Package

This package contains:
- Main planning generation algorithms
- Geometry processing and analysis
- Graph algorithms (converted from C#) - if available
- Mathematical utilities and statistics - if available
- Interval trees and spatial data structures - if available
- Clustering and distribution analysis

Converted C# algorithms (optional):
- Graph algorithms: Dijkstra, Centrality calculation, DFS
- Mathematics: Root finding, quadratic solver, parabola operations
- Trees: Interval trees with Red-Black tree implementation
- Utilities: Statistics, collection operations, extensions
"""

__version__ = '1.0.0'
__author__ = 'Urban Planning Team'

import logging

logger = logging.getLogger(__name__)

# Initialize availability flags
ALGORITHMS_AVAILABLE = False
ALGORITHM_MODULES = {}

# Try to import algorithms package gracefully
def _import_algorithms():
    """Import algorithms with graceful error handling"""
    global ALGORITHMS_AVAILABLE, ALGORITHM_MODULES
    
    algorithm_modules = {}
    
    # Try importing individual algorithm modules
    try:
        from . import algorithms
        from .algorithms import graph_algorithms
        algorithm_modules['graph_algorithms'] = graph_algorithms
        logger.info("Graph algorithms imported successfully")
    except ImportError as e:
        logger.warning(f"Graph algorithms not available: {e}")
    
    try:
        from . import algorithms
        from .algorithms import trees
        algorithm_modules['trees'] = trees
        logger.info("Tree algorithms imported successfully")
    except ImportError as e:
        logger.warning(f"Tree algorithms not available: {e}")
    
    try:
        from . import algorithms
        from .algorithms import mathematics
        algorithm_modules['mathematics'] = mathematics
        logger.info("Mathematics algorithms imported successfully")
    except ImportError as e:
        logger.warning(f"Mathematics algorithms not available: {e}")
    
    try:
        from . import algorithms
        from .algorithms import utilities
        algorithm_modules['utilities'] = utilities
        logger.info("Utilities imported successfully")
    except ImportError as e:
        logger.warning(f"Utilities not available: {e}")
    
    if algorithm_modules:
        ALGORITHMS_AVAILABLE = True
        ALGORITHM_MODULES = algorithm_modules
        logger.info(f"Partial algorithm support: {list(algorithm_modules.keys())}")
        return True
    else:
        logger.warning("No algorithm modules available")
        return False

# Try to import algorithms on package initialization
try:
    _import_algorithms()
    if ALGORITHMS_AVAILABLE:
        print("Urban Planning algorithms loaded successfully")
    else:
        print("Urban Planning API running in basic mode (no algorithms)")
except Exception as e:
    print(f"Warning: Could not initialize algorithms: {e}")

# Package information function
def get_package_info():
    """Get information about the package and available modules"""
    return {
        'version': __version__,
        'author': __author__,
        'algorithms_available': ALGORITHMS_AVAILABLE,
        'available_modules': list(ALGORITHM_MODULES.keys()),
        'description': 'Urban Planning API with geometry processing and optional C# converted algorithms'
    }

def get_algorithm_module(module_name):
    """Get a specific algorithm module if available"""
    return ALGORITHM_MODULES.get(module_name)

def is_module_available(module_name):
    """Check if a specific algorithm module is available"""
    return module_name in ALGORITHM_MODULES

# Export availability functions for other modules to use
__all__ = [
    'get_package_info',
    'get_algorithm_module', 
    'is_module_available',
    'ALGORITHMS_AVAILABLE',
    'ALGORITHM_MODULES'
]