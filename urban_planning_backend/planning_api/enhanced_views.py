# planning_api/enhanced_views.py
import logging
import math
import random
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GeneratePlanRequestSerializer, GeneratePlanResponseSerializer
from .geometry.clustering import (
    AgglomerativeClustering, Point3D, Vector3D, Cluster, MultiClusters
)
from .geometry.geometry3d import (
    UPoint, UVector3, UPolyline, LinesIntersection3D, 
    PolylineSnapper3D, SegmentsIntersection3D
)
from .geometry.voronoi import Voronoi, FortuneSite, VPoint

logger = logging.getLogger(__name__)


class EnhancedSiteParameters:
    """Enhanced site parameters with C# algorithm integration"""
    
    def __init__(self):
        self.site_type = 0
        self.density = 0.5
        self.site_far = 1.0
        self.mix_ratio = 0.0
        self.building_style = 0
        self.radiant = 0.0
        self.site_area = 0.0
        self.site_curve = None
        self.site_polyline = None
        self.site_bounds = None
        
        # Enhanced parameters
        self.min_building_spacing = 5.0
        self.setback_distance = 3.0
        self.use_grid_layout = False
        self.adaptive_orientation = True
        self.max_buildings = 100
        self.use_clustering = True
        self.cluster_diameter = 50.0
        self.use_voronoi = False
        self.building_variation = 0.3
    
    def set_site_from_vertices(self, flattened_vertices):
        """Set site parameters from flattened vertices"""
        if len(flattened_vertices) < 9:
            raise ValueError("Insufficient vertices")
        
        # Convert to UPoint objects
        points = []
        for i in range(0, len(flattened_vertices), 3):
            points.append(UPoint(
                flattened_vertices[i],
                flattened_vertices[i + 1],
                flattened_vertices[i + 2]
            ))
        
        self.site_polyline = UPolyline(points)
        self.site_area = self._calculate_area(points)
        self.radiant = self._calculate_main_orientation(points)
        
        # Calculate bounds
        min_x = min(p.x for p in points)
        max_x = max(p.x for p in points)
        min_y = min(p.y for p in points)
        max_y = max(p.y for p in points)
        
        self.site_bounds = {
            'min_x': min_x, 'max_x': max_x,
            'min_y': min_y, 'max_y': max_y
        }
        
        self.site_curve = [{'x': p.x, 'y': p.y, 'z': p.z} for p in points]
    
    def _calculate_area(self, points):
        """Calculate polygon area using shoelace formula"""
        if len(points) < 3:
            return 0.0
        
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i].x * points[j].y
            area -= points[j].x * points[i].y
        return abs(area) / 2.0
    
    def _calculate_main_orientation(self, points):
        """Calculate main orientation of the polygon"""
        if len(points) < 2:
            return 0.0
        
        max_length = 0.0
        main_angle = 0.0
        
        for i in range(len(points)):
            j = (i + 1) % len(points)
            if j < len(points):
                dx = points[j].x - points[i].x
                dy = points[j].y - points[i].y
                length = math.sqrt(dx*dx + dy*dy)
                
                if length > max_length:
                    max_length = length
                    main_angle = math.atan2(dy, dx)
        
        return main_angle
    
    def update_dependent_parameters(self):
        """Update dependent parameters based on site characteristics"""
        # Update building spacing based on density and site type
        base_spacing = 8.0 if self.site_type in [1, 2] else 6.0  # Commercial/Office vs Residential
        
        if self.density > 0.8:
            self.min_building_spacing = max(3.0, base_spacing * 0.7)
        elif self.density > 0.6:
            self.min_building_spacing = base_spacing * 0.9
        elif self.density < 0.3:
            self.min_building_spacing = base_spacing * 1.5
        else:
            self.min_building_spacing = base_spacing
        
        # Update setback based on FAR and site type
        base_setback = 4.0 if self.site_type in [1, 2] else 3.0
        if self.site_far > 3.0:
            self.setback_distance = max(base_setback, 6.0)
        elif self.site_far > 2.0:
            self.setback_distance = base_setback * 1.2
        else:
            self.setback_distance = base_setback
        
        # Determine clustering parameters
        if self.site_area > 10000:  # Large sites benefit from clustering
            self.use_clustering = True
            self.cluster_diameter = min(100.0, math.sqrt(self.site_area) * 0.8)
        else:
            self.use_clustering = False
        
        # Enable Voronoi for specific scenarios
        self.use_voronoi = (self.site_type == 3 and self.density < 0.4)  # Mixed use, low density
        
        logger.info(f"Updated parameters: spacing={self.min_building_spacing:.1f}, "
                   f"setback={self.setback_distance:.1f}, clustering={self.use_clustering}")


class EnhancedBuildingGenerator:
    """Enhanced building generator using C# algorithms"""
    
    def __init__(self, site_params: EnhancedSiteParameters):
        self.site_params = site_params
        self.building_positions = []
        self.building_dimensions = []
        self.building_heights = []
    
    def generate_buildings(self):
        """Generate buildings using advanced algorithms"""
        if self.site_params.use_clustering:
            return self._generate_clustered_buildings()
        elif self.site_params.use_voronoi:
            return self._generate_voronoi_buildings()
        else:
            return self._generate_grid_buildings()
    
    def _generate_clustered_buildings(self):
        """Generate buildings using hierarchical clustering"""
        logger.info("Generating buildings using hierarchical clustering")
        
        # Generate candidate positions
        candidate_positions = self._generate_candidate_positions()
        
        if len(candidate_positions) < 2:
            return self._generate_grid_buildings()
        
        # Create distance matrix
        n = len(candidate_positions)
        distance_matrix = np.zeros((n, n))
        coordinates = np.zeros((n, 3))
        
        for i, pos_i in enumerate(candidate_positions):
            coordinates[i] = [pos_i.x, pos_i.y, pos_i.z]
            for j, pos_j in enumerate(candidate_positions):
                if i != j:
                    distance_matrix[i, j] = pos_i.distance_to(pos_j)
        
        # Apply clustering
        clusters = AgglomerativeClustering.run(
            distance_matrix, 
            self.site_params.cluster_diameter,
            coordinates
        )
        
        # Generate buildings from clusters
        building_data = []
        for cluster in clusters:
            centroid = cluster.centroid
            cluster_size = cluster.count
            
            # Determine building characteristics based on cluster
            building_width, building_depth = self._get_cluster_building_size(cluster_size)
            floors = self._get_cluster_floors(cluster_size)
            floor_height = self._get_floor_height()
            
            if self._is_position_valid(centroid, building_width, building_depth):
                building_data.append({
                    'position': centroid,
                    'width': building_width,
                    'depth': building_depth,
                    'floors': floors,
                    'floor_height': floor_height
                })
        
        return building_data
    
    def _generate_voronoi_buildings(self):
        """Generate buildings using Voronoi diagrams"""
        logger.info("Generating buildings using Voronoi diagrams")
        
        # Generate seed points
        seed_count = min(20, max(5, int(self.site_params.site_area / 1000)))
        sites = []
        
        bounds = self.site_params.site_bounds
        margin = 10.0
        
        for _ in range(seed_count):
            x = random.uniform(bounds['min_x'] + margin, bounds['max_x'] - margin)
            y = random.uniform(bounds['min_y'] + margin, bounds['max_y'] - margin)
            
            if self._is_point_in_site(UPoint(x, y, 0)):
                sites.append(FortuneSite(x, y, []))
        
        if len(sites) < 3:
            return self._generate_grid_buildings()
        
        # Generate Voronoi diagram
        voronoi = Voronoi(
            sites,
            bounds['min_x'], bounds['min_y'],
            bounds['max_x'], bounds['max_y']
        )
        
        # Generate buildings from Voronoi cells
        building_data = []
        for site in voronoi.sites:
            if len(site.cell) >= 6:  # At least 3 points (2 coordinates each)
                # Calculate cell centroid
                cell_points = []
                for i in range(0, len(site.cell), 2):
                    if i + 1 < len(site.cell):
                        cell_points.append(UPoint(site.cell[i].x, site.cell[i].y, 0))
                
                if cell_points:
                    centroid = self._calculate_centroid(cell_points)
                    cell_area = self._calculate_polygon_area(cell_points)
                    
                    # Size building based on cell area
                    building_width, building_depth = self._get_voronoi_building_size(cell_area)
                    floors = self._get_voronoi_floors(cell_area)
                    floor_height = self._get_floor_height()
                    
                    if self._is_position_valid(centroid, building_width, building_depth):
                        building_data.append({
                            'position': centroid,
                            'width': building_width,
                            'depth': building_depth,
                            'floors': floors,
                            'floor_height': floor_height
                        })
        
        return building_data
    
    def _generate_grid_buildings(self):
        """Generate buildings using enhanced grid with variations"""
        logger.info("Generating buildings using enhanced grid layout")
        
        bounds = self.site_params.site_bounds
        building_data = []
        
        # Calculate optimal grid spacing
        base_width, base_depth = self._get_base_building_dimensions()
        spacing_x = base_width + self.site_params.min_building_spacing
        spacing_y = base_depth + self.site_params.min_building_spacing
        
        # Apply adaptive rotation based on site orientation
        rotation = self.site_params.radiant if self.site_params.adaptive_orientation else 0
        
        # Generate grid with variations
        start_x = bounds['min_x'] + self.site_params.setback_distance
        start_y = bounds['min_y'] + self.site_params.setback_distance
        end_x = bounds['max_x'] - self.site_params.setback_distance
        end_y = bounds['max_y'] - self.site_params.setback_distance
        
        building_count = 0
        max_buildings = min(self.site_params.max_buildings, 50)
        
        y = start_y
        row = 0
        while y < end_y and building_count < max_buildings:
            x = start_x
            col = 0
            
            while x < end_x and building_count < max_buildings:
                # Add variation to position
                variation_x = random.uniform(-spacing_x * 0.2, spacing_x * 0.2) * self.site_params.building_variation
                variation_y = random.uniform(-spacing_y * 0.2, spacing_y * 0.2) * self.site_params.building_variation
                
                pos_x = x + variation_x
                pos_y = y + variation_y
                
                # Apply rotation if needed
                if abs(rotation) > 0.1:
                    center_x = (bounds['min_x'] + bounds['max_x']) / 2
                    center_y = (bounds['min_y'] + bounds['max_y']) / 2
                    
                    # Rotate around site center
                    rel_x = pos_x - center_x
                    rel_y = pos_y - center_y
                    
                    pos_x = center_x + rel_x * math.cos(rotation) - rel_y * math.sin(rotation)
                    pos_y = center_y + rel_x * math.sin(rotation) + rel_y * math.cos(rotation)
                
                position = UPoint(pos_x, pos_y, 0)
                
                # Vary building dimensions
                width_variation = 1.0 + random.uniform(-0.3, 0.3) * self.site_params.building_variation
                depth_variation = 1.0 + random.uniform(-0.3, 0.3) * self.site_params.building_variation
                
                building_width = base_width * width_variation
                building_depth = base_depth * depth_variation
                
                # Ensure minimum and maximum sizes
                building_width = max(8.0, min(40.0, building_width))
                building_depth = max(6.0, min(30.0, building_depth))
                
                if self._is_position_valid(position, building_width, building_depth):
                    floors = self._get_adaptive_floors(row, col, building_width * building_depth)
                    floor_height = self._get_floor_height()
                    
                    building_data.append({
                        'position': position,
                        'width': building_width,
                        'depth': building_depth,
                        'floors': floors,
                        'floor_height': floor_height
                    })
                    
                    building_count += 1
                
                x += spacing_x
                col += 1
            
            y += spacing_y
            row += 1
        
        logger.info(f"Generated {len(building_data)} buildings using grid layout")
        return building_data
    
    def _generate_candidate_positions(self):
        """Generate candidate positions for clustering"""
        bounds = self.site_params.site_bounds
        candidates = []
        
        # Generate more candidates than needed for better clustering
        target_candidates = min(100, int(self.site_params.site_area / 200))
        attempts = 0
        max_attempts = target_candidates * 10
        
        while len(candidates) < target_candidates and attempts < max_attempts:
            x = random.uniform(
                bounds['min_x'] + self.site_params.setback_distance,
                bounds['max_x'] - self.site_params.setback_distance
            )
            y = random.uniform(
                bounds['min_y'] + self.site_params.setback_distance,
                bounds['max_y'] - self.site_params.setback_distance
            )
            
            position = UPoint(x, y, 0)
            
            if self._is_point_in_site(position):
                # Check minimum distance from existing candidates
                too_close = False
                min_distance = self.site_params.min_building_spacing * 0.5
                
                for existing in candidates:
                    if position.distance_to(existing) < min_distance:
                        too_close = True
                        break
                
                if not too_close:
                    candidates.append(position)
            
            attempts += 1
        
        return candidates
    
    def _get_base_building_dimensions(self):
        """Get base building dimensions based on site type and style"""
        # Base dimensions by site type
        type_dimensions = {
            0: (15.0, 12.0),   # Residential
            1: (22.0, 16.0),   # Commercial  
            2: (18.0, 14.0),   # Office
            3: (16.0, 13.0),   # Mixed
            4: (25.0, 18.0)    # Industrial
        }
        
        base_width, base_depth = type_dimensions.get(self.site_params.site_type, (15.0, 12.0))
        
        # Adjust by building style
        style_multipliers = {
            0: (1.0, 1.0),     # Standard
            1: (1.3, 1.1),     # Large
            2: (0.8, 0.9),     # Compact
            3: (1.1, 1.2)      # Extended
        }
        
        width_mult, depth_mult = style_multipliers.get(self.site_params.building_style, (1.0, 1.0))
        
        # Apply density scaling
        density_scale = 0.8 + (self.site_params.density * 0.6)  # 0.8 to 1.4 range
        
        return base_width * width_mult * density_scale, base_depth * depth_mult * density_scale
    
    def _get_cluster_building_size(self, cluster_size):
        """Get building size based on cluster characteristics"""
        base_width, base_depth = self._get_base_building_dimensions()
        
        # Larger clusters get bigger buildings
        size_multiplier = 1.0 + (cluster_size - 1) * 0.1
        size_multiplier = min(2.0, size_multiplier)  # Cap at 2x
        
        return base_width * size_multiplier, base_depth * size_multiplier
    
    def _get_voronoi_building_size(self, cell_area):
        """Get building size based on Voronoi cell area"""
        base_width, base_depth = self._get_base_building_dimensions()
        
        # Scale based on cell area
        area_ratio = cell_area / (base_width * base_depth)
        size_multiplier = math.sqrt(max(0.5, min(2.0, area_ratio)))
        
        return base_width * size_multiplier, base_depth * size_multiplier
    
    def _get_cluster_floors(self, cluster_size):
        """Get number of floors based on cluster size"""
        base_floors = self._calculate_base_floors()
        
        # Larger clusters can have taller buildings
        floor_multiplier = 1.0 + (cluster_size - 1) * 0.2
        floors = int(base_floors * floor_multiplier)
        
        return max(1, min(20, floors))
    
    def _get_voronoi_floors(self, cell_area):
        """Get number of floors based on Voronoi cell area"""
        base_floors = self._calculate_base_floors()
        
        # Larger cells get more floors
        if cell_area > 800:
            return min(20, int(base_floors * 1.5))
        elif cell_area > 400:
            return base_floors
        else:
            return max(1, int(base_floors * 0.7))
    
    def _get_adaptive_floors(self, row, col, building_area):
        """Get adaptive floors based on position and area"""
        base_floors = self._calculate_base_floors()
        
        # Add variation based on position
        position_factor = 1.0
        
        # Central buildings can be taller
        if row % 3 == 1 and col % 3 == 1:  # Center of 3x3 grid
            position_factor = 1.3
        elif (row + col) % 2 == 0:  # Checkerboard pattern
            position_factor = 1.1
        
        # Adjust for building area
        area_factor = math.sqrt(building_area / 200.0)  # Base area reference
        area_factor = max(0.7, min(1.5, area_factor))
        
        floors = int(base_floors * position_factor * area_factor)
        return max(1, min(25, floors))
    
    def _calculate_base_floors(self):
        """Calculate base number of floors from FAR and density"""
        base_width, base_depth = self._get_base_building_dimensions()
        building_footprint = base_width * base_depth
        
        # Calculate floors needed to achieve target FAR
        total_floor_area_needed = self.site_params.site_area * self.site_params.site_far
        estimated_buildings = max(1, int(self.site_params.site_area * self.site_params.density / (building_footprint * 2)))
        
        floors_per_building = total_floor_area_needed / (estimated_buildings * building_footprint)
        
        # Apply constraints
        min_floors = 1
        max_floors = 15 if self.site_params.site_type in [1, 2] else 8  # Commercial/Office vs others
        
        return max(min_floors, min(max_floors, int(floors_per_building)))
    
    def _get_floor_height(self):
        """Get floor height based on building style"""
        heights = {
            0: 3.0,   # Residential
            1: 3.5,   # Office
            2: 4.0,   # Commercial
            3: 3.2    # Mixed
        }
        return heights.get(self.site_params.building_style, 3.0)
    
    def _is_position_valid(self, position, width, depth):
        """Check if building position is valid"""
        # Check if all corners are within site
        half_width = width / 2
        half_depth = depth / 2
        
        corners = [
            UPoint(position.x - half_width, position.y - half_depth, 0),
            UPoint(position.x + half_width, position.y - half_depth, 0),
            UPoint(position.x + half_width, position.y + half_depth, 0),
            UPoint(position.x - half_width, position.y + half_depth, 0)
        ]
        
        return all(self._is_point_in_site(corner) for corner in corners)
    
    def _is_point_in_site(self, point):
        """Check if point is inside site boundary using ray casting"""
        if not self.site_params.site_polyline or len(self.site_params.site_polyline.coordinates) < 3:
            return False
        
        x, y = point.x, point.y
        coordinates = self.site_params.site_polyline.coordinates
        n = len(coordinates)
        inside = False
        
        p1x, p1y = coordinates[0].x, coordinates[0].y
        for i in range(1, n + 1):
            p2x, p2y = coordinates[i % n].x, coordinates[i % n].y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _calculate_centroid(self, points):
        """Calculate centroid of points"""
        if not points:
            return UPoint(0, 0, 0)
        
        x = sum(p.x for p in points) / len(points)
        y = sum(p.y for p in points) / len(points)
        z = sum(p.z for p in points) / len(points)
        
        return UPoint(x, y, z)
    
    def _calculate_polygon_area(self, points):
        """Calculate polygon area"""
        if len(points) < 3:
            return 0.0
        
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i].x * points[j].y
            area -= points[j].x * points[i].y
        return abs(area) / 2.0


class EnhancedGeometryProcessor:
    """Enhanced geometry processor with C# algorithm integration"""
    
    @staticmethod
    def compute_parameters(flattened_vertices):
        """Create enhanced site parameters"""
        site_params = EnhancedSiteParameters()
        site_params.set_site_from_vertices(flattened_vertices)
        site_params.update_dependent_parameters()
        return [site_params]
    
    @staticmethod
    def compute_design(site_parameters_list):
        """Generate urban design with enhanced algorithms"""
        if not site_parameters_list:
            return EnhancedGeometryProcessor._get_default_response()
        
        site_params = site_parameters_list[0]
        
        if not site_params.site_polyline or len(site_params.site_polyline.coordinates) < 3:
            return EnhancedGeometryProcessor._get_default_response()
        
        try:
            # Use enhanced building generator
            building_generator = EnhancedBuildingGenerator(site_params)
            building_data = building_generator.generate_buildings()
            
            logger.info(f"Generated {len(building_data)} buildings using enhanced algorithms")
            
            response = {
                'buildingLayersHeights': [],
                'buildingLayersVertices': [],
                'subSiteVertices': [],
                'subSiteSetbackVertices': []
            }
            
            # Process building data
            for building in building_data:
                position = building['position']
                width = building['width']
                depth = building['depth']
                floors = building['floors']
                floor_height = building['floor_height']
                
                # Create building layers
                building_vertices = []
                heights = []
                
                for floor in range(floors):
                    z = floor * floor_height
                    layer_vertices = EnhancedGeometryProcessor._create_building_floor_vertices(
                        position, width, depth, z
                    )
                    building_vertices.append(layer_vertices)
                    heights.append(floor_height)
                
                response['buildingLayersHeights'].append(heights)
                response['buildingLayersVertices'].append(building_vertices)
            
            # Generate site boundary
            site_vertices = []
            for point in site_params.site_polyline.coordinates:
                site_vertices.extend([point.x, point.y, point.z])
            response['subSiteVertices'].append(site_vertices)
            
            # Generate setback using polygon offsetting
            setback_vertices = EnhancedGeometryProcessor._create_setback_polygon(
                site_params.site_polyline.coordinates, site_params.setback_distance
            )
            if setback_vertices:
                response['subSiteSetbackVertices'].append(setback_vertices)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in enhanced design generation: {str(e)}")
            return EnhancedGeometryProcessor._get_default_response()
    
    @staticmethod
    def _create_building_floor_vertices(position, width, depth, z):
        """Create vertices for a building floor"""
        half_width = width / 2
        half_depth = depth / 2
        
        return [
            position.x - half_width, position.y - half_depth, z,  # Bottom-left
            position.x + half_width, position.y - half_depth, z,  # Bottom-right
            position.x + half_width, position.y + half_depth, z,  # Top-right
            position.x - half_width, position.y + half_depth, z   # Top-left
        ]
    
    @staticmethod
    def _create_setback_polygon(coordinates, setback_distance):
        """Create setback polygon using simple inward offsetting"""
        if len(coordinates) < 3:
            return []
        
        # Calculate centroid
        centroid_x = sum(p.x for p in coordinates) / len(coordinates)
        centroid_y = sum(p.y for p in coordinates) / len(coordinates)
        
        # Create inset polygon by moving vertices toward centroid
        setback_vertices = []
        
        for point in coordinates:
            # Vector from centroid to point
            to_point_x = point.x - centroid_x
            to_point_y = point.y - centroid_y
            
            # Distance from centroid
            distance = math.sqrt(to_point_x**2 + to_point_y**2)
            
            if distance > setback_distance:
                # Normalize and scale
                scale = (distance - setback_distance) / distance
                new_x = centroid_x + to_point_x * scale
                new_y = centroid_y + to_point_y * scale
                
                setback_vertices.extend([new_x, new_y, point.z + 0.2])
        
        return setback_vertices if len(setback_vertices) >= 9 else []
    
    @staticmethod
    def _get_default_response():
        """Return enhanced default response"""
        return {
            'buildingLayersHeights': [
                [3.0, 3.0, 3.0, 3.0],
                [4.0, 3.5, 3.5, 3.5],
                [3.0, 3.0, 3.0],
                [3.5, 3.5, 3.5, 3.5, 3.5]
            ],
            'buildingLayersVertices': [
                [
                    [0.0, 0.0, 0.0, 15.0, 0.0, 0.0, 15.0, 12.0, 0.0, 0.0, 12.0, 0.0],
                    [0.0, 0.0, 3.0, 15.0, 0.0, 3.0, 15.0, 12.0, 3.0, 0.0, 12.0, 3.0],
                    [0.0, 0.0, 6.0, 15.0, 0.0, 6.0, 15.0, 12.0, 6.0, 0.0, 12.0, 6.0],
                    [0.0, 0.0, 9.0, 15.0, 0.0, 9.0, 15.0, 12.0, 9.0, 0.0, 12.0, 9.0]
                ],
                [
                    [25.0, 5.0, 0.0, 45.0, 5.0, 0.0, 45.0, 21.0, 0.0, 25.0, 21.0, 0.0],
                    [25.0, 5.0, 4.0, 45.0, 5.0, 4.0, 45.0, 21.0, 4.0, 25.0, 21.0, 4.0],
                    [25.0, 5.0, 7.5, 45.0, 5.0, 7.5, 45.0, 21.0, 7.5, 25.0, 21.0, 7.5],
                    [25.0, 5.0, 11.0, 45.0, 5.0, 11.0, 45.0, 21.0, 11.0, 25.0, 21.0, 11.0]
                ],
                [
                    [55.0, 10.0, 0.0, 70.0, 10.0, 0.0, 70.0, 20.0, 0.0, 55.0, 20.0, 0.0],
                    [55.0, 10.0, 3.0, 70.0, 10.0, 3.0, 70.0, 20.0, 3.0, 55.0, 20.0, 3.0],
                    [55.0, 10.0, 6.0, 70.0, 10.0, 6.0, 70.0, 20.0, 6.0, 55.0, 20.0, 6.0]
                ],
                [
                    [10.0, 25.0, 0.0, 28.0, 25.0, 0.0, 28.0, 39.0, 0.0, 10.0, 39.0, 0.0],
                    [10.0, 25.0, 3.5, 28.0, 25.0, 3.5, 28.0, 39.0, 3.5, 10.0, 39.0, 3.5],
                    [10.0, 25.0, 7.0, 28.0, 25.0, 7.0, 28.0, 39.0, 7.0, 10.0, 39.0, 7.0],
                    [10.0, 25.0, 10.5, 28.0, 25.0, 10.5, 28.0, 39.0, 10.5, 10.0, 39.0, 10.5],
                    [10.0, 25.0, 14.0, 28.0, 25.0, 14.0, 28.0, 39.0, 14.0, 10.0, 39.0, 14.0]
                ]
            ],
            'subSiteVertices': [
                [0.0, 0.0, 0.0, 80.0, 0.0, 0.0, 80.0, 50.0, 0.0, 0.0, 50.0, 0.0]
            ],
            'subSiteSetbackVertices': [
                [4.0, 4.0, 0.2, 76.0, 4.0, 0.2, 76.0, 46.0, 0.2, 4.0, 46.0, 0.2]
            ]
        }


class EnhancedGeneratePlanView(APIView):
    """Enhanced plan generation with C# algorithms"""
    
    def post(self, request):
        try:
            # Validate input
            serializer = GeneratePlanRequestSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Validation failed: {serializer.errors}")
                return Response(
                    {'error': 'Invalid input data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            flattened_vertices = validated_data['plan_flattened_vertices']
            plan_parameters_data = validated_data.get('plan_parameters', {})
            
            logger.info(f"Enhanced plan generation request: {len(flattened_vertices)} vertices")
            
            # Compute enhanced site parameters
            site_parameters_list = EnhancedGeometryProcessor.compute_parameters(flattened_vertices)
            site_parameters = site_parameters_list[0] if site_parameters_list else EnhancedSiteParameters()
            
            # Apply enhanced parameter processing
            self._apply_enhanced_parameters(plan_parameters_data, site_parameters)
            
            logger.info(f"Enhanced parameters: area={site_parameters.site_area:.2f}, "
                       f"FAR={site_parameters.site_far}, density={site_parameters.density}, "
                       f"clustering={site_parameters.use_clustering}, "
                       f"voronoi={site_parameters.use_voronoi}")
            
            # Generate enhanced design
            design_result = EnhancedGeometryProcessor.compute_design(site_parameters_list)
            
            # Validate and serialize response
            response_serializer = GeneratePlanResponseSerializer(data=design_result)
            if response_serializer.is_valid():
                logger.info(f"Enhanced plan generation successful - "
                           f"{len(design_result['buildingLayersVertices'])} buildings generated")
                return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Response serialization failed: {response_serializer.errors}")
                return Response(
                    {'error': 'Internal processing failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"Enhanced plan generation error: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Enhanced plan generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _apply_enhanced_parameters(self, plan_params_data, site_parameters):
        """Apply enhanced parameter processing"""
        if not plan_params_data:
            return
        
        # Standard parameters
        if 'site_type' in plan_params_data:
            site_parameters.site_type = max(0, min(4, int(plan_params_data['site_type'])))
        
        if 'far' in plan_params_data:
            site_parameters.site_far = max(0.1, min(10.0, float(plan_params_data['far'])))
        
        if 'density' in plan_params_data:
            site_parameters.density = max(0.01, min(0.99, float(plan_params_data['density'])))
        
        if 'mix_ratio' in plan_params_data:
            site_parameters.mix_ratio = max(0.0, min(0.99, float(plan_params_data['mix_ratio'])))
        
        if 'building_style' in plan_params_data:
            site_parameters.building_style = max(0, min(3, int(plan_params_data['building_style'])))
        
        if 'orientation' in plan_params_data:
            site_parameters.radiant = math.radians(
                max(0.0, min(180.0, float(plan_params_data['orientation'])))
            )
        
        # Enhanced parameters
        if 'use_clustering' in plan_params_data:
            site_parameters.use_clustering = bool(plan_params_data['use_clustering'])
        
        if 'cluster_diameter' in plan_params_data:
            site_parameters.cluster_diameter = max(10.0, float(plan_params_data['cluster_diameter']))
        
        if 'use_voronoi' in plan_params_data:
            site_parameters.use_voronoi = bool(plan_params_data['use_voronoi'])
        
        if 'building_variation' in plan_params_data:
            site_parameters.building_variation = max(0.0, min(1.0, float(plan_params_data['building_variation'])))
        
        if 'max_buildings' in plan_params_data:
            site_parameters.max_buildings = max(1, min(200, int(plan_params_data['max_buildings'])))
        
        # Update dependent parameters after applying changes
        site_parameters.update_dependent_parameters()
        
        logger.info(f"Applied enhanced parameters: clustering={site_parameters.use_clustering}, "
                   f"voronoi={site_parameters.use_voronoi}, "
                   f"variation={site_parameters.building_variation}")