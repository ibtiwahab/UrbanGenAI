"""
Voronoi diagram implementation for urban planning
Simplified Fortune's algorithm for generating Voronoi diagrams
"""

import math
import heapq
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class VPoint:
    """Point class for Voronoi calculations"""
    x: float
    y: float
    
    def __eq__(self, other):
        if not isinstance(other, VPoint):
            return False
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9
    
    def __hash__(self):
        return hash((round(self.x, 9), round(self.y, 9)))
    
    def distance_to(self, other):
        """Calculate Euclidean distance to another point"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class FortuneSite:
    """Site (seed point) for Voronoi diagram"""
    point: VPoint
    index: int = 0
    
    def __eq__(self, other):
        return isinstance(other, FortuneSite) and self.point == other.point
    
    def __hash__(self):
        return hash(self.point)


class VoronoiEdge:
    """Edge in Voronoi diagram"""
    def __init__(self, start: Optional[VPoint] = None, end: Optional[VPoint] = None):
        self.start = start
        self.end = end
        self.left_site: Optional[FortuneSite] = None
        self.right_site: Optional[FortuneSite] = None
        self.direction: Optional[VPoint] = None
    
    def is_finite(self) -> bool:
        """Check if edge has both start and end points"""
        return self.start is not None and self.end is not None


class VoronoiCell:
    """Cell in Voronoi diagram"""
    def __init__(self, site: FortuneSite):
        self.site = site
        self.edges: List[VoronoiEdge] = []
        self.vertices: List[VPoint] = []
    
    def get_bounded_vertices(self, bounds: Tuple[float, float, float, float]) -> List[VPoint]:
        """Get cell vertices bounded by given rectangle"""
        min_x, min_y, max_x, max_y = bounds
        bounded_vertices = []
        
        for vertex in self.vertices:
            if min_x <= vertex.x <= max_x and min_y <= vertex.y <= max_y:
                bounded_vertices.append(vertex)
        
        # Add intersection points with bounds if needed
        # This is a simplified implementation
        return bounded_vertices
    
    def calculate_area(self, bounds: Optional[Tuple[float, float, float, float]] = None) -> float:
        """Calculate approximate area of the cell"""
        vertices = self.get_bounded_vertices(bounds) if bounds else self.vertices
        
        if len(vertices) < 3:
            return 0.0
        
        # Use shoelace formula
        area = 0.0
        n = len(vertices)
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i].x * vertices[j].y
            area -= vertices[j].x * vertices[i].y
        
        return abs(area) / 2.0


class SimplifiedVoronoi:
    """Simplified Voronoi diagram generator"""
    
    def __init__(self):
        self.sites: List[FortuneSite] = []
        self.cells: List[VoronoiCell] = []
        self.edges: List[VoronoiEdge] = []
        self.vertices: List[VPoint] = []
    
    def add_site(self, x: float, y: float, index: int = 0) -> FortuneSite:
        """Add a site to the diagram"""
        site = FortuneSite(VPoint(x, y), index)
        self.sites.append(site)
        return site
    
    def generate_simple_voronoi(self, bounds: Tuple[float, float, float, float]) -> None:
        """
        Generate a simplified Voronoi diagram using distance-based approach
        This is not Fortune's algorithm but a simpler approximation
        """
        if len(self.sites) < 2:
            return
        
        min_x, min_y, max_x, max_y = bounds
        self.cells = []
        
        # Create cells for each site
        for site in self.sites:
            cell = VoronoiCell(site)
            self.cells.append(cell)
        
        # Generate vertices using a grid-based approach
        resolution = 50  # Grid resolution for approximation
        step_x = (max_x - min_x) / resolution
        step_y = (max_y - min_y) / resolution
        
        # Find Voronoi vertices by checking grid intersections
        for i in range(resolution + 1):
            for j in range(resolution + 1):
                x = min_x + i * step_x
                y = min_y + j * step_y
                point = VPoint(x, y)
                
                # Find closest sites
                distances = [(site.point.distance_to(point), site) for site in self.sites]
                distances.sort()
                
                # If multiple sites are approximately equidistant, this is a vertex
                if len(distances) >= 3:
                    closest_dist = distances[0][0]
                    equidistant_sites = [site for dist, site in distances if abs(dist - closest_dist) < step_x / 2]
                    
                    if len(equidistant_sites) >= 3:
                        self.vertices.append(point)
                        # Add vertex to relevant cells
                        for _, site in distances[:3]:
                            for cell in self.cells:
                                if cell.site == site:
                                    cell.vertices.append(point)
    
    def get_cell_for_site(self, site: FortuneSite) -> Optional[VoronoiCell]:
        """Get the cell for a given site"""
        for cell in self.cells:
            if cell.site == site:
                return cell
        return None
    
    def get_neighbor_sites(self, site: FortuneSite) -> List[FortuneSite]:
        """Get neighboring sites (simplified)"""
        neighbors = []
        site_point = site.point
        
        # Find closest sites
        distances = []
        for other_site in self.sites:
            if other_site != site:
                dist = site_point.distance_to(other_site.point)
                distances.append((dist, other_site))
        
        distances.sort()
        
        # Return closest sites as neighbors (simplified approach)
        max_neighbors = min(6, len(distances))  # Limit to reasonable number
        return [site for _, site in distances[:max_neighbors]]


class Voronoi:
    """Main Voronoi class - wrapper for simplified implementation"""
    
    def __init__(self, points: List[Tuple[float, float]], bounds: Optional[Tuple[float, float, float, float]] = None):
        self.points = points
        self.diagram = SimplifiedVoronoi()
        
        # Add sites
        for i, (x, y) in enumerate(points):
            self.diagram.add_site(x, y, i)
        
        # Calculate bounds if not provided
        if bounds is None:
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                margin = 10
                bounds = (
                    min(xs) - margin, min(ys) - margin,
                    max(xs) + margin, max(ys) + margin
                )
            else:
                bounds = (0, 0, 100, 100)
        
        self.bounds = bounds
        
        # Generate diagram
        self.diagram.generate_simple_voronoi(bounds)
    
    @property
    def regions(self) -> List[List[int]]:
        """Get regions as lists of vertex indices"""
        regions = []
        for cell in self.diagram.cells:
            # Convert vertices to indices (simplified)
            region = list(range(len(cell.vertices)))
            regions.append(region)
        return regions
    
    @property
    def vertices(self) -> List[List[float]]:
        """Get vertices as list of [x, y] coordinates"""
        return [[v.x, v.y] for v in self.diagram.vertices]
    
    def get_site_polygons(self) -> List[List[Tuple[float, float]]]:
        """Get polygons for each site"""
        polygons = []
        
        for cell in self.diagram.cells:
            vertices = cell.get_bounded_vertices(self.bounds)
            
            if len(vertices) >= 3:
                # Sort vertices to form proper polygon
                center_x = sum(v.x for v in vertices) / len(vertices)
                center_y = sum(v.y for v in vertices) / len(vertices)
                
                def angle_from_center(vertex):
                    return math.atan2(vertex.y - center_y, vertex.x - center_x)
                
                vertices.sort(key=angle_from_center)
                polygon = [(v.x, v.y) for v in vertices]
            else:
                # Fallback: create simple square around site
                site = cell.site.point
                size = 20
                polygon = [
                    (site.x - size, site.y - size),
                    (site.x + size, site.y - size),
                    (site.x + size, site.y + size),
                    (site.x - size, site.y + size)
                ]
            
            polygons.append(polygon)
        
        return polygons
    
    def get_cell_areas(self) -> List[float]:
        """Get area of each Voronoi cell"""
        areas = []
        for cell in self.diagram.cells:
            area = cell.calculate_area(self.bounds)
            areas.append(area)
        return areas
    
    def point_to_region_index(self, x: float, y: float) -> int:
        """Find which region a point belongs to"""
        query_point = VPoint(x, y)
        min_distance = float('inf')
        closest_index = 0
        
        for i, site in enumerate(self.diagram.sites):
            distance = query_point.distance_to(site.point)
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        return closest_index


# Utility functions for integration
def create_voronoi_from_points(points: List[Tuple[float, float]], 
                             bounds: Optional[Tuple[float, float, float, float]] = None) -> Voronoi:
    """Create Voronoi diagram from list of points"""
    return Voronoi(points, bounds)


def generate_random_sites(bounds: Tuple[float, float, float, float], 
                         count: int, 
                         min_distance: float = 10.0) -> List[Tuple[float, float]]:
    """Generate random sites with minimum distance constraint"""
    import random
    
    min_x, min_y, max_x, max_y = bounds
    sites = []
    max_attempts = count * 100
    attempts = 0
    
    while len(sites) < count and attempts < max_attempts:
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        
        # Check minimum distance
        too_close = False
        for existing_x, existing_y in sites:
            if math.sqrt((x - existing_x) ** 2 + (y - existing_y) ** 2) < min_distance:
                too_close = True
                break
        
        if not too_close:
            sites.append((x, y))
        
        attempts += 1
    
    return sites


def voronoi_relaxation(sites: List[Tuple[float, float]], 
                      bounds: Tuple[float, float, float, float],
                      iterations: int = 3) -> List[Tuple[float, float]]:
    """Apply Lloyd's relaxation to improve site distribution"""
    current_sites = sites[:]
    
    for _ in range(iterations):
        voronoi = create_voronoi_from_points(current_sites, bounds)
        new_sites = []
        
        for i, cell in enumerate(voronoi.diagram.cells):
            vertices = cell.get_bounded_vertices(bounds)
            
            if vertices:
                # Move site to centroid of its cell
                centroid_x = sum(v.x for v in vertices) / len(vertices)
                centroid_y = sum(v.y for v in vertices) / len(vertices)
                new_sites.append((centroid_x, centroid_y))
            else:
                # Keep original site if no vertices
                new_sites.append(current_sites[i])
        
        current_sites = new_sites
    
    return current_sites


# Export main classes and functions
__all__ = [
    'Voronoi', 
    'FortuneSite', 
    'VPoint', 
    'VoronoiCell', 
    'VoronoiEdge',
    'SimplifiedVoronoi',
    'create_voronoi_from_points',
    'generate_random_sites',
    'voronoi_relaxation'
]