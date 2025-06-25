# planning_api/clustering_views.py - New views for clustering functionality
import logging
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .geometry.clustering import AgglomerativeClustering, Point3D, Cluster
from .geometry.geometry3d import UPoint, UPolyline, PolylineSnapper3D
from .geometry.voronoi import Voronoi, FortuneSite, VPoint
from .serializers import (
    GeometryValidationSerializer, 
    OffsetOperationSerializer,
    IntersectionTestSerializer
)

logger = logging.getLogger(__name__)


class ClusteringAnalysisView(APIView):
    """Analyze building positions using hierarchical clustering"""
    
    def post(self, request):
        try:
            data = request.data
            vertices = data.get('vertices', [])
            cluster_diameter = data.get('cluster_diameter', 50.0)
            
            if len(vertices) < 9:
                return Response(
                    {'error': 'At least 3 vertices required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert vertices to points
            points = []
            coordinates = np.zeros((len(vertices) // 3, 3))
            
            for i in range(0, len(vertices), 3):
                point = Point3D(vertices[i], vertices[i + 1], vertices[i + 2])
                points.append(point)
                coordinates[i // 3] = [vertices[i], vertices[i + 1], vertices[i + 2]]
            
            # Create distance matrix
            n = len(points)
            distance_matrix = np.zeros((n, n))
            
            for i in range(n):
                for j in range(n):
                    if i != j:
                        distance_matrix[i, j] = points[i].distance_to(points[j])
            
            # Apply clustering
            clusters = AgglomerativeClustering.run(
                distance_matrix, cluster_diameter, coordinates
            )
            
            # Convert results
            cluster_results = []
            for cluster in clusters:
                cluster_results.append({
                    'id': cluster.id,
                    'centroid': {
                        'x': cluster.centroid.x,
                        'y': cluster.centroid.y,
                        'z': cluster.centroid.z
                    },
                    'diameter': cluster.diameter,
                    'member_count': cluster.count,
                    'members': cluster.children
                })
            
            return Response({
                'success': True,
                'cluster_count': len(cluster_results),
                'clusters': cluster_results,
                'original_points': len(points),
                'cluster_diameter': cluster_diameter
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Clustering analysis failed: {str(e)}")
            return Response(
                {'error': f'Clustering analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VoronoiGenerationView(APIView):
    """Generate Voronoi diagram for site analysis"""
    
    def post(self, request):
        try:
            data = request.data
            site_vertices = data.get('site_vertices', [])
            seed_points = data.get('seed_points', [])
            seed_count = data.get('seed_count', 10)
            
            if len(site_vertices) < 9:
                return Response(
                    {'error': 'Site boundary requires at least 3 vertices'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate site bounds
            min_x = min(site_vertices[i] for i in range(0, len(site_vertices), 3))
            max_x = max(site_vertices[i] for i in range(0, len(site_vertices), 3))
            min_y = min(site_vertices[i + 1] for i in range(0, len(site_vertices), 3))
            max_y = max(site_vertices[i + 1] for i in range(0, len(site_vertices), 3))
            
            # Generate or use provided seed points
            sites = []
            if seed_points:
                for i in range(0, len(seed_points), 3):
                    if i + 1 < len(seed_points):
                        sites.append(FortuneSite(seed_points[i], seed_points[i + 1], []))
            else:
                # Generate random seed points within bounds
                import random
                margin = 10.0
                
                for _ in range(seed_count):
                    x = random.uniform(min_x + margin, max_x - margin)
                    y = random.uniform(min_y + margin, max_y - margin)
                    sites.append(FortuneSite(x, y, []))
            
            # Generate Voronoi diagram
            voronoi = Voronoi(sites, min_x, min_y, max_x, max_y)
            
            # Convert results
            voronoi_cells = []
            for site in voronoi.sites:
                cell_vertices = []
                for point in site.cell:
                    cell_vertices.extend([point.x, point.y, 0])
                
                # Calculate cell area
                cell_area = 0
                if len(cell_vertices) >= 9:
                    for i in range(0, len(cell_vertices) - 3, 3):
                        j = (i + 3) % (len(cell_vertices) - 3)
                        cell_area += cell_vertices[i] * cell_vertices[j + 1]
                        cell_area -= cell_vertices[j] * cell_vertices[i + 1]
                    cell_area = abs(cell_area) / 2
                
                voronoi_cells.append({
                    'site': {'x': site.x, 'y': site.y},
                    'vertices': cell_vertices,
                    'area': cell_area,
                    'vertex_count': len(cell_vertices) // 3
                })
            
            return Response({
                'success': True,
                'cells': voronoi_cells,
                'site_count': len(sites),
                'bounds': {
                    'min_x': min_x, 'max_x': max_x,
                    'min_y': min_y, 'max_y': max_y
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Voronoi generation failed: {str(e)}")
            return Response(
                {'error': f'Voronoi generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BuildingDistributionView(APIView):
    """Analyze and optimize building distribution"""
    
    def post(self, request):
        try:
            data = request.data
            site_vertices = data.get('site_vertices', [])
            building_positions = data.get('building_positions', [])
            target_density = data.get('target_density', 0.5)
            min_spacing = data.get('min_spacing', 5.0)
            
            if len(site_vertices) < 9:
                return Response(
                    {'error': 'Site boundary requires at least 3 vertices'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate site area
            site_area = self._calculate_polygon_area(site_vertices)
            
            # Analyze current distribution if positions provided
            current_analysis = None
            if building_positions:
                current_analysis = self._analyze_distribution(
                    building_positions, site_area, min_spacing
                )
            
            # Generate optimized distribution
            optimized_positions = self._generate_optimized_distribution(
                site_vertices, site_area, target_density, min_spacing
            )
            
            optimized_analysis = self._analyze_distribution(
                optimized_positions, site_area, min_spacing
            )
            
            return Response({
                'success': True,
                'site_area': site_area,
                'target_density': target_density,
                'current_analysis': current_analysis,
                'optimized_positions': optimized_positions,
                'optimized_analysis': optimized_analysis,
                'improvement_metrics': self._calculate_improvements(
                    current_analysis, optimized_analysis
                ) if current_analysis else None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Building distribution analysis failed: {str(e)}")
            return Response(
                {'error': f'Building distribution analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_polygon_area(self, vertices):
        """Calculate polygon area using shoelace formula"""
        if len(vertices) < 9:
            return 0
        
        area = 0
        for i in range(0, len(vertices), 3):
            j = (i + 3) % len(vertices)
            if j + 1 < len(vertices):
                area += vertices[i] * vertices[j + 1]
                area -= vertices[j] * vertices[i + 1]
        
        return abs(area) / 2
    
    def _analyze_distribution(self, positions, site_area, min_spacing):
        """Analyze building position distribution"""
        if not positions or len(positions) < 3:
            return None
        
        building_count = len(positions) // 3
        
        # Calculate distances between buildings
        distances = []
        for i in range(0, len(positions), 3):
            for j in range(i + 3, len(positions), 3):
                if j + 2 < len(positions):
                    dx = positions[i] - positions[j]
                    dy = positions[i + 1] - positions[j + 1]
                    distance = (dx * dx + dy * dy) ** 0.5
                    distances.append(distance)
        
        # Calculate metrics
        avg_distance = sum(distances) / len(distances) if distances else 0
        min_distance = min(distances) if distances else 0
        max_distance = max(distances) if distances else 0
        
        # Calculate coverage
        building_footprint = 200  # Assumed average building footprint
        total_building_area = building_count * building_footprint
        coverage_ratio = total_building_area / site_area if site_area > 0 else 0
        
        # Check spacing violations
        spacing_violations = sum(1 for d in distances if d < min_spacing)
        
        return {
            'building_count': building_count,
            'avg_distance': round(avg_distance, 2),
            'min_distance': round(min_distance, 2),
            'max_distance': round(max_distance, 2),
            'coverage_ratio': round(coverage_ratio, 3),
            'spacing_violations': spacing_violations,
            'distribution_quality': self._calculate_distribution_quality(
                distances, min_spacing, coverage_ratio
            )
        }
    
    def _generate_optimized_distribution(self, site_vertices, site_area, density, min_spacing):
        """Generate optimized building positions"""
        import random
        
        # Calculate bounds
        min_x = min(site_vertices[i] for i in range(0, len(site_vertices), 3))
        max_x = max(site_vertices[i] for i in range(0, len(site_vertices), 3))
        min_y = min(site_vertices[i + 1] for i in range(0, len(site_vertices), 3))
        max_y = max(site_vertices[i + 1] for i in range(0, len(site_vertices), 3))
        
        # Calculate target building count
        building_footprint = 200
        target_buildings = int(site_area * density / building_footprint)
        target_buildings = max(5, min(100, target_buildings))
        
        # Generate positions using improved algorithm
        positions = []
        max_attempts = target_buildings * 50
        attempts = 0
        
        while len(positions) < target_buildings * 3 and attempts < max_attempts:
            x = random.uniform(min_x + 10, max_x - 10)
            y = random.uniform(min_y + 10, max_y - 10)
            
            # Check if point is inside polygon
            if self._point_in_polygon([x, y], site_vertices):
                # Check minimum distance constraint
                valid = True
                for i in range(0, len(positions), 3):
                    dx = x - positions[i]
                    dy = y - positions[i + 1]
                    distance = (dx * dx + dy * dy) ** 0.5
                    
                    if distance < min_spacing:
                        valid = False
                        break
                
                if valid:
                    positions.extend([x, y, 0])
            
            attempts += 1
        
        return positions
    
    def _point_in_polygon(self, point, polygon_vertices):
        """Check if point is inside polygon using ray casting"""
        x, y = point
        inside = False
        
        for i in range(0, len(polygon_vertices), 3):
            j = (i + 3) % len(polygon_vertices)
            if j + 1 < len(polygon_vertices):
                xi, yi = polygon_vertices[i], polygon_vertices[i + 1]
                xj, yj = polygon_vertices[j], polygon_vertices[j + 1]
                
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                    inside = not inside
        
        return inside
    
    def _calculate_distribution_quality(self, distances, min_spacing, coverage_ratio):
        """Calculate overall distribution quality score"""
        if not distances:
            return 0
        
        # Spacing quality (0-40 points)
        spacing_violations = sum(1 for d in distances if d < min_spacing)
        spacing_score = max(0, 40 - spacing_violations * 10)
        
        # Uniformity quality (0-30 points)
        avg_distance = sum(distances) / len(distances)
        variance = sum((d - avg_distance) ** 2 for d in distances) / len(distances)
        uniformity_score = max(0, 30 - variance / 100)
        
        # Coverage quality (0-30 points)
        optimal_coverage = 0.6
        coverage_diff = abs(coverage_ratio - optimal_coverage)
        coverage_score = max(0, 30 - coverage_diff * 100)
        
        total_score = spacing_score + uniformity_score + coverage_score
        return round(total_score, 1)
    
    def _calculate_improvements(self, current, optimized):
        """Calculate improvement metrics"""
        if not current or not optimized:
            return None
        
        return {
            'building_count_change': optimized['building_count'] - current['building_count'],
            'avg_distance_change': round(optimized['avg_distance'] - current['avg_distance'], 2),
            'quality_improvement': round(optimized['distribution_quality'] - current['distribution_quality'], 1),
            'spacing_violations_reduced': current['spacing_violations'] - optimized['spacing_violations'],
            'coverage_improvement': round(optimized['coverage_ratio'] - current['coverage_ratio'], 3)
        }


class GeometryProcessingView(APIView):
    """Enhanced geometry processing with 3D operations"""
    
    def post(self, request):
        try:
            data = request.data
            operation = data.get('operation', 'snap')
            vertices = data.get('vertices', [])
            tolerance = data.get('tolerance', 1e-6)
            
            if len(vertices) < 9:
                return Response(
                    {'error': 'At least 3 vertices required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if operation == 'snap':
                result = self._perform_snapping(vertices, tolerance)
            elif operation == 'intersect':
                vertices_b = data.get('vertices_b', [])
                result = self._perform_intersection(vertices, vertices_b, tolerance)
            elif operation == 'reduce_precision':
                decimal_places = data.get('decimal_places', 6)
                result = self._reduce_precision(vertices, decimal_places)
            else:
                return Response(
                    {'error': f'Unknown operation: {operation}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Geometry processing failed: {str(e)}")
            return Response(
                {'error': f'Geometry processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _perform_snapping(self, vertices, tolerance):
        """Perform endpoint snapping"""
        # Convert to UPoint objects
        points = []
        for i in range(0, len(vertices), 3):
            points.append(UPoint(vertices[i], vertices[i + 1], vertices[i + 2]))
        
        # Create polyline
        polyline = UPolyline(points)
        
        # Apply snapping
        snapper = PolylineSnapper3D([polyline], tolerance)
        snapper.snap()
        
        # Convert back to flattened vertices
        snapped_vertices = []
        for point in snapper.get_snapped_polylines()[0].coordinates:
            snapped_vertices.extend([point.x, point.y, point.z])
        
        return {
            'success': True,
            'operation': 'snap',
            'original_vertices': vertices,
            'snapped_vertices': snapped_vertices,
            'tolerance': tolerance
        }
    
    def _perform_intersection(self, vertices_a, vertices_b, tolerance):
        """Perform line intersection analysis"""
        from .geometry.geometry3d import LinesIntersection3D
        
        if len(vertices_a) < 6 or len(vertices_b) < 6:
            return {'success': False, 'error': 'Each line needs at least 2 points'}
        
        # Create line segments
        p1 = UPoint(vertices_a[0], vertices_a[1], vertices_a[2])
        p2 = UPoint(vertices_a[3], vertices_a[4], vertices_a[5])
        q1 = UPoint(vertices_b[0], vertices_b[1], vertices_b[2])
        q2 = UPoint(vertices_b[3], vertices_b[4], vertices_b[5])
        
        # Calculate intersection
        intersection = LinesIntersection3D(tolerance)
        has_intersection = intersection.compute(p1, p2, q1, q2)
        
        result = {
            'success': True,
            'operation': 'intersect',
            'has_intersection': has_intersection,
            'is_parallel': intersection.is_parallel,
            'is_collinear': intersection.is_collinear,
            'is_proper': intersection.is_proper,
            'tolerance': tolerance
        }
        
        if has_intersection:
            result['p_intersections'] = [
                [p.x, p.y, p.z] for p in intersection.p_intersections
            ]
            result['q_intersections'] = [
                [q.x, q.y, q.z] for q in intersection.q_intersections
            ]
        
        return result
    
    def _reduce_precision(self, vertices, decimal_places):
        """Reduce coordinate precision"""
        reduced_vertices = []
        for vertex in vertices:
            reduced_vertices.append(round(vertex, decimal_places))
        
        return {
            'success': True,
            'operation': 'reduce_precision',
            'original_vertices': vertices,
            'reduced_vertices': reduced_vertices,
            'decimal_places': decimal_places
        }