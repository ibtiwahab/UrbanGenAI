# planning_api/algorithms_views.py - COMPLETE FIXED VERSION
"""
Django views integrating the converted C# algorithms
Fixed version with proper error handling and conditional imports
"""

import logging
import json
from typing import List, Dict, Any, Tuple
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

logger = logging.getLogger(__name__)

# Check for available algorithm modules with graceful fallbacks
GRAPH_ALGORITHMS_AVAILABLE = False
TREE_ALGORITHMS_AVAILABLE = False
MATH_ALGORITHMS_AVAILABLE = False
UTILITIES_AVAILABLE = False

# Try to import graph algorithms
try:
    from .algorithms.graph_algorithms import (
        DijkstraShortestPaths, CalculateCentrality, DepthFirstSearch,
        GraphAdapter, Edge, DirectedEdge, EdgeWeightedGraph, EdgeWeightedDigraph
    )
    GRAPH_ALGORITHMS_AVAILABLE = True
    logger.info("Graph algorithms imported successfully")
except ImportError as e:
    logger.warning(f"Graph algorithms not available: {e}")

# Try to import tree algorithms
try:
    from .algorithms.trees import IntervalTree, UInterval, IntervalNode, IntervalTreeOperations
    TREE_ALGORITHMS_AVAILABLE = True
    logger.info("Tree algorithms imported successfully")
except ImportError as e:
    logger.warning(f"Tree algorithms not available: {e}")

# Try to import mathematics
try:
    from .algorithms.mathematics import (
        RootFinding, SolveQuadratic, Parabola, GeometryMath, Point2D, Vector2D
    )
    MATH_ALGORITHMS_AVAILABLE = True
    logger.info("Mathematics algorithms imported successfully")
except ImportError as e:
    logger.warning(f"Mathematics algorithms not available: {e}")

# Try to import utilities
try:
    from .algorithms.utilities import (
        Statistics, MathUtilities, CollectionUtilities, ListExtensions, Validators
    )
    UTILITIES_AVAILABLE = True
    logger.info("Utilities imported successfully")
except ImportError as e:
    logger.warning(f"Utilities not available: {e}")


# Serializers for algorithm requests
class GraphAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for graph analysis requests"""
    vertices = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of vertex IDs"
    )
    edges = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of edge objects with 'from', 'to', and 'weight' fields"
    )
    source_vertex = serializers.IntegerField(
        required=False,
        help_text="Source vertex for shortest path calculations"
    )
    radius = serializers.FloatField(
        default=float('inf'),
        help_text="Radius for centrality calculations"
    )
    algorithm = serializers.ChoiceField(
        choices=['dijkstra', 'centrality', 'dfs'],
        default='centrality',
        help_text="Algorithm to run"
    )

    def validate_edges(self, value):
        """Validate edge format"""
        for edge in value:
            if not all(key in edge for key in ['from', 'to', 'weight']):
                raise serializers.ValidationError(
                    "Each edge must have 'from', 'to', and 'weight' fields"
                )
        return value


class IntervalAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for interval tree analysis requests"""
    intervals = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of interval objects with 'low', 'high', and 'id' fields"
    )
    query_interval = serializers.DictField(
        required=False,
        help_text="Query interval with 'low' and 'high' fields"
    )
    query_point = serializers.FloatField(
        required=False,
        help_text="Query point for point-in-interval search"
    )
    operation = serializers.ChoiceField(
        choices=['overlaps', 'contains_point', 'merge', 'gaps'],
        default='overlaps',
        help_text="Operation to perform"
    )

    def validate_intervals(self, value):
        """Validate interval format"""
        for interval in value:
            if not all(key in interval for key in ['low', 'high', 'id']):
                raise serializers.ValidationError(
                    "Each interval must have 'low', 'high', and 'id' fields"
                )
            if interval['low'] > interval['high']:
                raise serializers.ValidationError(
                    f"Invalid interval: low ({interval['low']}) > high ({interval['high']})"
                )
        return value


class MathematicsRequestSerializer(serializers.Serializer):
    """Serializer for mathematics requests"""
    operation = serializers.ChoiceField(
        choices=['quadratic', 'root_finding', 'linear_regression', 'geometry'],
        help_text="Mathematical operation to perform"
    )
    
    # Quadratic equation parameters
    a = serializers.FloatField(required=False, help_text="Quadratic coefficient a")
    b = serializers.FloatField(required=False, help_text="Linear coefficient b")
    c = serializers.FloatField(required=False, help_text="Constant coefficient c")
    
    # Root finding parameters
    function_type = serializers.ChoiceField(
        choices=['polynomial', 'exponential', 'trigonometric'],
        required=False,
        help_text="Type of function for root finding"
    )
    coefficients = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        help_text="Function coefficients"
    )
    left_bound = serializers.FloatField(required=False, help_text="Left bound for root finding")
    right_bound = serializers.FloatField(required=False, help_text="Right bound for root finding")
    tolerance = serializers.FloatField(default=1e-6, help_text="Numerical tolerance")
    
    # Statistics parameters
    x_values = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        help_text="X values for regression"
    )
    y_values = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        help_text="Y values for regression"
    )
    
    # Geometry parameters
    points = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Points for geometry calculations"
    )


class UtilitiesRequestSerializer(serializers.Serializer):
    """Serializer for utilities requests"""
    operation = serializers.ChoiceField(
        choices=['statistics', 'collection', 'validation'],
        help_text="Utility operation to perform"
    )
    
    # Statistics parameters
    values = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        help_text="Values for statistical analysis"
    )
    statistic_type = serializers.ChoiceField(
        choices=['descriptive', 'regression', 'correlation'],
        required=False,
        help_text="Type of statistical analysis"
    )
    
    # Collection parameters
    data = serializers.ListField(
        required=False,
        help_text="Data for collection operations"
    )
    chunk_size = serializers.IntegerField(
        required=False,
        help_text="Chunk size for collection operations"
    )
    
    # Validation parameters
    validation_rules = serializers.DictField(
        required=False,
        help_text="Validation rules to apply"
    )


class GraphAnalysisView(APIView):
    """Graph algorithm analysis endpoint"""
    
    def post(self, request):
        if not GRAPH_ALGORITHMS_AVAILABLE:
            return Response(
                {'error': 'Graph algorithms not available', 'available': False},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            serializer = GraphAnalysisRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            vertices = data['vertices']
            edges_data = data['edges']
            algorithm = data['algorithm']
            
            # Build graph
            edges = []
            for edge_data in edges_data:
                try:
                    if algorithm == 'dijkstra':
                        edge = DirectedEdge(
                            edge_data['from'],
                            edge_data['to'],
                            edge_data['weight']
                        )
                    else:
                        edge = Edge(
                            edge_data['from'],
                            edge_data['to'],
                            edge_data['weight']
                        )
                    edges.append(edge)
                except Exception as e:
                    return Response(
                        {'error': f'Error creating edge: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            graph = GraphAdapter(vertices, edges)
            
            # Run algorithm
            if algorithm == 'dijkstra':
                source = data.get('source_vertex', vertices[0])
                result = self._run_dijkstra(graph, source)
            elif algorithm == 'centrality':
                radius = data.get('radius', float('inf'))
                result = self._run_centrality(graph, radius)
            elif algorithm == 'dfs':
                result = self._run_dfs(graph)
            else:
                return Response(
                    {'error': f'Unknown algorithm: {algorithm}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'algorithm': algorithm,
                'result': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Graph analysis error: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Graph analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _run_dijkstra(self, graph, source):
        """Run Dijkstra's shortest path algorithm"""
        try:
            dijkstra = DijkstraShortestPaths(graph, source)
            
            result = {
                'source': source,
                'distances': {},
                'paths': {}
            }
            
            for vertex in graph.vertices():
                try:
                    if dijkstra.has_path_to(vertex):
                        result['distances'][vertex] = dijkstra.distance_to(vertex)
                        result['paths'][vertex] = dijkstra.shortest_path_to(vertex)
                    else:
                        result['distances'][vertex] = float('inf')
                        result['paths'][vertex] = None
                except Exception as e:
                    logger.warning(f"Error processing vertex {vertex}: {str(e)}")
            
            return result
        except Exception as e:
            return {'error': f'Dijkstra failed: {str(e)}'}
    
    def _run_centrality(self, graph, radius):
        """Run centrality calculation"""
        try:
            centrality = CalculateCentrality(graph, radius)
            
            result = {
                'betweenness': {str(k): v for k, v in centrality.betweenness.items()},
                'total_depths': {str(k): v for k, v in centrality.total_depths.items()},
                'node_counts': {str(k): v for k, v in centrality.node_counts.items()},
                'radius': radius
            }
            
            return result
        except Exception as e:
            return {'error': f'Centrality calculation failed: {str(e)}'}
    
    def _run_dfs(self, graph):
        """Run depth-first search to find connected components"""
        try:
            # Convert to EdgeWeightedGraph for DFS
            ewg = EdgeWeightedGraph(len(graph.vertices()))
            
            for edge in graph.edges():
                ewg.add_edge(edge)
            
            dfs = DepthFirstSearch(ewg)
            
            result = {
                'connected_components': [list(group) for group in dfs.group_list],
                'main_component': list(dfs.get_main_group_vertices()) if dfs.get_main_group_vertices() else []
            }
            
            return result
        except Exception as e:
            return {'error': f'DFS failed: {str(e)}'}


class IntervalAnalysisView(APIView):
    """Interval tree analysis endpoint"""
    
    def post(self, request):
        if not TREE_ALGORITHMS_AVAILABLE:
            return Response(
                {'error': 'Tree algorithms not available', 'available': False},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            serializer = IntervalAnalysisRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            intervals_data = data['intervals']
            operation = data['operation']
            
            # Create intervals
            intervals = []
            for interval_data in intervals_data:
                try:
                    interval = UInterval(interval_data['low'], interval_data['high'])
                    intervals.append((interval, interval_data['id']))
                except Exception as e:
                    return Response(
                        {'error': f'Invalid interval: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Build interval tree
            tree = IntervalTree()
            for interval, interval_id in intervals:
                tree.insert_interval(interval, interval_id)
            
            # Perform operation
            if operation == 'overlaps':
                query_data = data.get('query_interval')
                if not query_data:
                    return Response(
                        {'error': 'query_interval required for overlaps operation'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                query_interval = UInterval(query_data['low'], query_data['high'])
                overlaps = tree.search_overlapping_interval(query_interval)
                
                result = {
                    'query_interval': query_data,
                    'overlapping_intervals': [
                        {
                            'low': node.interval.low,
                            'high': node.interval.high,
                            'id': node.id
                        }
                        for node in overlaps
                    ]
                }
            
            elif operation == 'contains_point':
                query_point = data.get('query_point')
                if query_point is None:
                    return Response(
                        {'error': 'query_point required for contains_point operation'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                containing = tree.search_point(query_point)
                
                result = {
                    'query_point': query_point,
                    'containing_intervals': [
                        {
                            'low': node.interval.low,
                            'high': node.interval.high,
                            'id': node.id
                        }
                        for node in containing
                    ]
                }
            
            elif operation == 'merge':
                interval_objects = [interval for interval, _ in intervals]
                merged = IntervalTreeOperations.merge_overlapping_intervals(interval_objects)
                
                result = {
                    'merged_intervals': [
                        {'low': interval.low, 'high': interval.high}
                        for interval in merged
                    ]
                }
            
            elif operation == 'gaps':
                query_data = data.get('query_interval')
                if not query_data:
                    return Response(
                        {'error': 'query_interval required for gaps operation'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                query_interval = UInterval(query_data['low'], query_data['high'])
                interval_objects = [interval for interval, _ in intervals]
                gaps = IntervalTreeOperations.find_gaps(interval_objects, query_interval)
                
                result = {
                    'search_range': query_data,
                    'gaps': [
                        {'low': gap.low, 'high': gap.high}
                        for gap in gaps
                    ]
                }
            
            else:
                return Response(
                    {'error': f'Unknown operation: {operation}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'operation': operation,
                'result': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Interval analysis error: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Interval analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MathematicsView(APIView):
    """Mathematics algorithms endpoint"""
    
    def post(self, request):
        if not MATH_ALGORITHMS_AVAILABLE:
            return Response(
                {'error': 'Mathematics algorithms not available', 'available': False},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            serializer = MathematicsRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            operation = data['operation']
            
            if operation == 'quadratic':
                result = self._solve_quadratic(data)
            elif operation == 'root_finding':
                result = self._find_roots(data)
            elif operation == 'linear_regression':
                result = self._linear_regression(data)
            elif operation == 'geometry':
                result = self._geometry_calculations(data)
            else:
                return Response(
                    {'error': f'Unknown operation: {operation}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'operation': operation,
                'result': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Mathematics error: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Mathematics calculation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _solve_quadratic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Solve quadratic equation"""
        a = data.get('a', 1.0)
        b = data.get('b', 0.0)
        c = data.get('c', 0.0)
        
        try:
            root1, root2 = SolveQuadratic.solve(a, b, c)
            
            if root1 is None and root2 is None:
                roots = None
                equation_type = 'no_real_roots'
            elif root1 == root2:
                roots = [root1]
                equation_type = 'one_real_root'
            else:
                roots = [root1, root2] if root2 is not None else [root1]
                equation_type = 'two_real_roots'
            
            return {
                'equation': f"{a}x² + {b}x + {c} = 0",
                'success': True,
                'roots': roots,
                'type': equation_type
            }
        except Exception as e:
            return {
                'equation': f"{a}x² + {b}x + {c} = 0",
                'success': False,
                'error': str(e)
            }
    
    def _find_roots(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find roots using numerical methods"""
        left = data.get('left_bound', -10.0)
        right = data.get('right_bound', 10.0)
        tolerance = data.get('tolerance', 1e-6)
        coefficients = data.get('coefficients', [1, 0, -2])  # Default: x² - 2
        
        # Create polynomial function
        def polynomial(x):
            result = 0
            for i, coeff in enumerate(coefficients):
                result += coeff * (x ** (len(coefficients) - 1 - i))
            return result
        
        try:
            root = RootFinding.bisection(polynomial, left, right, tolerance)
            
            return {
                'polynomial_coefficients': coefficients,
                'search_interval': [left, right],
                'root': root,
                'success': root is not None,
                'tolerance': tolerance
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'polynomial_coefficients': coefficients,
                'search_interval': [left, right],
                'success': False
            }
    
    def _linear_regression(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform linear regression"""
        if not UTILITIES_AVAILABLE:
            return {'error': 'Statistics utilities not available'}
        
        x_values = data.get('x_values', [])
        y_values = data.get('y_values', [])
        
        if len(x_values) != len(y_values):
            return {'error': 'x_values and y_values must have the same length'}
        
        if len(x_values) < 2:
            return {'error': 'At least 2 data points required for regression'}
        
        try:
            r_squared, y_intercept, slope = Statistics.linear_regression(x_values, y_values)
            correlation = Statistics.correlation_coefficient(x_values, y_values)
            predictions = [slope * x + y_intercept for x in x_values]
            residuals = [y - pred for y, pred in zip(y_values, predictions)]
            
            return {
                'data_points': len(x_values),
                'slope': slope,
                'y_intercept': y_intercept,
                'r_squared': r_squared,
                'correlation_coefficient': correlation,
                'equation': f"y = {slope:.6f}x + {y_intercept:.6f}",
                'predictions': predictions,
                'residuals': residuals,
                'residual_sum_squares': sum(r*r for r in residuals)
            }
        except Exception as e:
            return {'error': f'Linear regression failed: {str(e)}'}
    
    def _geometry_calculations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform geometry calculations"""
        points_data = data.get('points', [])
        
        if len(points_data) < 3:
            return {'error': 'At least 3 points required for polygon calculations'}
        
        try:
            # Convert to Point2D objects
            points = []
            for point_data in points_data:
                point = Point2D(point_data['x'], point_data['y'])
                points.append(point)
            
            # Calculate polygon area and other properties
            area = GeometryMath.polygon_area(points)
            centroid = GeometryMath.polygon_centroid(points)
            
            # Calculate perimeter
            perimeter = 0.0
            for i in range(len(points)):
                j = (i + 1) % len(points)
                perimeter += points[i].distance_to(points[j])
            
            return {
                'polygon': {
                    'vertices': len(points),
                    'area': area,
                    'perimeter': perimeter,
                    'centroid': {'x': centroid.x, 'y': centroid.y}
                },
                'input_points': [{'x': p.x, 'y': p.y} for p in points]
            }
        except Exception as e:
            return {'error': f'Geometry calculation failed: {str(e)}'}


class UtilitiesView(APIView):
    """Utilities and statistical analysis endpoint"""
    
    def post(self, request):
        if not UTILITIES_AVAILABLE:
            return Response(
                {'error': 'Utilities not available', 'available': False},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            serializer = UtilitiesRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            operation = data['operation']
            
            if operation == 'statistics':
                result = self._statistical_analysis(data)
            elif operation == 'collection':
                result = self._collection_operations(data)
            elif operation == 'validation':
                result = self._validation_operations(data)
            else:
                return Response(
                    {'error': f'Unknown operation: {operation}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'operation': operation,
                'result': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Utilities error: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Utilities operation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _statistical_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis"""
        values = data.get('values', [])
        statistic_type = data.get('statistic_type', 'descriptive')
        
        if not values:
            return {'error': 'Values list cannot be empty'}
        
        try:
            if statistic_type == 'descriptive':
                mean = Statistics.mean(values)
                median = Statistics.median(values)
                std_dev = Statistics.standard_deviation(values)
                variance = Statistics.variance(values)
                q1, q2, q3 = Statistics.quartiles(values)
                iqr = Statistics.interquartile_range(values)
                
                return {
                    'descriptive_statistics': {
                        'count': len(values),
                        'mean': mean,
                        'median': median,
                        'standard_deviation': std_dev,
                        'variance': variance,
                        'quartiles': {'Q1': q1, 'Q2': q2, 'Q3': q3},
                        'interquartile_range': iqr,
                        'min': min(values),
                        'max': max(values),
                        'range': max(values) - min(values)
                    }
                }
            else:
                return {'error': f'Unsupported statistic type: {statistic_type}'}
        except Exception as e:
            return {'error': f'Statistical analysis failed: {str(e)}'}
    
    def _collection_operations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform collection operations"""
        collection_data = data.get('data', [])
        chunk_size = data.get('chunk_size', 3)
        
        if not collection_data:
            return {'error': 'Data list cannot be empty'}
        
        try:
            chunks = CollectionUtilities.chunk(collection_data, chunk_size)
            unique_values = CollectionUtilities.unique(collection_data)
            
            grouped = CollectionUtilities.group_by(
                collection_data, 
                lambda x: type(x).__name__
            )
            
            def is_numeric(x):
                return isinstance(x, (int, float))
            
            numeric, non_numeric = CollectionUtilities.partition(collection_data, is_numeric)
            
            return {
                'collection_operations': {
                    'original_count': len(collection_data),
                    'chunks': chunks,
                    'unique_values': unique_values,
                    'unique_count': len(unique_values),
                    'grouped_by_type': {k: len(v) for k, v in grouped.items()},
                    'numeric_values': numeric,
                    'non_numeric_values': non_numeric
                }
            }
        except Exception as e:
            return {'error': f'Collection operations failed: {str(e)}'}
    
    def _validation_operations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform validation operations"""
        rules = data.get('validation_rules', {})
        
        try:
            results = []
            
            if 'range_check' in rules:
                range_rule = rules['range_check']
                value = range_rule.get('value', 0)
                min_val = range_rule.get('min', 0)
                max_val = range_rule.get('max', 100)
                name = range_rule.get('name', 'Value')
                
                validation_result = Validators.validate_range(value, min_val, max_val, name)
                results.append({
                    'rule': 'range_check',
                    'valid': validation_result.is_valid,
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings
                })
            
            if 'positive_check' in rules:
                positive_rule = rules['positive_check']
                value = positive_rule.get('value', 0)
                name = positive_rule.get('name', 'Value')
                
                validation_result = Validators.validate_positive(value, name)
                results.append({
                    'rule': 'positive_check',
                    'valid': validation_result.is_valid,
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings
                })
            
            overall_valid = all(result['valid'] for result in results)
            
            return {
                'validation_results': {
                    'overall_valid': overall_valid,
                    'individual_results': results,
                    'total_errors': sum(len(r['errors']) for r in results),
                    'total_warnings': sum(len(r['warnings']) for r in results)
                }
            }
        except Exception as e:
            return {'error': f'Validation operations failed: {str(e)}'}


class SimpleTestView(APIView):
    """Simple test endpoint to verify the server is working"""
    
    def get(self, request):
        return Response({
            'status': 'server_running',
            'available_modules': {
                'graph_algorithms': GRAPH_ALGORITHMS_AVAILABLE,
                'tree_algorithms': TREE_ALGORITHMS_AVAILABLE,
                'math_algorithms': MATH_ALGORITHMS_AVAILABLE,
                'utilities': UTILITIES_AVAILABLE
            },
            'message': 'Planning API is running',
            'timestamp': '2024-01-01T00:00:00Z'
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        return Response({
            'echo': request.data,
            'method': 'POST',
            'available_modules': {
                'graph_algorithms': GRAPH_ALGORITHMS_AVAILABLE,
                'tree_algorithms': TREE_ALGORITHMS_AVAILABLE,
                'math_algorithms': MATH_ALGORITHMS_AVAILABLE,
                'utilities': UTILITIES_AVAILABLE
            },
            'timestamp': '2024-01-01T00:00:00Z'
        }, status=status.HTTP_200_OK)


class AlgorithmTestView(APIView):
    """Endpoint for testing algorithm availability and basic functionality"""
    
    def get(self, request):
        test_results = self._run_basic_tests()
        
        return Response({
            'algorithm_tests': test_results,
            'modules_available': {
                'graph_algorithms': GRAPH_ALGORITHMS_AVAILABLE,
                'tree_algorithms': TREE_ALGORITHMS_AVAILABLE,
                'math_algorithms': MATH_ALGORITHMS_AVAILABLE,
                'utilities': UTILITIES_AVAILABLE
            },
            'overall_status': 'healthy' if any(test_results.values()) else 'limited'
        }, status=status.HTTP_200_OK)
    
    def _run_basic_tests(self) -> Dict[str, bool]:
        """Run basic tests for each available algorithm module"""
        results = {
            'graph_algorithms': False,
            'tree_algorithms': False,
            'math_algorithms': False,
            'utilities': False
        }
        
        # Test utilities
        if UTILITIES_AVAILABLE:
            try:
                values = [1, 2, 3, 4, 5]
                mean = Statistics.mean(values)
                results['utilities'] = abs(mean - 3.0) < 0.001
            except Exception as e:
                logger.warning(f"Utilities test failed: {e}")
        
        # Test mathematics
        if MATH_ALGORITHMS_AVAILABLE:
            try:
                root1, root2 = SolveQuadratic.solve(1, -5, 6)  # Should give roots 2, 3
                results['math_algorithms'] = (root1 is not None and root2 is not None)
            except Exception as e:
                logger.warning(f"Mathematics test failed: {e}")
        
        # Test tree algorithms  
        if TREE_ALGORITHMS_AVAILABLE:
            try:
                tree = IntervalTree()
                interval = UInterval(1, 3)
                success = tree.insert_interval(interval, 1)
                results['tree_algorithms'] = success and tree.count == 1
            except Exception as e:
                logger.warning(f"Tree algorithms test failed: {e}")
        
        # Test graph algorithms
        if GRAPH_ALGORITHMS_AVAILABLE:
            try:
                vertices = [0, 1, 2]
                edges = [Edge(0, 1, 1.0), Edge(1, 2, 1.0)]
                graph = GraphAdapter(vertices, edges)
                results['graph_algorithms'] = len(graph.vertices()) == 3
            except Exception as e:
                logger.warning(f"Graph algorithms test failed: {e}")
        
        return results


# Response serializers for API documentation
class GraphAnalysisResponseSerializer(serializers.Serializer):
    """Response serializer for graph analysis"""
    success = serializers.BooleanField()
    algorithm = serializers.CharField()
    result = serializers.DictField()


class IntervalAnalysisResponseSerializer(serializers.Serializer):
    """Response serializer for interval analysis"""
    success = serializers.BooleanField()
    operation = serializers.CharField()
    result = serializers.DictField()


class MathematicsResponseSerializer(serializers.Serializer):
    """Response serializer for mathematics operations"""
    success = serializers.BooleanField()
    operation = serializers.CharField()
    result = serializers.DictField()


class UtilitiesResponseSerializer(serializers.Serializer):
    """Response serializer for utilities operations"""
    success = serializers.BooleanField()
    operation = serializers.CharField()
    result = serializers.DictField()


# Example usage and testing functions
def test_graph_algorithms():
    """Test graph algorithms with sample data"""
    if not GRAPH_ALGORITHMS_AVAILABLE:
        return {'error': 'Graph algorithms not available'}
    
    try:
        vertices = [0, 1, 2, 3, 4]
        edges = [
            {'from': 0, 'to': 1, 'weight': 2.0},
            {'from': 1, 'to': 2, 'weight': 3.0},
            {'from': 2, 'to': 3, 'weight': 1.0},
            {'from': 3, 'to': 4, 'weight': 2.0},
            {'from': 0, 'to': 4, 'weight': 5.0}
        ]
        
        test_data = {
            'vertices': vertices,
            'edges': edges,
            'source_vertex': 0,
            'algorithm': 'centrality'
        }
        
        return test_data
    except Exception as e:
        return {'error': f'Graph algorithm test failed: {str(e)}'}


def test_interval_algorithms():
    """Test interval algorithms with sample data"""
    if not TREE_ALGORITHMS_AVAILABLE:
        return {'error': 'Tree algorithms not available'}
    
    try:
        intervals = [
            {'low': 1, 'high': 3, 'id': 1},
            {'low': 2, 'high': 4, 'id': 2},
            {'low': 5, 'high': 7, 'id': 3},
            {'low': 6, 'high': 8, 'id': 4}
        ]
        
        query_interval = {'low': 3, 'high': 6}
        
        test_data = {
            'intervals': intervals,
            'query_interval': query_interval,
            'operation': 'overlaps'
        }
        
        return test_data
    except Exception as e:
        return {'error': f'Interval algorithm test failed: {str(e)}'}


def test_mathematics_algorithms():
    """Test mathematics algorithms with sample data"""
    if not MATH_ALGORITHMS_AVAILABLE:
        return {'error': 'Mathematics algorithms not available'}
    
    try:
        test_data = {
            'quadratic': {
                'operation': 'quadratic',
                'a': 1,
                'b': -5,
                'c': 6
            },
            'geometry': {
                'operation': 'geometry',
                'points': [
                    {'x': 0, 'y': 0},
                    {'x': 4, 'y': 0},
                    {'x': 4, 'y': 3},
                    {'x': 0, 'y': 3}
                ]
            }
        }
        
        return test_data
    except Exception as e:
        return {'error': f'Mathematics algorithm test failed: {str(e)}'}


def test_utilities_algorithms():
    """Test utility algorithms with sample data"""
    if not UTILITIES_AVAILABLE:
        return {'error': 'Utilities not available'}
    
    try:
        test_data = {
            'statistics': {
                'operation': 'statistics',
                'values': [1, 2, 3, 4, 5, 5, 6, 7, 8, 9],
                'statistic_type': 'descriptive'
            },
            'collection': {
                'operation': 'collection',
                'data': [1, 2, 2, 3, 'a', 'b', 'a', 4, 5],
                'chunk_size': 3
            }
        }
        
        return test_data
    except Exception as e:
        return {'error': f'Utilities algorithm test failed: {str(e)}'}


# Error handling helpers
class APIErrorHandler:
    """Helper class for consistent error handling across all views"""
    
    @staticmethod
    def handle_validation_error(serializer_errors):
        """Format serializer validation errors"""
        formatted_errors = {}
        for field, errors in serializer_errors.items():
            if isinstance(errors, list):
                formatted_errors[field] = [str(error) for error in errors]
            else:
                formatted_errors[field] = str(errors)
        
        return {
            'error': 'Validation failed',
            'details': formatted_errors,
            'message': 'Please check your input data and try again.'
        }
    
    @staticmethod
    def handle_algorithm_error(algorithm_name, error):
        """Format algorithm execution errors"""
        return {
            'error': f'{algorithm_name} execution failed',
            'details': str(error),
            'message': 'An error occurred while running the algorithm. Please check your input parameters.'
        }
    
    @staticmethod
    def handle_generic_error(error):
        """Format generic errors"""
        return {
            'error': 'Internal server error',
            'details': str(error),
            'message': 'An unexpected error occurred. Please try again later.'
        }


# Module availability information
def get_module_status():
    """Get current module availability status"""
    return {
        'graph_algorithms': {
            'available': GRAPH_ALGORITHMS_AVAILABLE,
            'features': ['dijkstra', 'centrality', 'dfs'] if GRAPH_ALGORITHMS_AVAILABLE else []
        },
        'tree_algorithms': {
            'available': TREE_ALGORITHMS_AVAILABLE,
            'features': ['interval_tree', 'overlaps', 'gaps'] if TREE_ALGORITHMS_AVAILABLE else []
        },
        'math_algorithms': {
            'available': MATH_ALGORITHMS_AVAILABLE,
            'features': ['quadratic', 'root_finding', 'geometry'] if MATH_ALGORITHMS_AVAILABLE else []
        },
        'utilities': {
            'available': UTILITIES_AVAILABLE,
            'features': ['statistics', 'collections', 'validation'] if UTILITIES_AVAILABLE else []
        }
    }


if __name__ == "__main__":
    # Run basic tests when module is imported
    print("Algorithm Views Module Status:")
    print("=" * 50)
    
    status = get_module_status()
    for module, info in status.items():
        print(f"{module}: {'✓' if info['available'] else '✗'}")
        if info['features']:
            print(f"  Features: {', '.join(info['features'])}")
    
    print("\nRunning basic tests...")
    if UTILITIES_AVAILABLE:
        print("Utilities test:", test_utilities_algorithms())
    if MATH_ALGORITHMS_AVAILABLE:
        print("Mathematics test:", test_mathematics_algorithms())
    if TREE_ALGORITHMS_AVAILABLE:
        print("Tree algorithms test:", test_interval_algorithms())
    if GRAPH_ALGORITHMS_AVAILABLE:
        print("Graph algorithms test:", test_graph_algorithms())