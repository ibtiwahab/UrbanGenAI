# planning_api/algorithms/trees.py
"""
Python implementation of C# tree algorithms
Converted from IntervalTree.cs
"""

from typing import List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import bisect


@dataclass(frozen=True)
class UInterval:
    """
    Interval structure - equivalent to C# UInterval struct
    This is an immutable interval with [low, high] bounds
    """
    low: float
    high: float
    
    def __post_init__(self):
        if self.low > self.high:
            raise ValueError(f"Invalid interval: low ({self.low}) > high ({self.high})")
    
    def is_overlap(self, other: 'UInterval') -> bool:
        """Check if this interval overlaps with another"""
        return self.low <= other.high and other.low <= self.high
    
    def contains(self, value: float) -> bool:
        """Check if interval contains a value"""
        return self.low <= value <= self.high
    
    def contains_interval(self, other: 'UInterval') -> bool:
        """Check if this interval completely contains another"""
        return self.low <= other.low and other.high <= self.high
    
    def intersection(self, other: 'UInterval') -> Optional['UInterval']:
        """Get intersection with another interval"""
        if not self.is_overlap(other):
            return None
        return UInterval(max(self.low, other.low), min(self.high, other.high))
    
    def union(self, other: 'UInterval') -> 'UInterval':
        """Get union with another interval (works even if not overlapping)"""
        return UInterval(min(self.low, other.low), max(self.high, other.high))
    
    @property
    def length(self) -> float:
        """Get interval length"""
        return self.high - self.low
    
    @property
    def midpoint(self) -> float:
        """Get interval midpoint"""
        return (self.low + self.high) / 2
    
    def __str__(self) -> str:
        return f"[{self.low},{self.high}]"
    
    def __repr__(self) -> str:
        return f"UInterval({self.low}, {self.high})"


class IntervalNode:
    """
    Interval node class for interval tree
    Contains interval, id, and max value for tree operations
    """
    
    def __init__(self, interval: UInterval, node_id: int):
        self.interval = interval
        self.id = node_id
        self.max = interval.high  # Initialize max to interval's high value
    
    def update_max(self, new_max: float):
        """Update the max value for this node"""
        self.max = new_max
    
    def change_interval(self, new_interval: UInterval):
        """Change the interval for this node"""
        self.interval = new_interval
        self.max = max(self.max, new_interval.high)
    
    def is_overlap(self, other: 'IntervalNode') -> bool:
        """Check if this node's interval overlaps with another node's interval"""
        return self.interval.is_overlap(other.interval)
    
    def __lt__(self, other: 'IntervalNode') -> bool:
        """Comparison for tree ordering - first by low value, then by id"""
        if self.interval.low != other.interval.low:
            return self.interval.low < other.interval.low
        return self.id < other.id
    
    def __eq__(self, other: 'IntervalNode') -> bool:
        """Equality based on interval and id"""
        if not isinstance(other, IntervalNode):
            return False
        return self.interval == other.interval and self.id == other.id
    
    def __hash__(self) -> int:
        return hash((self.interval.low, self.interval.high, self.id))
    
    def __str__(self) -> str:
        return f"Id:{self.id} {self.interval} Max:{self.max}"
    
    def __repr__(self) -> str:
        return f"IntervalNode({self.interval}, {self.id})"


class Color(Enum):
    """Colors for Red-Black tree nodes"""
    RED = "RED"
    BLACK = "BLACK"


class RBTreeNode:
    """Red-Black tree node"""
    
    def __init__(self, value: IntervalNode, color: Color = Color.RED):
        self.value = value
        self.color = color
        self.left: Optional['RBTreeNode'] = None
        self.right: Optional['RBTreeNode'] = None
        self.parent: Optional['RBTreeNode'] = None
    
    @property
    def left_child(self) -> Optional['RBTreeNode']:
        """Get left child (alias for compatibility)"""
        return self.left
    
    @property
    def right_child(self) -> Optional['RBTreeNode']:
        """Get right child (alias for compatibility)"""
        return self.right
    
    def is_red(self) -> bool:
        """Check if node is red"""
        return self.color == Color.RED
    
    def is_black(self) -> bool:
        """Check if node is black"""
        return self.color == Color.BLACK
    
    def set_red(self):
        """Set node color to red"""
        self.color = Color.RED
    
    def set_black(self):
        """Set node color to black"""
        self.color = Color.BLACK


class RBTree:
    """
    Red-Black tree implementation for interval tree
    Simplified version focusing on interval tree requirements
    """
    
    def __init__(self, allow_duplicates: bool = False):
        self.root: Optional[RBTreeNode] = None
        self.count = 0
        self.allow_duplicates = allow_duplicates
    
    def insert(self, value: IntervalNode) -> bool:
        """Insert a node into the tree"""
        if self.root is None:
            self.root = RBTreeNode(value, Color.BLACK)
            self.count += 1
            return True
        
        # Find insertion point
        current = self.root
        parent = None
        
        while current is not None:
            parent = current
            if value < current.value:
                current = current.left
            elif value > current.value or self.allow_duplicates:
                current = current.right
            else:
                # Duplicate found and duplicates not allowed
                return False
        
        # Create new node
        new_node = RBTreeNode(value, Color.RED)
        new_node.parent = parent
        
        # Insert as child of parent
        if value < parent.value:
            parent.left = new_node
        else:
            parent.right = new_node
        
        # Fix Red-Black tree properties
        self._fix_insertion(new_node)
        self.count += 1
        return True
    
    def remove(self, value: IntervalNode) -> bool:
        """Remove a node from the tree"""
        node = self._find_node(value)
        if node is None:
            return False
        
        self._delete_node(node)
        self.count -= 1
        return True
    
    def find(self, value: IntervalNode) -> Optional[RBTreeNode]:
        """Find a node in the tree"""
        return self._find_node(value)
    
    def _find_node(self, value: IntervalNode) -> Optional[RBTreeNode]:
        """Internal method to find a node"""
        current = self.root
        while current is not None:
            if value == current.value:
                return current
            elif value < current.value:
                current = current.left
            else:
                current = current.right
        return None
    
    def _fix_insertion(self, node: RBTreeNode):
        """Fix Red-Black tree properties after insertion"""
        while node != self.root and node.parent.is_red():
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right
                
                if uncle is not None and uncle.is_red():
                    # Case 1: Uncle is red
                    node.parent.set_black()
                    uncle.set_black()
                    node.parent.parent.set_red()
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        # Case 2: Node is right child
                        node = node.parent
                        self._rotate_left(node)
                    
                    # Case 3: Node is left child
                    node.parent.set_black()
                    node.parent.parent.set_red()
                    self._rotate_right(node.parent.parent)
            else:
                # Mirror cases
                uncle = node.parent.parent.left
                
                if uncle is not None and uncle.is_red():
                    node.parent.set_black()
                    uncle.set_black()
                    node.parent.parent.set_red()
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self._rotate_right(node)
                    
                    node.parent.set_black()
                    node.parent.parent.set_red()
                    self._rotate_left(node.parent.parent)
        
        self.root.set_black()
    
    def _rotate_left(self, node: RBTreeNode):
        """Left rotation"""
        right_child = node.right
        node.right = right_child.left
        
        if right_child.left is not None:
            right_child.left.parent = node
        
        right_child.parent = node.parent
        
        if node.parent is None:
            self.root = right_child
        elif node == node.parent.left:
            node.parent.left = right_child
        else:
            node.parent.right = right_child
        
        right_child.left = node
        node.parent = right_child
    
    def _rotate_right(self, node: RBTreeNode):
        """Right rotation"""
        left_child = node.left
        node.left = left_child.right
        
        if left_child.right is not None:
            left_child.right.parent = node
        
        left_child.parent = node.parent
        
        if node.parent is None:
            self.root = left_child
        elif node == node.parent.right:
            node.parent.right = left_child
        else:
            node.parent.left = left_child
        
        left_child.right = node
        node.parent = left_child
    
    def _delete_node(self, node: RBTreeNode):
        """Delete a node from the tree (simplified implementation)"""
        # Simplified deletion - in a full implementation, this would
        # properly handle Red-Black tree deletion with fixup
        if node.left is None and node.right is None:
            # Leaf node
            if node.parent is None:
                self.root = None
            elif node == node.parent.left:
                node.parent.left = None
            else:
                node.parent.right = None
        elif node.left is None:
            # Only right child
            self._replace_node(node, node.right)
        elif node.right is None:
            # Only left child
            self._replace_node(node, node.left)
        else:
            # Two children - find inorder successor
            successor = self._find_min(node.right)
            node.value = successor.value
            self._delete_node(successor)
    
    def _replace_node(self, old_node: RBTreeNode, new_node: Optional[RBTreeNode]):
        """Replace old node with new node"""
        if old_node.parent is None:
            self.root = new_node
        elif old_node == old_node.parent.left:
            old_node.parent.left = new_node
        else:
            old_node.parent.right = new_node
        
        if new_node is not None:
            new_node.parent = old_node.parent
    
    def _find_min(self, node: RBTreeNode) -> RBTreeNode:
        """Find minimum node in subtree"""
        while node.left is not None:
            node = node.left
        return node


class IntervalTree:
    """
    Augmented Red-Black tree for interval intersection queries
    """
    
    def __init__(self):
        self._interval_tree = RBTree(allow_duplicates=False)
    
    @property
    def count(self) -> int:
        """Get number of intervals in tree"""
        return self._interval_tree.count
    
    @property
    def root(self) -> Optional[RBTreeNode]:
        """Get root node"""
        return self._interval_tree.root
    
    def insert_node(self, node: IntervalNode) -> bool:
        """Insert an interval node into the tree"""
        success = self._interval_tree.insert(node)
        if success:
            self._update_tree(self.root)
        return success
    
    def insert_interval(self, interval: UInterval, node_id: int) -> bool:
        """Insert an interval with given ID"""
        node = IntervalNode(interval, node_id)
        return self.insert_node(node)
    
    def delete_node(self, node: IntervalNode) -> bool:
        """Delete an interval node from the tree"""
        success = self._interval_tree.remove(node)
        if success and self.root is not None:
            self._update_tree(self.root)
        return success
    
    def delete_interval(self, interval: UInterval, node_id: int) -> bool:
        """Delete an interval with given ID"""
        node = IntervalNode(interval, node_id)
        return self.delete_node(node)
    
    def search_overlaps(self, target_node: IntervalNode) -> List[IntervalNode]:
        """
        Find all intervals that overlap with the target interval
        """
        result = []
        if self.root is not None:
            self._search_overlaps_recursive(target_node, self.root, result)
        return result
    
    def search_overlapping_interval(self, interval: UInterval) -> List[IntervalNode]:
        """Find all intervals that overlap with given interval"""
        target_node = IntervalNode(interval, -1)  # Temporary node for search
        return self.search_overlaps(target_node)
    
    def find_one_overlap(self, target_node: IntervalNode) -> Optional[IntervalNode]:
        """
        Find one interval that overlaps with target (faster than finding all)
        """
        node = self.root
        
        while node is not None:
            if node.value.is_overlap(target_node):
                return node.value
            elif node.left is None:
                node = node.right
            elif node.left.value.max < target_node.interval.low:
                node = node.right
            else:
                node = node.left
        
        return None
    
    def find_overlapping_interval(self, interval: UInterval) -> Optional[IntervalNode]:
        """Find one interval that overlaps with given interval"""
        target_node = IntervalNode(interval, -1)
        return self.find_one_overlap(target_node)
    
    def search_point(self, point: float) -> List[IntervalNode]:
        """Find all intervals that contain the given point"""
        point_interval = UInterval(point, point)
        return self.search_overlapping_interval(point_interval)
    
    def search_contained(self, container_interval: UInterval) -> List[IntervalNode]:
        """Find all intervals completely contained within the given interval"""
        result = []
        if self.root is not None:
            self._search_contained_recursive(container_interval, self.root, result)
        return result
    
    def get_all_intervals(self) -> List[IntervalNode]:
        """Get all intervals in the tree (in sorted order)"""
        result = []
        if self.root is not None:
            self._inorder_traversal(self.root, result)
        return result
    
    def _search_overlaps_recursive(self, target_node: IntervalNode, 
                                 current_node: RBTreeNode, result: List[IntervalNode]):
        """Recursive helper for overlap search"""
        if current_node.value.is_overlap(target_node):
            result.append(current_node.value)
        
        # Go left if left subtree might contain overlaps
        if (current_node.left is not None and 
            current_node.left.value.max >= target_node.interval.low):
            self._search_overlaps_recursive(target_node, current_node.left, result)
        
        # Go right if right subtree might contain overlaps
        if (current_node.right is not None and 
            current_node.right.value.max >= target_node.interval.low and
            current_node.value.interval.low <= target_node.interval.high):
            self._search_overlaps_recursive(target_node, current_node.right, result)
    
    def _search_contained_recursive(self, container: UInterval, 
                                  current_node: RBTreeNode, result: List[IntervalNode]):
        """Recursive helper for contained interval search"""
        if container.contains_interval(current_node.value.interval):
            result.append(current_node.value)
        
        # Continue search in both subtrees if they might contain relevant intervals
        if current_node.left is not None and current_node.left.value.max >= container.low:
            self._search_contained_recursive(container, current_node.left, result)
        
        if (current_node.right is not None and 
            current_node.value.interval.low <= container.high):
            self._search_contained_recursive(container, current_node.right, result)
    
    def _inorder_traversal(self, node: RBTreeNode, result: List[IntervalNode]):
        """Inorder traversal helper"""
        if node.left is not None:
            self._inorder_traversal(node.left, result)
        
        result.append(node.value)
        
        if node.right is not None:
            self._inorder_traversal(node.right, result)
    
    def _update_tree(self, node: Optional[RBTreeNode]) -> float:
        """
        Update max values in the tree after insertion/deletion
        Returns the max value for the subtree rooted at node
        """
        if node is None:
            return float('-inf')
        
        # Recursively update children and get their max values
        left_max = self._update_tree(node.left)
        right_max = self._update_tree(node.right)
        
        # Calculate max for current node
        current_max = max(
            node.value.interval.high,
            left_max if left_max != float('-inf') else node.value.interval.high,
            right_max if right_max != float('-inf') else node.value.interval.high
        )
        
        # Update node's max value
        node.value.update_max(current_max)
        
        return current_max


class IntervalTreeOperations:
    """Additional operations for interval trees"""
    
    @staticmethod
    def merge_overlapping_intervals(intervals: List[UInterval]) -> List[UInterval]:
        """Merge all overlapping intervals in a list"""
        if not intervals:
            return []
        
        # Sort intervals by start time
        sorted_intervals = sorted(intervals, key=lambda x: x.low)
        merged = [sorted_intervals[0]]
        
        for current in sorted_intervals[1:]:
            last_merged = merged[-1]
            
            if current.low <= last_merged.high:
                # Overlapping intervals - merge them
                merged[-1] = UInterval(last_merged.low, max(last_merged.high, current.high))
            else:
                # Non-overlapping interval
                merged.append(current)
        
        return merged
    
    @staticmethod
    def find_gaps(intervals: List[UInterval], search_range: UInterval) -> List[UInterval]:
        """Find gaps between intervals within a search range"""
        if not intervals:
            return [search_range]
        
        # Merge overlapping intervals first
        merged = IntervalTreeOperations.merge_overlapping_intervals(intervals)
        
        # Filter intervals that intersect with search range
        relevant_intervals = []
        for interval in merged:
            if interval.is_overlap(search_range):
                # Clip interval to search range
                clipped = UInterval(
                    max(interval.low, search_range.low),
                    min(interval.high, search_range.high)
                )
                relevant_intervals.append(clipped)
        
        if not relevant_intervals:
            return [search_range]
        
        # Sort by start time
        relevant_intervals.sort(key=lambda x: x.low)
        
        gaps = []
        
        # Check for gap before first interval
        if relevant_intervals[0].low > search_range.low:
            gaps.append(UInterval(search_range.low, relevant_intervals[0].low))
        
        # Check for gaps between intervals
        for i in range(len(relevant_intervals) - 1):
            current_end = relevant_intervals[i].high
            next_start = relevant_intervals[i + 1].low
            
            if current_end < next_start:
                gaps.append(UInterval(current_end, next_start))
        
        # Check for gap after last interval
        last_end = relevant_intervals[-1].high
        if last_end < search_range.high:
            gaps.append(UInterval(last_end, search_range.high))
        
        return gaps
    
    @staticmethod
    def interval_union(intervals: List[UInterval]) -> List[UInterval]:
        """Compute union of all intervals (same as merge_overlapping_intervals)"""
        return IntervalTreeOperations.merge_overlapping_intervals(intervals)
    
    @staticmethod
    def interval_intersection(intervals1: List[UInterval], 
                            intervals2: List[UInterval]) -> List[UInterval]:
        """Compute intersection of two sets of intervals"""
        result = []
        
        for interval1 in intervals1:
            for interval2 in intervals2:
                intersection = interval1.intersection(interval2)
                if intersection is not None:
                    result.append(intersection)
        
        # Merge overlapping results
        return IntervalTreeOperations.merge_overlapping_intervals(result)


# Example usage and testing
def test_interval_tree():
    """Test interval tree functionality"""
    print("Testing Interval Tree:")
    
    # Create interval tree
    tree = IntervalTree()
    
    # Test intervals
    intervals = [
        (UInterval(1, 3), 1),
        (UInterval(2, 4), 2),
        (UInterval(5, 7), 3),
        (UInterval(6, 8), 4),
        (UInterval(10, 12), 5),
    ]
    
    # Insert intervals
    print("  Inserting intervals:")
    for interval, node_id in intervals:
        success = tree.insert_interval(interval, node_id)
        print(f"    {interval} (ID: {node_id}): {'Success' if success else 'Failed'}")
    
    print(f"  Tree count: {tree.count}")
    
    # Test overlap search
    test_interval = UInterval(3, 6)
    overlaps = tree.search_overlapping_interval(test_interval)
    print(f"  Overlaps with {test_interval}:")
    for node in overlaps:
        print(f"    {node}")
    
    # Test point search
    test_point = 2.5
    containing = tree.search_point(test_point)
    print(f"  Intervals containing point {test_point}:")
    for node in containing:
        print(f"    {node}")
    
    # Test finding one overlap
    one_overlap = tree.find_overlapping_interval(test_interval)
    print(f"  One overlap with {test_interval}: {one_overlap}")


def test_interval_operations():
    """Test interval operations"""
    print("\nTesting Interval Operations:")
    
    intervals = [
        UInterval(1, 3),
        UInterval(2, 5),
        UInterval(7, 9),
        UInterval(8, 10),
        UInterval(12, 15)
    ]
    
    print("  Original intervals:")
    for interval in intervals:
        print(f"    {interval}")
    
    # Test merging
    merged = IntervalTreeOperations.merge_overlapping_intervals(intervals)
    print("  Merged intervals:")
    for interval in merged:
        print(f"    {interval}")
    
    # Test finding gaps
    search_range = UInterval(0, 20)
    gaps = IntervalTreeOperations.find_gaps(intervals, search_range)
    print(f"  Gaps in range {search_range}:")
    for gap in gaps:
        print(f"    {gap}")


if __name__ == "__main__":
    test_interval_tree()
    test_interval_operations()