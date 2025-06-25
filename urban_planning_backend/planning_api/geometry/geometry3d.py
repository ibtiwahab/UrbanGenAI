# planning_api/geometry/geometry3d.py
import math
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass


@dataclass
class UPoint:
    """3D Point for urban geometry operations"""
    x: float
    y: float
    z: float = 0.0
    
    def distance_to(self, other: 'UPoint') -> float:
        """Calculate distance to another point"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def translate(self, vector: 'UVector3') -> 'UPoint':
        """Translate point by vector"""
        return UPoint(self.x + vector.x, self.y + vector.y, self.z + vector.z)
    
    def get_envelope(self):
        """Get bounding envelope for spatial indexing"""
        return {
            'min_x': self.x - 0.1, 'max_x': self.x + 0.1,
            'min_y': self.y - 0.1, 'max_y': self.y + 0.1,
            'min_z': self.z - 0.1, 'max_z': self.z + 0.1
        }


@dataclass
class UVector3:
    """3D Vector for urban geometry operations"""
    x: float
    y: float
    z: float = 0.0
    
    def length(self) -> float:
        """Calculate vector length"""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'UVector3':
        """Return normalized vector"""
        length = self.length()
        if length == 0:
            return UVector3(0, 0, 0)
        return UVector3(self.x / length, self.y / length, self.z / length)
    
    def dot(self, other: 'UVector3') -> float:
        """Dot product with another vector"""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'UVector3') -> 'UVector3':
        """Cross product with another vector"""
        return UVector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def angle_between(self, other: 'UVector3') -> float:
        """Calculate angle to another vector in radians"""
        dot_product = self.dot(other)
        lengths = self.length() * other.length()
        if lengths == 0:
            return 0
        cos_angle = max(-1, min(1, dot_product / lengths))
        return math.acos(cos_angle)
    
    def __mul__(self, scalar: float) -> 'UVector3':
        return UVector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __add__(self, other: 'UVector3') -> 'UVector3':
        return UVector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'UVector3') -> 'UVector3':
        return UVector3(self.x - other.x, self.y - other.y, self.z - other.z)


class UPolyline:
    """3D Polyline for urban geometry operations"""
    
    def __init__(self, coordinates: List[UPoint]):
        self.coordinates = coordinates
        self.num_points = len(coordinates)
    
    @property
    def first(self) -> UPoint:
        """Get first point"""
        return self.coordinates[0] if self.coordinates else UPoint(0, 0, 0)
    
    @property
    def last(self) -> UPoint:
        """Get last point"""
        return self.coordinates[-1] if self.coordinates else UPoint(0, 0, 0)
    
    def is_closed(self, tolerance: float = 1e-6) -> bool:
        """Check if polyline is closed"""
        if len(self.coordinates) < 4:
            return False
        return self.first.distance_to(self.last) <= tolerance


class Point3DComparer:
    """3D Point comparer with tolerance"""
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
    
    def compare(self, p1: UPoint, p2: UPoint) -> int:
        """Compare two points with tolerance"""
        if abs(p1.x - p2.x) < self.tolerance:
            if abs(p1.y - p2.y) < self.tolerance:
                if abs(p1.z - p2.z) < self.tolerance:
                    return 0
                return 1 if p1.z > p2.z else -1
            return 1 if p1.y > p2.y else -1
        return 1 if p1.x > p2.x else -1


class LinesIntersection3D:
    """3D line intersection calculations"""
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.small_num = tolerance * tolerance
        self.p_intersections = []
        self.q_intersections = []
        self.is_parallel = False
        self.has_intersection = False
        self.is_collinear = False
        self.is_proper = False
    
    def compute(self, p1: UPoint, p2: UPoint, q1: UPoint, q2: UPoint) -> bool:
        """Compute intersection between two 3D line segments"""
        # Reset state
        self.is_parallel = False
        self.has_intersection = False
        self.is_collinear = False
        self.is_proper = False
        self.p_intersections = []
        self.q_intersections = []
        
        # Convert to vectors
        u = UVector3(p2.x - p1.x, p2.y - p1.y, p2.z - p1.z)
        v = UVector3(q2.x - q1.x, q2.y - q1.y, q2.z - q1.z)
        w = UVector3(p1.x - q1.x, p1.y - q1.y, p1.z - q1.z)
        
        # Calculate parameters
        a = u.dot(u)
        b = u.dot(v)
        c = v.dot(v)
        d = u.dot(w)
        e = v.dot(w)
        
        D = a * c - b * b
        
        # Check if lines are parallel using angle
        radian = u.angle_between(v)
        gap = math.sin(radian) * min(u.length(), v.length())
        
        if gap < self.tolerance:
            self.is_parallel = True
            sN, sD = 0.0, 1.0
            tN, tD = e, c
        else:
            sN = b * e - c * d
            tN = a * e - b * d
            sD = tD = D
            
            if sN < 0.0:
                sN = 0.0
                tN, tD = e, c
            elif sN > sD:
                sN = sD
                tN, tD = e + b, c
        
        if tN < 0.0:
            tN = 0.0
            if -d < 0.0:
                sN = 0.0
            elif -d > a:
                sN = sD
            else:
                sN = -d
                sD = a
        elif tN > tD:
            tN = tD
            if (-d + b) < 0.0:
                sN = 0.0
            elif (-d + b) > a:
                sN = sD
            else:
                sN = -d + b
                sD = a
        
        # Calculate final parameters
        sc = 0.0 if abs(sN) < self.small_num else sN / sD
        tc = 0.0 if abs(tN) < self.small_num else tN / tD
        
        # Clamp to segment bounds
        scd = max(0, min(1, sc))
        tcd = max(0, min(1, tc))
        
        # Calculate closest points
        p = p1.translate(u * scd)
        q = q1.translate(v * tcd)
        
        # Adjust to exact endpoints if very close
        if scd > 0.9 and p.distance_to(p2) < self.tolerance:
            p = p2
            scd = 1.0
        elif scd < 0.1 and p.distance_to(p1) < self.tolerance:
            p = p1
            scd = 0.0
        
        if tcd > 0.9 and q.distance_to(q2) < self.tolerance:
            q = q2
            tcd = 1.0
        elif tcd < 0.1 and q.distance_to(q1) < self.tolerance:
            q = q1
            tcd = 0.0
        
        # Check if intersection exists
        distance = p.distance_to(q)
        
        if distance < self.tolerance:
            self.has_intersection = True
            
            if self.is_parallel:
                self.is_collinear = True
                # Handle collinear intersection
                comparer = Point3DComparer(self.tolerance)
                points = sorted([p1, p2, q1, q2], key=lambda pt: (pt.x, pt.y, pt.z))
                
                # Get middle points for overlap
                if len(set([(p.x, p.y, p.z) for p in points])) > 2:
                    # Remove endpoints, keep middle points
                    middle_points = points[1:-1]
                    for point in middle_points:
                        self.p_intersections.append(point)
                        self.q_intersections.append(point)
            else:
                # Point intersection
                if 0 < scd < 1 and 0 < tcd < 1:
                    self.is_proper = True
                    intersection_point = UPoint(
                        0.5 * (p.x + q.x),
                        0.5 * (p.y + q.y), 
                        0.5 * (p.z + q.z)
                    )
                    self.p_intersections.append(intersection_point)
                    self.q_intersections.append(intersection_point)
                elif (scd == 0 or scd == 1) and (tcd == 0 or tcd == 1):
                    # Endpoint intersection
                    self.p_intersections.append(p)
                    self.q_intersections.append(q)
                elif (scd == 0 or scd == 1) and (0 < tcd < 1):
                    # First line endpoint intersects second line
                    self.q_intersections.append(p)
                elif (0 < scd < 1) and (tcd == 0 or tcd == 1):
                    # Second line endpoint intersects first line
                    self.p_intersections.append(q)
            
            return True
        
        return False


class LineStringSnapper3D:
    """3D LineString snapping operations"""
    
    def __init__(self, polylines: List[UPolyline], tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.polylines = list(set(polylines))  # Remove duplicates
        self.end_points_position = {}
        self.end_points = {}
        self.visited = set()
        
        self._build_dict()
        self._build_tree()
    
    def _build_dict(self):
        """Build dictionary of endpoint positions"""
        for i, polyline in enumerate(self.polylines):
            endpoints = [polyline.first, polyline.last]
            
            for j, point in enumerate(endpoints):
                if point not in self.end_points_position:
                    self.end_points_position[point] = []
                
                position = 'start' if j == 0 else 'end'
                self.end_points_position[point].append({
                    'line_id': i,
                    'position': position
                })
    
    def _build_tree(self):
        """Build spatial index for endpoints"""
        for point in self.end_points_position.keys():
            envelope = point.get_envelope()
            # Expand by tolerance
            for key in envelope:
                if 'min' in key:
                    envelope[key] -= self.tolerance * 0.5
                else:
                    envelope[key] += self.tolerance * 0.5
            self.end_points[point] = envelope
    
    def snap(self):
        """Perform snapping operation"""
        for point, envelope in self.end_points.items():
            if point in self.visited:
                continue
            
            self.visited.add(point)
            
            # Find nearby points
            candidates = []
            for other_point in self.end_points.keys():
                if other_point != point and other_point not in self.visited:
                    if point.distance_to(other_point) < self.tolerance:
                        candidates.append(other_point)
                        self.visited.add(other_point)
            
            # Snap candidates to current point
            for candidate in candidates:
                positions = self.end_points_position[candidate]
                for pos_info in positions:
                    line_id = pos_info['line_id']
                    position = pos_info['position']
                    
                    if position == 'start':
                        self.polylines[line_id].coordinates[0] = point
                    else:
                        self.polylines[line_id].coordinates[-1] = point


class GeometryComparer3D:
    """3D geometry comparer for deduplication"""
    
    def __init__(self, normalize: bool = True):
        self.normalize = normalize
    
    def equals(self, geom1, geom2) -> bool:
        """Check if two geometries are equal"""
        if not hasattr(geom1, 'coordinates') or not hasattr(geom2, 'coordinates'):
            return False
        
        if len(geom1.coordinates) != len(geom2.coordinates):
            return False
        
        # Normalize geometries if needed
        coords1 = geom1.coordinates
        coords2 = geom2.coordinates
        
        if self.normalize:
            coords1 = self._normalize_coordinates(coords1)
            coords2 = self._normalize_coordinates(coords2)
        
        # Check coordinate equality
        for i in range(len(coords1)):
            if not self._points_equal(coords1[i], coords2[i]):
                return False
        
        return True
    
    def _normalize_coordinates(self, coordinates: List[UPoint]) -> List[UPoint]:
        """Normalize coordinate order"""
        if len(coordinates) < 2:
            return coordinates
        
        # Find minimum point as starting point
        min_idx = 0
        min_point = coordinates[0]
        
        for i, point in enumerate(coordinates):
            if (point.x < min_point.x or 
                (point.x == min_point.x and point.y < min_point.y) or
                (point.x == min_point.x and point.y == min_point.y and point.z < min_point.z)):
                min_point = point
                min_idx = i
        
        # Reorder starting from minimum point
        return coordinates[min_idx:] + coordinates[:min_idx]
    
    def _points_equal(self, p1: UPoint, p2: UPoint, tolerance: float = 1e-9) -> bool:
        """Check if two points are equal within tolerance"""
        return (abs(p1.x - p2.x) < tolerance and 
                abs(p1.y - p2.y) < tolerance and 
                abs(p1.z - p2.z) < tolerance)
    
    def get_hash_code(self, geometry) -> int:
        """Get hash code for geometry"""
        if not hasattr(geometry, 'coordinates'):
            return 0
        
        coordinates = geometry.coordinates
        if self.normalize:
            coordinates = self._normalize_coordinates(coordinates)
        
        hash_code = 0
        for i, point in enumerate(coordinates):
            point_hash = self._get_coordinate_hash(point)
            if i == 0:
                hash_code = point_hash
            else:
                hash_code ^= point_hash * (i * 3 + 31)
        
        return hash_code
    
    def _get_coordinate_hash(self, point: UPoint) -> int:
        """Get hash code for a coordinate"""
        x_hash = hash(round(point.x, 9))
        y_hash = hash(round(point.y, 9))  
        z_hash = hash(round(point.z, 9))
        return (x_hash * 31) ^ (y_hash * 37) ^ (z_hash * 41)


# planning_api/geometry/advanced_operations.py
class Extension3D:
    """3D extension operations"""
    
    @staticmethod
    def translate_coordinate(coordinate: UPoint, vector: UVector3) -> UPoint:
        """Translate coordinate by vector"""
        return UPoint(
            coordinate.x + vector.x,
            coordinate.y + vector.y, 
            coordinate.z + vector.z
        )
    
    @staticmethod
    def reduce_3d_precision(coordinates: List[UPoint], decimal_places: int) -> List[UPoint]:
        """Reduce 3D coordinate precision"""
        result = []
        for coord in coordinates:
            result.append(UPoint(
                round(coord.x, decimal_places),
                round(coord.y, decimal_places),
                round(coord.z, decimal_places)
            ))
        return result
    
    @staticmethod
    def reduce_geometry_precision(geometries: List[Any], decimal_places: int):
        """Reduce precision for multiple geometries"""
        for geometry in geometries:
            if hasattr(geometry, 'coordinates'):
                geometry.coordinates = Extension3D.reduce_3d_precision(
                    geometry.coordinates, decimal_places
                )


class PolylineSnapper3D:
    """Enhanced polyline snapping with spatial indexing"""
    
    def __init__(self, polylines: List[UPolyline], tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.polylines = list(set(polylines))
        self.end_points_position = {}
        self.spatial_index = {}
        self.visited = set()
        
        self._build_spatial_structures()
    
    def _build_spatial_structures(self):
        """Build spatial data structures for efficient snapping"""
        # Grid-based spatial index
        grid_size = self.tolerance * 10
        
        for i, polyline in enumerate(self.polylines):
            endpoints = [polyline.first, polyline.last]
            
            for j, point in enumerate(endpoints):
                # Add to position tracking
                if point not in self.end_points_position:
                    self.end_points_position[point] = []
                
                position = 'start' if j == 0 else 'end'
                self.end_points_position[point].append({
                    'line_id': i,
                    'position': position
                })
                
                # Add to spatial grid
                grid_x = int(point.x / grid_size)
                grid_y = int(point.y / grid_size)
                grid_key = (grid_x, grid_y)
                
                if grid_key not in self.spatial_index:
                    self.spatial_index[grid_key] = []
                self.spatial_index[grid_key].append(point)
    
    def snap(self):
        """Perform optimized snapping using spatial index"""
        grid_size = self.tolerance * 10
        
        for point in list(self.end_points_position.keys()):
            if point in self.visited:
                continue
            
            self.visited.add(point)
            
            # Get candidates from nearby grid cells
            grid_x = int(point.x / grid_size)
            grid_y = int(point.y / grid_size)
            
            candidates = []
            
            # Check 3x3 grid around point
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_key = (grid_x + dx, grid_y + dy)
                    if check_key in self.spatial_index:
                        for candidate in self.spatial_index[check_key]:
                            if (candidate != point and 
                                candidate not in self.visited and
                                point.distance_to(candidate) < self.tolerance):
                                candidates.append(candidate)
                                self.visited.add(candidate)
            
            # Snap all candidates to current point
            for candidate in candidates:
                positions = self.end_points_position[candidate]
                for pos_info in positions:
                    line_id = pos_info['line_id']
                    position = pos_info['position']
                    
                    if position == 'start':
                        self.polylines[line_id].coordinates[0] = point
                    else:
                        self.polylines[line_id].coordinates[-1] = point
    
    def get_snapped_polylines(self) -> List[UPolyline]:
        """Get the snapped polylines"""
        return self.polylines


class SegmentsIntersection3D:
    """Enhanced 3D segment intersection with better precision handling"""
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.small_num = tolerance * tolerance
        self.round_digits = int(abs(math.log10(self.small_num)))
        
        # Results
        self.p_intersections = []
        self.q_intersections = []
        self.is_parallel = False
        self.has_intersection = False
        self.is_collinear = False
        self.is_proper = False
    
    def compute(self, p1: UPoint, p2: UPoint, q1: UPoint, q2: UPoint) -> bool:
        """Compute intersection with enhanced precision handling"""
        # Reset state
        self._reset_state()
        
        # Convert to vectors using higher precision
        u = UVector3(p2.x - p1.x, p2.y - p1.y, p2.z - p1.z)
        v = UVector3(q2.x - q1.x, q2.y - q1.y, q2.z - q1.z)
        w = UVector3(p1.x - q1.x, p1.y - q1.y, p1.z - q1.z)
        
        # Calculate dot products with rounding for precision
        a = round(u.dot(u), self.round_digits)
        b = round(u.dot(v), self.round_digits)
        c = round(v.dot(v), self.round_digits)
        d = round(u.dot(w), self.round_digits)
        e = round(v.dot(w), self.round_digits)
        
        D = round(a * c - b * b, self.round_digits)
        
        # Check parallelism using angle calculation
        try:
            cos_angle = b / (u.length() * v.length()) if u.length() * v.length() > 0 else 0
            cos_angle = max(-1, min(1, cos_angle))
            radiant = math.acos(abs(cos_angle))
            gap = math.sin(radiant) * min(u.length(), v.length())
        except (ValueError, ZeroDivisionError):
            gap = float('inf')
        
        # Determine if lines are parallel
        if gap < self.tolerance:
            self.is_parallel = True
            sN, sD = 0.0, 1.0
            tN, tD = e, c
        else:
            sN = round(b * e - c * d, self.round_digits)
            tN = round(a * e - b * d, self.round_digits)
            sD = tD = D
            
            if sN < 0.0:
                sN, tN, tD = 0.0, e, c
            elif sN > sD:
                sN, tN, tD = sD, e + b, c
        
        # Handle t parameter constraints
        if tN < 0.0:
            tN = 0.0
            if -d < 0.0:
                sN = 0.0
            elif -d > a:
                sN = sD
            else:
                sN, sD = -d, a
        elif tN > tD:
            tN = tD
            if (-d + b) < 0.0:
                sN = 0.0
            elif (-d + b) > a:
                sN = sD
            else:
                sN, sD = -d + b, a
        
        # Calculate final parameters
        sc = 0.0 if abs(sN) < self.small_num else sN / sD
        tc = 0.0 if abs(tN) < self.small_num else tN / tD
        
        # Get intersection points
        p_point = p1.translate(u * sc)
        q_point = q1.translate(v * tc)
        
        # Calculate distance between closest points
        dp = UVector3(
            (w.x + u.x * sc - v.x * tc),
            (w.y + u.y * sc - v.y * tc), 
            (w.z + u.z * sc - v.z * tc)
        )
        distance = dp.length()
        
        # Check for intersection
        if distance < self.tolerance:
            self.has_intersection = True
            self._process_intersection(p1, p2, q1, q2, sc, tc, p_point, q_point)
            return True
        
        return False
    
    def _reset_state(self):
        """Reset intersection state"""
        self.p_intersections = []
        self.q_intersections = []
        self.is_parallel = False
        self.has_intersection = False
        self.is_collinear = False
        self.is_proper = False
    
    def _process_intersection(self, p1: UPoint, p2: UPoint, q1: UPoint, q2: UPoint,
                            sc: float, tc: float, p_point: UPoint, q_point: UPoint):
        """Process the intersection based on type"""
        if self.is_parallel:
            self.is_collinear = True
            # Handle collinear case
            point_comparer = Point3DComparer(self.tolerance)
            all_points = [p1, p2, q1, q2]
            
            # Sort points along the line
            sorted_points = sorted(all_points, key=lambda pt: (pt.x, pt.y, pt.z))
            
            # Remove duplicates within tolerance
            unique_points = []
            for point in sorted_points:
                is_duplicate = False
                for existing in unique_points:
                    if point.distance_to(existing) <= self.tolerance:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_points.append(point)
            
            # Get overlap (middle points)
            if len(unique_points) > 2:
                overlap_points = unique_points[1:-1]
                for point in overlap_points:
                    self.p_intersections.append(point)
                    self.q_intersections.append(point)
        else:
            # Point intersection
            if 0 < sc < 1 and 0 < tc < 1:
                self.is_proper = True
            
            # Create intersection point
            intersection = UPoint(
                0.5 * (p_point.x + q_point.x),
                0.5 * (p_point.y + q_point.y),
                0.5 * (p_point.z + q_point.z)
            )
            
            self.p_intersections.append(intersection)
            self.q_intersections.append(intersection)