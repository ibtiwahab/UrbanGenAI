# planning_api/geometry/clustering.py
import math
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Point3D:
    """3D Point representation"""
    x: float
    y: float
    z: float = 0.0
    
    def distance_to(self, other: 'Point3D') -> float:
        """Calculate distance to another point"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def translate(self, vector: 'Vector3D') -> 'Point3D':
        """Translate point by vector"""
        return Point3D(self.x + vector.x, self.y + vector.y, self.z + vector.z)


@dataclass
class Vector3D:
    """3D Vector representation"""
    x: float
    y: float
    z: float = 0.0
    
    def length(self) -> float:
        """Calculate vector length"""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Vector3D':
        """Return normalized vector"""
        length = self.length()
        if length == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x / length, self.y / length, self.z / length)
    
    def dot(self, other: 'Vector3D') -> float:
        """Dot product with another vector"""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'Vector3D') -> 'Vector3D':
        """Cross product with another vector"""
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def angle_between(self, other: 'Vector3D') -> float:
        """Calculate angle to another vector in radians"""
        dot_product = self.dot(other)
        lengths = self.length() * other.length()
        if lengths == 0:
            return 0
        cos_angle = max(-1, min(1, dot_product / lengths))
        return math.acos(cos_angle)
    
    def __mul__(self, scalar: float) -> 'Vector3D':
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __add__(self, other: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)


class Cluster:
    """Hierarchical clustering cluster representation"""
    
    def __init__(self, cluster_id: int, x: float = 0, y: float = 0, z: float = 0, 
                 diameter: float = 0, children: List[int] = None, 
                 left_cluster: 'Cluster' = None, right_cluster: 'Cluster' = None):
        self.id = cluster_id
        self.diameter = diameter
        self.children = children or [cluster_id]
        self.left_cluster = left_cluster
        self.right_cluster = right_cluster
        
        # Calculate centroid sum
        if left_cluster and right_cluster:
            self.centroid_sum = Point3D(
                left_cluster.centroid_sum.x + right_cluster.centroid_sum.x,
                left_cluster.centroid_sum.y + right_cluster.centroid_sum.y,
                left_cluster.centroid_sum.z + right_cluster.centroid_sum.z
            )
        else:
            self.centroid_sum = Point3D(x, y, z)
    
    @property
    def count(self) -> int:
        return len(self.children)
    
    @property
    def centroid(self) -> Point3D:
        if self.count == 0:
            return Point3D(0, 0, 0)
        return Point3D(
            self.centroid_sum.x / self.count,
            self.centroid_sum.y / self.count,
            self.centroid_sum.z / self.count
        )


class ClusterPair:
    """Pair of clusters for hierarchical clustering"""
    
    def __init__(self, cluster1: Cluster, cluster2: Cluster):
        self.cluster1 = cluster1
        self.cluster2 = cluster2
    
    def __eq__(self, other):
        if not isinstance(other, ClusterPair):
            return False
        return ((self.cluster1.id == other.cluster1.id and self.cluster2.id == other.cluster2.id) or
                (self.cluster1.id == other.cluster2.id and self.cluster2.id == other.cluster1.id))
    
    def __hash__(self):
        return self.cluster1.id ^ self.cluster2.id


class MultiClusters:
    """Collection of clusters"""
    
    def __init__(self, clusters: List[Cluster] = None):
        self._clusters = set(clusters or [])
    
    @property
    def count(self) -> int:
        return len(self._clusters)
    
    def add(self, cluster: Cluster):
        self._clusters.add(cluster)
    
    def remove(self, cluster: Cluster):
        self._clusters.discard(cluster)
    
    def __iter__(self):
        return iter(self._clusters)
    
    def __getitem__(self, index: int) -> Cluster:
        return list(self._clusters)[index]


class DissimilarityMatrix:
    """Matrix for storing cluster dissimilarities"""
    
    def __init__(self, clusters: MultiClusters, distance_matrix: np.ndarray, diameter: float):
        self._distance_matrix = {}
        self._diameter = diameter
        
        # Build distance matrix for all cluster pairs within diameter
        cluster_list = list(clusters)
        for i in range(len(cluster_list)):
            for j in range(i + 1, len(cluster_list)):
                c1, c2 = cluster_list[i], cluster_list[j]
                dist = distance_matrix[i, j]
                
                if dist <= diameter:
                    pair = ClusterPair(c1, c2)
                    self._distance_matrix[pair] = dist
    
    @property
    def pairs_count(self) -> int:
        return len(self._distance_matrix)
    
    def get_closest_cluster_pair(self) -> Tuple[ClusterPair, float]:
        """Get the closest cluster pair"""
        if not self._distance_matrix:
            raise ValueError("No cluster pairs available")
        
        min_pair = min(self._distance_matrix.items(), key=lambda x: x[1])
        return min_pair[0], min_pair[1]
    
    def update_matrix(self, cluster_pair: ClusterPair, new_cluster_index: int, 
                     clusters: MultiClusters):
        """Update matrix after merging clusters"""
        # Create new merged cluster
        distance = self._distance_matrix[cluster_pair]
        merged = Cluster(
            new_cluster_index, 
            diameter=distance,
            left_cluster=cluster_pair.cluster1,
            right_cluster=cluster_pair.cluster2
        )
        merged.children = cluster_pair.cluster1.children + cluster_pair.cluster2.children
        
        # Remove old cluster pair
        del self._distance_matrix[cluster_pair]
        clusters.remove(cluster_pair.cluster1)
        clusters.remove(cluster_pair.cluster2)
        
        # Update distances to remaining clusters using complete linkage
        for cluster in clusters:
            # Remove old pairs
            pair1 = ClusterPair(cluster, cluster_pair.cluster1)
            pair2 = ClusterPair(cluster, cluster_pair.cluster2)
            
            d1 = self._distance_matrix.pop(pair1, float('inf'))
            d2 = self._distance_matrix.pop(pair2, float('inf'))
            
            # Complete linkage: maximum distance
            complete_dist = max(d1, d2)
            
            if complete_dist != float('inf') and complete_dist <= self._diameter:
                new_pair = ClusterPair(cluster, merged)
                self._distance_matrix[new_pair] = complete_dist
        
        # Add new cluster
        clusters.add(merged)


class AgglomerativeClustering:
    """Hierarchical agglomerative clustering algorithm"""
    
    @staticmethod
    def run(distance_matrix: np.ndarray, diameter: float, 
            coordinates: np.ndarray) -> MultiClusters:
        """Run hierarchical agglomerative clustering"""
        # Step 1: Create singleton clusters
        singleton_count = distance_matrix.shape[0]
        singletons = []
        
        for i in range(singleton_count):
            cluster = Cluster(i, coordinates[i, 0], coordinates[i, 1], 
                            coordinates[i, 2] if coordinates.shape[1] > 2 else 0)
            singletons.append(cluster)
        
        # Step 2: Create multi-clusters container
        clusters = MultiClusters(singletons)
        
        # Step 3: Build dissimilarity matrix
        matrix = DissimilarityMatrix(clusters, distance_matrix, diameter)
        
        # Step 4: Build hierarchical clustering
        new_cluster_index = singleton_count
        AgglomerativeClustering._build_hierarchical_clustering(
            new_cluster_index, diameter, clusters, matrix
        )
        
        return clusters
    
    @staticmethod
    def run_multiple_diameters(distance_matrix: np.ndarray, diameters: List[float], 
                             coordinates: np.ndarray) -> List[MultiClusters]:
        """Run clustering for multiple diameter values"""
        diameters = sorted(set(diameters))
        
        # Create singleton clusters
        singleton_count = distance_matrix.shape[0]
        singletons = []
        
        for i in range(singleton_count):
            cluster = Cluster(i, coordinates[i, 0], coordinates[i, 1], 
                            coordinates[i, 2] if coordinates.shape[1] > 2 else 0)
            singletons.append(cluster)
        
        clusters = MultiClusters(singletons)
        matrix = DissimilarityMatrix(clusters, distance_matrix, max(diameters))
        
        results = []
        new_cluster_index = singleton_count
        
        for diameter in diameters:
            AgglomerativeClustering._build_hierarchical_clustering(
                new_cluster_index, diameter, clusters, matrix
            )
            results.append(MultiClusters(list(clusters)))
            new_cluster_index = clusters.count + singleton_count
        
        return results
    
    @staticmethod
    def _build_hierarchical_clustering(new_cluster_index: int, diameter: float,
                                     clusters: MultiClusters, 
                                     matrix: DissimilarityMatrix):
        """Build hierarchical clustering recursively"""
        while matrix.pairs_count > 0:
            closest_pair, dist = matrix.get_closest_cluster_pair()
            
            if dist < diameter:
                matrix.update_matrix(closest_pair, new_cluster_index, clusters)
                new_cluster_index += 1
            else:
                break


# planning_api/geometry/voronoi.py
import math
import heapq
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VPoint:
    """Voronoi point"""
    x: float
    y: float


@dataclass
class VEdge:
    """Voronoi edge"""
    start: Optional[VPoint] = None
    end: Optional[VPoint] = None
    left: Optional['FortuneSite'] = None
    right: Optional['FortuneSite'] = None
    neighbor: Optional['VEdge'] = None
    slope: Optional[float] = None
    intercept: Optional[float] = None
    slope_rise: float = 0.0
    slope_run: float = 0.0


@dataclass 
class FortuneSite:
    """Site for Fortune's algorithm"""
    x: float
    y: float
    cell: List[VPoint]
    
    def __post_init__(self):
        if not hasattr(self, 'cell') or self.cell is None:
            self.cell = []


class FortuneEvent:
    """Base class for Fortune's algorithm events"""
    def __init__(self, x: float):
        self.x = x
        self.valid = True


class FortuneSiteEvent(FortuneEvent):
    """Site event for Fortune's algorithm"""
    def __init__(self, site: FortuneSite):
        super().__init__(site.x)
        self.site = site
    
    def __lt__(self, other):
        return self.x < other.x


class FortuneCircleEvent(FortuneEvent):
    """Circle event for Fortune's algorithm"""
    def __init__(self, x: float, y: float, arc: 'BeachArc'):
        super().__init__(x)
        self.y = y
        self.arc = arc
    
    def __lt__(self, other):
        if hasattr(other, 'x'):
            return self.x < other.x
        return False


class BeachArc:
    """Beach line arc for Fortune's algorithm"""
    def __init__(self, site: FortuneSite):
        self.site = site
        self.left_edge: Optional[VEdge] = None
        self.right_edge: Optional[VEdge] = None
        self.event: Optional[FortuneCircleEvent] = None
        self.prev: Optional['BeachArc'] = None
        self.next: Optional['BeachArc'] = None


class BeachLine:
    """Beach line for Fortune's algorithm"""
    def __init__(self):
        self.root: Optional[BeachArc] = None
    
    def add_beach_section(self, site_event: FortuneSiteEvent, event_queue: List, 
                         deleted: set, edges: List[VEdge]):
        """Add beach section for site event"""
        site = site_event.site
        
        if not self.root:
            self.root = BeachArc(site)
            return
        
        # Find arc above site
        arc = self._get_arc_above(site.x)
        if not arc:
            return
        
        # Remove false alarm
        if arc.event:
            arc.event.valid = False
            deleted.add(arc.event)
            arc.event = None
        
        # Create new arc
        new_arc = BeachArc(site)
        
        # Split the arc
        self._split_arc(arc, new_arc, edges)
        
        # Check for circle events
        self._check_circle_event(arc, event_queue)
        if new_arc.prev:
            self._check_circle_event(new_arc.prev, event_queue)
        if new_arc.next:
            self._check_circle_event(new_arc.next, event_queue)
    
    def remove_beach_section(self, circle_event: FortuneCircleEvent, 
                           event_queue: List, deleted: set, edges: List[VEdge]):
        """Remove beach section for circle event"""
        arc = circle_event.arc
        if not arc:
            return
        
        # Create vertex
        vertex = VPoint(circle_event.x, circle_event.y)
        
        # End edges
        if arc.left_edge:
            arc.left_edge.end = vertex
        if arc.right_edge:
            arc.right_edge.end = vertex
        
        # Remove arc and update edges
        if arc.prev:
            arc.prev.right_edge = arc.right_edge
        if arc.next:
            arc.next.left_edge = arc.left_edge
        
        # Remove arc from beach line
        if arc.prev:
            arc.prev.next = arc.next
        if arc.next:
            arc.next.prev = arc.prev
        
        # Check for circle events
        if arc.prev:
            self._check_circle_event(arc.prev, event_queue)
        if arc.next:
            self._check_circle_event(arc.next, event_queue)
    
    def _get_arc_above(self, x: float) -> Optional[BeachArc]:
        """Get arc above point x"""
        # Simplified implementation
        return self.root
    
    def _split_arc(self, arc: BeachArc, new_arc: BeachArc, edges: List[VEdge]):
        """Split arc with new arc"""
        # Create new edges
        left_edge = VEdge()
        right_edge = VEdge()
        
        left_edge.left = arc.site
        left_edge.right = new_arc.site
        right_edge.left = new_arc.site  
        right_edge.right = arc.site
        
        edges.extend([left_edge, right_edge])
        
        # Update arc relationships
        new_arc.left_edge = left_edge
        new_arc.right_edge = right_edge
        
        if arc.left_edge:
            arc.left_edge = left_edge
        if arc.right_edge:
            arc.right_edge = right_edge
    
    def _check_circle_event(self, arc: BeachArc, event_queue: List):
        """Check for circle events"""
        if not arc or not arc.prev or not arc.next:
            return
        
        # Calculate circle event (simplified)
        # In full implementation, this would check if three consecutive
        # arcs form a circle event
        pass


class Voronoi:
    """Voronoi diagram generator using Fortune's algorithm"""
    
    def __init__(self, sites: List[FortuneSite], min_x: float, min_y: float, 
                 max_x: float, max_y: float):
        self.sites = sites
        self.bounds = (min_x, min_y, max_x, max_y)
        self._run_fortune_algorithm()
    
    def _run_fortune_algorithm(self):
        """Run Fortune's sweep line algorithm"""
        # Create event queue
        event_queue = []
        for site in self.sites:
            heapq.heappush(event_queue, FortuneSiteEvent(site))
        
        # Initialize beach line and edge list
        beach_line = BeachLine()
        edges = []
        deleted = set()
        
        # Process events
        while event_queue:
            event = heapq.heappop(event_queue)
            
            if isinstance(event, FortuneSiteEvent):
                beach_line.add_beach_section(event, event_queue, deleted, edges)
            elif isinstance(event, FortuneCircleEvent):
                if event not in deleted:
                    beach_line.remove_beach_section(event, event_queue, deleted, edges)
        
        # Clip edges to bounds
        self._clip_edges(edges)
        
        # Build cells
        self._build_cells(edges)
    
    def _clip_edges(self, edges: List[VEdge]):
        """Clip edges to bounding box"""
        min_x, min_y, max_x, max_y = self.bounds
        
        for edge in edges:
            if not edge.end:  # Infinite edge
                # Simplified clipping - extend to boundary
                if edge.start:
                    if edge.slope is not None:
                        # Calculate intersection with boundary
                        if edge.slope_run > 0:
                            edge.end = VPoint(max_x, edge.start.y)
                        else:
                            edge.end = VPoint(min_x, edge.start.y)
                    else:
                        edge.end = VPoint(edge.start.x, max_y)
    
    def _build_cells(self, edges: List[VEdge]):
        """Build Voronoi cells from edges"""
        for edge in edges:
            if edge.left and edge.start and edge.end:
                edge.left.cell.extend([edge.start, edge.end])
            if edge.right and edge.start and edge.end:
                edge.right.cell.extend([edge.start, edge.end])