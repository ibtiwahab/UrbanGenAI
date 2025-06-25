# planning_api/algorithms_views.py
"""
Django views integrating the converted C# algorithms
"""

import logging
import json
from typing import List, Dict, Any, Tuple
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

# Import our converted algorithms
from .algorithms.graph_algorithms import (
    DijkstraShortestPaths, CalculateCentrality, DepthFirstSearch,
    GraphAdapter, Edge, DirectedEdge, EdgeWeightedGraph, EdgeWeightedDigraph
)
from .algorithms.trees import IntervalTree, UInterval, IntervalNode, IntervalTreeOperations
from .algorithms.mathematics import (
    RootFinding, SolveQuadratic, Parabola, GeometryMath, Point2D, Vector2D
)
from .algorithms.utilities import (
    Statistics, MathUtilities, CollectionUtilities, ListExtensions, Validators
)

logger = logging.getLogger(__name__)


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
    
    def _run_dijkstra(self, graph: GraphAdapter, source: int) -> Dict[str, Any]:
        """Run Dijkstra's shortest path algorithm"""
        dijkstra = DijkstraShortestPaths(graph, source)
        
        result = {
            'source': source,
            'distances': {},
            'paths': {}
        }
        
        for vertex in graph.vertices():
            if dijkstra.has_path_to(vertex):
                result['distances'][vertex] = dijkstra.distance_to(vertex)
                result['paths'][vertex] = dijkstra.shortest_path_to(vertex)
            else:
                result['distances'][vertex] = float('inf')
                result['paths'][vertex] = None
        
        return result
    
    def _run_centrality(self, graph: GraphAdapter, radius: float) -> Dict[str, Any]:
        """Run centrality calculation"""
        centrality = CalculateCentrality(graph, radius)
        
        result = {
            'betweenness': {str(k): v for k, v in centrality.betweenness.items()},
            'total_depths': {str(k): v for k, v in centrality.total_depths.items()},
            'node_counts': {str(k): v for k, v in centrality.node_counts.items()},
            'radius': radius
        }
        
        return result
    
    def _run_dfs(self, graph: GraphAdapter) -> Dict[str, Any]:
        """Run depth-first search to find connected components"""
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


class IntervalAnalysisView(APIView):
    """Interval tree analysis endpoint"""
    
    def post(self, request):
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
                interval = UInterval(interval_data['low'], interval_data['high'])
                intervals.append((interval, interval_data['id']))
            
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
        
        # Calculate discriminant
        discriminant = b*b - 4*a*c
        
        if a == 0:
            # Linear equation
            if b == 0:
                if c == 0:
                    return {
                        'equation': f"{a}x² + {b}x + {c} = 0",
                        'success': True,
                        'roots': 'infinite',
                        'discriminant': None,
                        'type': 'degenerate'
                    }
                else:
                    return {
                        'equation': f"{a}x² + {b}x + {c} = 0",
                        'success': False,
                        'roots': None,
                        'discriminant': None,
                        'type': 'no_solution'
                    }
            else:
                root = -c / b
                return {
                    'equation': f"{b}x + {c} = 0",
                    'success': True,
                    'roots': [root],
                    'discriminant': None,
                    'type': 'linear'
                }
        
        # Quadratic equation
        if discriminant > 0:
            # Two real roots
            sqrt_disc = discriminant ** 0.5
            root1 = (-b + sqrt_disc) / (2 * a)
            root2 = (-b - sqrt_disc) / (2 * a)
            roots = [root1, root2]
            equation_type = 'two_real_roots'
        elif discriminant == 0:
            # One real root (repeated)
            root = -b / (2 * a)
            roots = [root]
            equation_type = 'one_real_root'
        else:
            # Complex roots
            real_part = -b / (2 * a)
            imag_part = (-discriminant) ** 0.5 / (2 * a)
            roots = [
                {'real': real_part, 'imaginary': imag_part},
                {'real': real_part, 'imaginary': -imag_part}
            ]
            equation_type = 'complex_roots'
        
        return {
            'equation': f"{a}x² + {b}x + {c} = 0",
            'success': True,
            'roots': roots,
            'discriminant': discriminant,
            'type': equation_type
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
            # Simple bisection method implementation
            def bisection(func, a, b, tol):
                if func(a) * func(b) >= 0:
                    raise ValueError("Function values at bounds must have opposite signs")
                
                iterations = 0
                while abs(b - a) > tol and iterations < 1000:
                    c = (a + b) / 2
                    if func(c) == 0:
                        return c, iterations
                    elif func(a) * func(c) < 0:
                        b = c
                    else:
                        a = c
                    iterations += 1
                
                return (a + b) / 2, iterations
            
            # Try to find root using bisection
            try:
                root_bisect, iter_bisect = bisection(polynomial, left, right, tolerance)
                error_bisect = abs(polynomial(root_bisect))
            except ValueError as e:
                root_bisect = None
                iter_bisect = 0
                error_bisect = float('inf')
            
            return {
                'polynomial_coefficients': coefficients,
                'search_interval': [left, right],
                'bisection': {
                    'root': root_bisect,
                    'iterations': iter_bisect,
                    'error': error_bisect,
                    'success': root_bisect is not None
                }
            }
            
        except ValueError as e:
            return {
                'error': str(e),
                'polynomial_coefficients': coefficients,
                'search_interval': [left, right]
            }
    
    def _linear_regression(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform linear regression"""
        x_values = data.get('x_values', [])
        y_values = data.get('y_values', [])
        
        if len(x_values) != len(y_values):
            raise ValueError("x_values and y_values must have the same length")
        
        if len(x_values) < 2:
            raise ValueError("At least 2 data points required for regression")
        
        r_squared, y_intercept, slope = Statistics.linear_regression(x_values, y_values)
        
        # Calculate correlation coefficient
        correlation = Statistics.correlation_coefficient(x_values, y_values)
        
        # Generate predictions
        predictions = [slope * x + y_intercept for x in x_values]
        
        # Calculate residuals
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
    
    def _geometry_calculations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform geometry calculations"""
        points_data = data.get('points', [])
        
        if len(points_data) < 3:
            raise ValueError("At least 3 points required for polygon calculations")
        
        # Convert to Point2D objects (mock implementation since we don't have the full geometry module)
        points = []
        for point_data in points_data:
            # Simple point class for this example
            class SimplePoint:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y
                
                def distance_to(self, other):
                    return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
            
            point = SimplePoint(point_data['x'], point_data['y'])
            points.append(point)
        
        # Calculate polygon area using shoelace formula
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i].x * points[j].y
            area -= points[j].x * points[i].y
        area = abs(area) / 2.0
        
        # Calculate centroid
        cx = sum(p.x for p in points) / len(points)
        cy = sum(p.y for p in points) / len(points)
        
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
                'centroid': {'x': cx, 'y': cy}
            },
            'input_points': [{'x': p.x, 'y': p.y} for p in points]
        }


class UtilitiesView(APIView):
    """Utilities and statistical analysis endpoint"""
    
    def post(self, request):
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
            raise ValueError("Values list cannot be empty")
        
        if statistic_type == 'descriptive':
            # Basic descriptive statistics
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
    
    def _collection_operations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform collection operations"""
        collection_data = data.get('data', [])
        chunk_size = data.get('chunk_size', 3)
        
        if not collection_data:
            raise ValueError("Data list cannot be empty")
        
        # Perform various collection operations
        chunks = CollectionUtilities.chunk(collection_data, chunk_size)
        unique_values = CollectionUtilities.unique(collection_data)
        
        # Group by value type
        grouped = CollectionUtilities.group_by(
            collection_data, 
            lambda x: type(x).__name__
        )
        
        # Partition by numeric/non-numeric
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
    
    def _validation_operations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform validation operations"""
        rules = data.get('validation_rules', {})
        
        # Example validation based on rules
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


# URL patterns for including in planning_api/urls.py
"""
Updated URL patterns to include algorithm endpoints

Add these to your main urls.py:

from django.urls import path, include
from .algorithms_views import (
    GraphAnalysisView, IntervalAnalysisView, 
    MathematicsView, UtilitiesView
)

algorithm_urlpatterns = [
    # Graph algorithms
    path('algorithms/graph/analysis/', GraphAnalysisView.as_view(), name='graph_analysis'),
    
    # Interval tree algorithms  
    path('algorithms/intervals/analysis/', IntervalAnalysisView.as_view(), name='interval_analysis'),
    
    # Mathematics algorithms
    path('algorithms/mathematics/', MathematicsView.as_view(), name='mathematics'),
    
    # Utilities and statistics
    path('algorithms/utilities/', UtilitiesView.as_view(), name='utilities'),
]

# Include in main urlpatterns
urlpatterns = [
    # ... your existing patterns
] + algorithm_urlpatterns
"""


# Example usage and testing functions
def test_graph_algorithms():
    """Test graph algorithms with sample data"""
    # Create test graph
    vertices = [0, 1, 2, 3, 4]
    edges = [
        {'from': 0, 'to': 1, 'weight': 2.0},
        {'from': 1, 'to': 2, 'weight': 3.0},
        {'from': 2, 'to': 3, 'weight': 1.0},
        {'from': 3, 'to': 4, 'weight': 2.0},
        {'from': 0, 'to': 4, 'weight': 5.0}
    ]
    
    print("Graph Analysis Test:")
    print(f"Vertices: {vertices}")
    print(f"Edges: {edges}")
    
    # Test data for API call
    test_data = {
        'vertices': vertices,
        'edges': edges,
        'source_vertex': 0,
        'algorithm': 'centrality'
    }
    
    print(f"Test request data: {test_data}")
    return test_data


def test_interval_algorithms():
    """Test interval algorithms with sample data"""
    intervals = [
        {'low': 1, 'high': 3, 'id': 1},
        {'low': 2, 'high': 4, 'id': 2},
        {'low': 5, 'high': 7, 'id': 3},
        {'low': 6, 'high': 8, 'id': 4}
    ]
    
    query_interval = {'low': 3, 'high': 6}
    
    print("Interval Analysis Test:")
    print(f"Intervals: {intervals}")
    print(f"Query interval: {query_interval}")
    
    test_data = {
        'intervals': intervals,
        'query_interval': query_interval,
        'operation': 'overlaps'
    }
    
    print(f"Test request data: {test_data}")
    return test_data


def test_mathematics_algorithms():
    """Test mathematics algorithms with sample data"""
    # Quadratic equation test
    quadratic_data = {
        'operation': 'quadratic',
        'a': 1,
        'b': -5,
        'c': 6
    }
    
    # Linear regression test
    regression_data = {
        'operation': 'linear_regression',
        'x_values': [1, 2, 3, 4, 5],
        'y_values': [2, 4, 6, 8, 10]
    }
    
    # Root finding test
    root_finding_data = {
        'operation': 'root_finding',
        'coefficients': [1, 0, -4],  # x² - 4 = 0, roots at ±2
        'left_bound': -5,
        'right_bound': 5,
        'tolerance': 1e-6
    }
    
    # Geometry test
    geometry_data = {
        'operation': 'geometry',
        'points': [
            {'x': 0, 'y': 0},
            {'x': 4, 'y': 0},
            {'x': 4, 'y': 3},
            {'x': 0, 'y': 3}
        ]
    }
    
    print("Mathematics Test:")
    print(f"Quadratic test: {quadratic_data}")
    print(f"Regression test: {regression_data}")
    print(f"Root finding test: {root_finding_data}")
    print(f"Geometry test: {geometry_data}")
    
    return {
        'quadratic': quadratic_data,
        'regression': regression_data,
        'root_finding': root_finding_data,
        'geometry': geometry_data
    }


def test_utilities_algorithms():
    """Test utility algorithms with sample data"""
    # Statistics test
    stats_data = {
        'operation': 'statistics',
        'values': [1, 2, 3, 4, 5, 5, 6, 7, 8, 9],
        'statistic_type': 'descriptive'
    }
    
    # Collection operations test
    collection_data = {
        'operation': 'collection',
        'data': [1, 2, 2, 3, 'a', 'b', 'a', 4, 5],
        'chunk_size': 3
    }
    
    # Validation test
    validation_data = {
        'operation': 'validation',
        'validation_rules': {
            'range_check': {
                'value': 75,
                'min': 0,
                'max': 100,
                'name': 'Percentage'
            },
            'positive_check': {
                'value': 42,
                'name': 'Age'
            }
        }
    }
    
    print("Utilities Test:")
    print(f"Statistics test: {stats_data}")
    print(f"Collection test: {collection_data}")
    print(f"Validation test: {validation_data}")
    
    return {
        'statistics': stats_data,
        'collection': collection_data,
        'validation': validation_data
    }


# API Usage Examples
class APIUsageExamples:
    """
    Examples of how to use the algorithm APIs
    """
    
    @staticmethod
    def graph_analysis_example():
        """Example of graph analysis API usage"""
        import requests
        
        # Example request for centrality analysis
        url = "http://localhost:8000/api/algorithms/graph/analysis/"
        
        data = {
            "vertices": [0, 1, 2, 3, 4],
            "edges": [
                {"from": 0, "to": 1, "weight": 2.0},
                {"from": 1, "to": 2, "weight": 3.0},
                {"from": 2, "to": 3, "weight": 1.0},
                {"from": 3, "to": 4, "weight": 2.0},
                {"from": 0, "to": 4, "weight": 5.0}
            ],
            "algorithm": "centrality",
            "radius": 10.0
        }
        
        # Uncomment to make actual request:
        # response = requests.post(url, json=data)
        # print(response.json())
        
        return data
    
    @staticmethod
    def interval_analysis_example():
        """Example of interval analysis API usage"""
        import requests
        
        url = "http://localhost:8000/api/algorithms/intervals/analysis/"
        
        data = {
            "intervals": [
                {"low": 1, "high": 3, "id": 1},
                {"low": 2, "high": 4, "id": 2},
                {"low": 5, "high": 7, "id": 3}
            ],
            "query_interval": {"low": 2.5, "high": 6},
            "operation": "overlaps"
        }
        
        # Uncomment to make actual request:
        # response = requests.post(url, json=data)
        # print(response.json())
        
        return data
    
    @staticmethod
    def mathematics_example():
        """Example of mathematics API usage"""
        import requests
        
        url = "http://localhost:8000/api/algorithms/mathematics/"
        
        # Quadratic equation example
        quadratic_data = {
            "operation": "quadratic",
            "a": 1,
            "b": -5,
            "c": 6
        }
        
        # Linear regression example
        regression_data = {
            "operation": "linear_regression",
            "x_values": [1, 2, 3, 4, 5],
            "y_values": [2, 4, 6, 8, 10]
        }
        
        # Uncomment to make actual requests:
        # response1 = requests.post(url, json=quadratic_data)
        # response2 = requests.post(url, json=regression_data)
        # print("Quadratic:", response1.json())
        # print("Regression:", response2.json())
        
        return {'quadratic': quadratic_data, 'regression': regression_data}
    
    @staticmethod
    def utilities_example():
        """Example of utilities API usage"""
        import requests
        
        url = "http://localhost:8000/api/algorithms/utilities/"
        
        data = {
            "operation": "statistics",
            "values": [1, 2, 3, 4, 5, 5, 6, 7, 8, 9],
            "statistic_type": "descriptive"
        }
        
        # Uncomment to make actual request:
        # response = requests.post(url, json=data)
        # print(response.json())
        
        return data


# Error handling and validation helpers
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


# Performance monitoring decorators
def monitor_performance(algorithm_name):
    """Decorator to monitor algorithm performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(f"{algorithm_name} executed successfully in {execution_time:.3f}s")
                
                # Add performance metrics to result if it's a dict
                if isinstance(result, dict):
                    result['_performance'] = {
                        'execution_time_seconds': execution_time,
                        'algorithm': algorithm_name
                    }
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{algorithm_name} failed after {execution_time:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


if __name__ == "__main__":
    print("Algorithm Integration Tests:")
    print("=" * 50)
    
    # Run all test functions
    test_graph_algorithms()
    print("\n" + "=" * 50)
    test_interval_algorithms()
    print("\n" + "=" * 50)
    test_mathematics_algorithms()
    print("\n" + "=" * 50)
    test_utilities_algorithms()
    
    print("\n" + "=" * 50)
    print("API Usage Examples:")
    print("=" * 50)
    
    # Show API usage examples
    examples = APIUsageExamples()
    print("Graph Analysis Example:", examples.graph_analysis_example())
    print("Interval Analysis Example:", examples.interval_analysis_example())
    print("Mathematics Example:", examples.mathematics_example())
    print("Utilities Example:", examples.utilities_example())