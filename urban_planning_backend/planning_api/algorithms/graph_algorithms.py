# planning_api/algorithms/graph_algorithms.py
"""
Python implementation of C# graph algorithms for urban planning
Converted from C# files: DijkstraShortestPaths.cs, CalculateCentrality.cs, etc.
"""

import heapq
import math
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict, deque
from abc import ABC, abstractmethod
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class Edge:
    """Represents an edge in a weighted graph"""
    
    def __init__(self, from_vertex: int, to_vertex: int, weight: float = 1.0):
        self.from_vertex = from_vertex
        self.to_vertex = to_vertex
        self.weight = weight
        self._weights = {'default': weight}
    
    def either(self) -> int:
        """Return one endpoint of the edge"""
        return self.from_vertex
    
    def other(self, vertex: int) -> int:
        """Return the other endpoint of the edge"""
        if vertex == self.from_vertex:
            return self.to_vertex
        elif vertex == self.to_vertex:
            return self.from_vertex
        else:
            raise ValueError(f"Vertex {vertex} is not an endpoint of this edge")
    
    def get_weight(self, weight_type: str = 'default') -> float:
        """Get edge weight by type"""
        return self._weights.get(weight_type, self.weight)
    
    def set_weight(self, weight_type: str, value: float):
        """Set edge weight by type"""
        self._weights[weight_type] = value
        if weight_type == 'default':
            self.weight = value


class DirectedEdge(Edge):
    """Represents a directed edge"""
    
    def __init__(self, from_vertex: int, to_vertex: int, weight: float = 1.0):
        super().__init__(from_vertex, to_vertex, weight)
    
    def get_reversed_edge(self) -> 'DirectedEdge':
        """Get the reversed edge"""
        reversed_edge = DirectedEdge(self.to_vertex, self.from_vertex, self.weight)
        reversed_edge._weights = self._weights.copy()
        return reversed_edge


class IGraph(ABC):
    """Interface for graph implementations"""
    
    @abstractmethod
    def vertices_count(self) -> int:
        pass
    
    @abstractmethod
    def edges_count(self) -> int:
        pass
    
    @abstractmethod
    def has_vertex(self, vertex: Any) -> bool:
        pass
    
    @abstractmethod
    def vertices(self) -> List[Any]:
        pass
    
    @abstractmethod
    def edges(self) -> List[Edge]:
        pass


class IWeightedGraph(ABC):
    """Interface for weighted graph implementations"""
    
    @abstractmethod
    def outgoing_edges(self, vertex: Any) -> List[Edge]:
        pass


class EdgeWeightedGraph:
    """Undirected weighted graph implementation"""
    
    def __init__(self, vertex_count: int = 0):
        self._vertex_count = vertex_count
        self._edge_count = 0
        self._adjacency_list: Dict[int, List[Edge]] = defaultdict(list)
    
    @property
    def V(self) -> int:
        """Number of vertices"""
        return self._vertex_count
    
    @property
    def E(self) -> int:
        """Number of edges"""
        return self._edge_count
    
    def add_vertice(self):
        """Add a new vertex"""
        self._vertex_count += 1
    
    def add_edge(self, edge: Edge):
        """Add an edge to the graph"""
        v = edge.from_vertex
        w = edge.to_vertex
        
        self._adjacency_list[v].append(edge)
        self._adjacency_list[w].append(edge)
        self._edge_count += 1
    
    def adj(self, vertex: int) -> List[Edge]:
        """Get adjacent edges for a vertex"""
        return self._adjacency_list.get(vertex, [])


class EdgeWeightedDigraph:
    """Directed weighted graph implementation"""
    
    def __init__(self, vertex_count: int = 0):
        self._vertex_count = vertex_count
        self._edge_count = 0
        self._adjacency_list: Dict[int, List[DirectedEdge]] = defaultdict(list)
    
    @property
    def V(self) -> int:
        """Number of vertices"""
        return self._vertex_count
    
    @property
    def E(self) -> int:
        """Number of edges"""
        return self._edge_count
    
    def add_vertice(self):
        """Add a new vertex"""
        self._vertex_count += 1
    
    def add_edge(self, edge: DirectedEdge):
        """Add a directed edge to the graph"""
        self._adjacency_list[edge.from_vertex].append(edge)
        self._edge_count += 1
    
    def adj(self, vertex: int) -> List[DirectedEdge]:
        """Get adjacent edges for a vertex"""
        return self._adjacency_list.get(vertex, [])


class MinPriorityQueue:
    """Min priority queue implementation using heapq"""
    
    def __init__(self, capacity: int = None):
        self._heap = []
        self._entry_map = {}
        self._counter = 0
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._heap) == 0
    
    def enqueue(self, item: Any, priority: float):
        """Add item with priority"""
        if item in self._entry_map:
            self.update_priority(item, priority)
            return
        
        entry = [priority, self._counter, item]
        self._entry_map[item] = entry
        heapq.heappush(self._heap, entry)
        self._counter += 1
    
    def dequeue_min(self) -> Any:
        """Remove and return item with minimum priority"""
        while self._heap:
            priority, count, item = heapq.heappop(self._heap)
            if item is not None:
                del self._entry_map[item]
                return item
        raise IndexError("Priority queue is empty")
    
    def contains(self, item: Any) -> bool:
        """Check if item is in queue"""
        return item in self._entry_map and self._entry_map[item][2] is not None
    
    def update_priority(self, item: Any, new_priority: float):
        """Update priority of existing item"""
        if item in self._entry_map:
            # Mark old entry as removed
            old_entry = self._entry_map[item]
            old_entry[2] = None
            
            # Add new entry
            entry = [new_priority, self._counter, item]
            self._entry_map[item] = entry
            heapq.heappush(self._heap, entry)
            self._counter += 1


class DijkstraShortestPaths:
    """
    Computes Dijkstra's shortest paths for directed weighted graphs
    from a single source to all destinations
    """
    
    INFINITY = float('inf')
    NONE_PREDECESSOR = -1
    
    def __init__(self, graph: 'GraphAdapter', source: Any):
        if not graph.has_vertex(source):
            raise ValueError("The source vertex doesn't exist in this graph")
        
        # Check for negative weights
        for edge in graph.edges():
            if edge.weight < 0:
                raise ValueError("Negative edge weight detected")
        
        self._graph = graph
        self._source = source
        self._vertices = graph.vertices()
        self._vertices_count = len(self._vertices)
        
        # Create vertex to index mapping
        self._nodes_to_indices = {vertex: i for i, vertex in enumerate(self._vertices)}
        
        # Initialize arrays
        self._distances = [self.INFINITY] * self._vertices_count
        self._predecessors = [self.NONE_PREDECESSOR] * self._vertices_count
        self._min_priority_queue = MinPriorityQueue(self._vertices_count)
        
        self._initialize()
        self._dijkstra()
    
    def _initialize(self):
        """Initialize distances and priority queue"""
        source_index = self._nodes_to_indices[self._source]
        self._distances[source_index] = 0
        self._min_priority_queue.enqueue(self._source, 0)
    
    def _dijkstra(self):
        """Main Dijkstra algorithm implementation"""
        while not self._min_priority_queue.is_empty():
            current_vertex = self._min_priority_queue.dequeue_min()
            current_vertex_index = self._nodes_to_indices[current_vertex]
            
            outgoing_edges = self._graph.outgoing_edges(current_vertex)
            
            for edge in outgoing_edges:
                adjacent_vertex = edge.to_vertex if hasattr(edge, 'to_vertex') else edge.other(current_vertex)
                adjacent_index = self._nodes_to_indices[adjacent_vertex]
                
                # Calculate new distance
                if self._distances[current_vertex_index] != self.INFINITY:
                    delta = self._distances[current_vertex_index] + edge.weight
                else:
                    delta = self.INFINITY
                
                if delta < self._distances[adjacent_index]:
                    # Update distance and predecessor
                    self._distances[adjacent_index] = delta
                    self._predecessors[adjacent_index] = current_vertex_index
                    
                    if self._min_priority_queue.contains(adjacent_vertex):
                        self._min_priority_queue.update_priority(adjacent_vertex, delta)
                    else:
                        self._min_priority_queue.enqueue(adjacent_vertex, delta)
    
    def has_path_to(self, destination: Any) -> bool:
        """Check if path exists to destination"""
        return self.distance_to(destination) != self.INFINITY
    
    def distance_to(self, destination: Any) -> float:
        """Get distance to destination"""
        if destination not in self._nodes_to_indices:
            raise ValueError("Graph doesn't have the specified vertex")
        
        index = self._nodes_to_indices[destination]
        return self._distances[index]
    
    def shortest_path_to(self, destination: Any) -> Optional[List[Any]]:
        """Get shortest path to destination"""
        if not self.has_path_to(destination):
            return None
        
        dest_index = self._nodes_to_indices[destination]
        path = []
        
        # Reconstruct path from destination to source
        current_index = dest_index
        while self._distances[current_index] != 0:
            path.append(self._vertices[current_index])
            current_index = self._predecessors[current_index]
        
        # Add source vertex
        path.append(self._vertices[current_index])
        
        # Reverse to get path from source to destination
        path.reverse()
        return path


class DepthFirstSearch:
    """Depth-first search for finding connected components"""
    
    def __init__(self, graph: EdgeWeightedGraph):
        self.groups = [-1] * graph.V
        self.group_list: List[Set[int]] = []
        
        for v in range(graph.V):
            if self.groups[v] >= 0:
                continue
            
            self.group_list.append(set())
            self._dfs(graph, v, len(self.group_list) - 1)
    
    def get_main_group_vertices(self) -> Optional[Set[int]]:
        """Get the largest connected component"""
        if not self.group_list:
            return None
        
        max_size = 0
        max_set = None
        
        for vertex_set in self.group_list:
            if len(vertex_set) > max_size:
                max_size = len(vertex_set)
                max_set = vertex_set
        
        return max_set
    
    def _dfs(self, graph: EdgeWeightedGraph, v: int, flag: int):
        """Recursive depth-first search"""
        self.groups[v] = flag
        self.group_list[flag].add(v)
        
        for edge in graph.adj(v):
            w = edge.other(v)
            if self.groups[w] < 0:
                self._dfs(graph, w, flag)


class CentralitySingleSource:
    """
    Internal class for computing betweenness centrality for a single source
    """
    
    INFINITY = float('inf')
    
    def __init__(self, graph: 'GraphAdapter', source: Any, vertices_to_indices: Dict[Any, int], 
                 radius: float = float('inf'), sub_indices: List[int] = None):
        
        self._graph = graph
        self._source = source
        self._vertices = graph.vertices()
        self._nodes_to_indices = vertices_to_indices
        self._sub_indices = sub_indices
        self._radius = radius
        
        # Determine working vertex set
        if sub_indices is not None:
            count = len(sub_indices)
            indices = sub_indices
        else:
            count = len(self._vertices)
            indices = list(range(count))
        
        # Initialize data structures
        self._predecessors: Dict[int, List[int]] = {i: [] for i in indices}
        self._distances: Dict[int, float] = {i: self.INFINITY for i in indices}
        self._min_priority_queue = MinPriorityQueue(count)
        
        # Betweenness calculation structures
        self._stack = []
        self._sigma: Dict[int, int] = {i: 0 for i in indices}
        self._delta: Dict[int, float] = {i: 0.0 for i in indices}
        
        self.betweenness_score: Dict[Any, float] = {self._vertices[i]: 0.0 for i in indices}
        
        self._initialize(indices)
        self._dijkstra()
        self.vertices_within_radius = self._stack.copy()
        self._accumulation()
        
        self.total_depth_score, self.node_count = self._get_total_depth()
    
    def _initialize(self, indices: List[int]):
        """Initialize data structures"""
        source_index = self._nodes_to_indices[self._source]
        
        self._distances[source_index] = 0
        self._min_priority_queue.enqueue(source_index, 0)
        self._sigma[source_index] = 1
    
    def _dijkstra(self):
        """Modified Dijkstra for betweenness centrality"""
        while not self._min_priority_queue.is_empty():
            current_vertex_index = self._min_priority_queue.dequeue_min()
            self._stack.append(current_vertex_index)
            
            current_vertex = self._vertices[current_vertex_index]
            outgoing_edges = self._graph.outgoing_edges(current_vertex)
            
            # Get predecessors of current node
            predecessors = self._predecessors[current_vertex_index]
            
            for edge in outgoing_edges:
                adjacent_vertex = edge.to_vertex if hasattr(edge, 'to_vertex') else edge.other(current_vertex)
                adjacent_index = self._nodes_to_indices[adjacent_vertex]
                
                # Check if vertex is in subgraph
                if self._sub_indices is not None and adjacent_index not in self._sub_indices:
                    continue
                
                # Skip if already processed
                if adjacent_index in self._stack:
                    continue
                
                # Space syntax constraints
                if predecessors:
                    # Adjacent vertex shouldn't be a predecessor
                    if adjacent_index in predecessors:
                        continue
                    
                    # Check for cycles in space syntax
                    if self._forms_cycle(predecessors, adjacent_index):
                        continue
                
                dist = round(self._distances[current_vertex_index] + edge.weight, 6)
                
                if dist <= self._radius:
                    if dist < self._distances[adjacent_index]:
                        # Shorter path found
                        self._distances[adjacent_index] = dist
                        
                        if self._min_priority_queue.contains(adjacent_index):
                            self._min_priority_queue.update_priority(adjacent_index, dist)
                        else:
                            self._min_priority_queue.enqueue(adjacent_index, dist)
                        
                        # Update sigma and predecessors
                        self._sigma[adjacent_index] = self._sigma[current_vertex_index]
                        self._predecessors[adjacent_index] = [current_vertex_index]
                    
                    elif dist == self._distances[adjacent_index]:
                        # Equal distance path found
                        self._sigma[adjacent_index] += self._sigma[current_vertex_index]
                        self._predecessors[adjacent_index].append(current_vertex_index)
    
    def _forms_cycle(self, predecessors: List[int], adjacent_index: int) -> bool:
        """Check if adding adjacent vertex would form a cycle (for space syntax)"""
        for pred in predecessors:
            if self._graph.has_edge(self._vertices[pred], self._vertices[adjacent_index]):
                return True
        return False
    
    def _accumulation(self):
        """Accumulate betweenness scores"""
        source_index = self._nodes_to_indices[self._source]
        
        while self._stack:
            current_vertex_index = self._stack.pop()
            
            if self._sigma[current_vertex_index] > 0:
                coeff = (1.0 + self._delta[current_vertex_index]) / self._sigma[current_vertex_index]
            else:
                coeff = 0.0
            
            # Update predecessors
            for pred_index in self._predecessors[current_vertex_index]:
                self._delta[pred_index] += self._sigma[pred_index] * coeff
            
            # Add to betweenness score (exclude source)
            if current_vertex_index != source_index:
                vertex = self._vertices[current_vertex_index]
                self.betweenness_score[vertex] += self._delta[current_vertex_index]
    
    def _get_total_depth(self) -> Tuple[float, int]:
        """Calculate total depth and node count"""
        total_depth = 0.0
        node_count = 0
        
        for distance in self._distances.values():
            if distance != self.INFINITY:
                total_depth += distance
                node_count += 1
        
        return total_depth, node_count


class CalculateCentrality:
    """
    Calculate centrality measures in a graph
    """
    
    def __init__(self, graph: 'GraphAdapter', radius: float = float('inf'), 
                 sub_graphs: List[List[int]] = None):
        
        self._graph = graph
        self._vertices = graph.vertices()
        self._vertices_to_indices = {vertex: i for i, vertex in enumerate(self._vertices)}
        self._sub_graphs = sub_graphs
        self._radius = radius
        
        # Results
        self.betweenness: Dict[Any, float] = {vertex: 0.0 for vertex in self._vertices}
        self.total_depths: Dict[Any, float] = {}
        self.node_counts: Dict[Any, int] = {}
        self.sub_graphs_result: List[List[int]] = [[] for _ in self._vertices]
        
        self._compute()
    
    def _compute(self):
        """Main computation method"""
        vertices_count = len(self._vertices)
        
        if vertices_count >= 30:
            # Use parallel processing for large graphs
            self._compute_parallel()
        else:
            # Sequential processing for small graphs
            self._compute_sequential()
    
    def _compute_sequential(self):
        """Sequential computation"""
        for source in self._vertices:
            source_index = self._vertices_to_indices[source]
            sub_id = self._sub_graphs[source_index] if self._sub_graphs else None
            
            centrality = CentralitySingleSource(
                self._graph, source, self._vertices_to_indices, self._radius, sub_id
            )
            
            # Accumulate betweenness scores
            for vertex, score in centrality.betweenness_score.items():
                self.betweenness[vertex] += score
            
            # Store other metrics
            self.total_depths[source] = centrality.total_depth_score
            self.node_counts[source] = centrality.node_count
            
            # Store sub-graph if radius is finite
            if self._radius != float('inf'):
                self.sub_graphs_result[source_index] = centrality.vertices_within_radius
    
    def _compute_parallel(self):
        """Parallel computation using ThreadPoolExecutor"""
        lock = threading.Lock()
        
        def process_vertex(source):
            source_index = self._vertices_to_indices[source]
            sub_id = self._sub_graphs[source_index] if self._sub_graphs else None
            
            centrality = CentralitySingleSource(
                self._graph, source, self._vertices_to_indices, self._radius, sub_id
            )
            
            return source, source_index, centrality
        
        with ThreadPoolExecutor(max_workers=30) as executor:
            future_to_vertex = {executor.submit(process_vertex, source): source 
                              for source in self._vertices}
            
            for future in as_completed(future_to_vertex):
                source, source_index, centrality = future.result()
                
                # Thread-safe accumulation
                with lock:
                    for vertex, score in centrality.betweenness_score.items():
                        self.betweenness[vertex] += score
                
                # Store metrics (no lock needed as each source is unique)
                self.total_depths[source] = centrality.total_depth_score
                self.node_counts[source] = centrality.node_count
                
                if self._radius != float('inf'):
                    self.sub_graphs_result[source_index] = centrality.vertices_within_radius


class GraphAdapter:
    """Adapter class to make graphs compatible with centrality algorithms"""
    
    def __init__(self, vertices: List[Any], edges: List[Edge]):
        self._vertices = vertices
        self._edges = edges
        self._adjacency_map: Dict[Any, List[Edge]] = defaultdict(list)
        
        # Build adjacency map
        for edge in edges:
            if hasattr(edge, 'from_vertex') and hasattr(edge, 'to_vertex'):
                # Directed edge
                self._adjacency_map[edge.from_vertex].append(edge)
            else:
                # Undirected edge
                v = edge.either()
                w = edge.other(v)
                self._adjacency_map[v].append(edge)
                self._adjacency_map[w].append(edge)
    
    def vertices(self) -> List[Any]:
        """Get all vertices"""
        return self._vertices.copy()
    
    def edges(self) -> List[Edge]:
        """Get all edges"""
        return self._edges.copy()
    
    def has_vertex(self, vertex: Any) -> bool:
        """Check if vertex exists"""
        return vertex in self._vertices
    
    def has_edge(self, vertex1: Any, vertex2: Any) -> bool:
        """Check if edge exists between two vertices"""
        for edge in self._adjacency_map.get(vertex1, []):
            if hasattr(edge, 'to_vertex'):
                if edge.to_vertex == vertex2:
                    return True
            else:
                if edge.other(vertex1) == vertex2:
                    return True
        return False
    
    def outgoing_edges(self, vertex: Any) -> List[Edge]:
        """Get outgoing edges from vertex"""
        return self._adjacency_map.get(vertex, [])
    
    def vertices_count(self) -> int:
        """Get number of vertices"""
        return len(self._vertices)
    
    def edges_count(self) -> int:
        """Get number of edges"""
        return len(self._edges)


# Example usage and testing functions
def create_sample_graph() -> GraphAdapter:
    """Create a sample graph for testing"""
    vertices = [0, 1, 2, 3, 4]
    edges = [
        Edge(0, 1, 2.0),
        Edge(1, 2, 3.0),
        Edge(2, 3, 1.0),
        Edge(3, 4, 2.0),
        Edge(0, 4, 5.0)
    ]
    
    return GraphAdapter(vertices, edges)


def test_dijkstra():
    """Test Dijkstra's algorithm"""
    graph = create_sample_graph()
    dijkstra = DijkstraShortestPaths(graph, 0)
    
    print("Dijkstra Test Results:")
    for vertex in graph.vertices():
        if dijkstra.has_path_to(vertex):
            distance = dijkstra.distance_to(vertex)
            path = dijkstra.shortest_path_to(vertex)
            print(f"Distance to {vertex}: {distance}, Path: {path}")
        else:
            print(f"No path to {vertex}")


def test_centrality():
    """Test centrality calculation"""
    graph = create_sample_graph()
    centrality = CalculateCentrality(graph)
    
    print("\nCentrality Test Results:")
    for vertex in graph.vertices():
        betweenness = centrality.betweenness[vertex]
        total_depth = centrality.total_depths.get(vertex, 0)
        node_count = centrality.node_counts.get(vertex, 0)
        print(f"Vertex {vertex}: Betweenness={betweenness:.3f}, "
              f"TotalDepth={total_depth:.3f}, NodeCount={node_count}")


if __name__ == "__main__":
    test_dijkstra()
    test_centrality()