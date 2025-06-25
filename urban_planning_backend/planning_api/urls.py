# planning_api/urls.py - Complete updated URL configuration
from django.urls import path, include
from .views import GeneratePlanView, GeometryAnalysisView
from .additional_views import (
    GeometryValidationView,
    PolygonOffsetView,
    IntersectionTestView,
    GeometryInfoView
)
from .enhanced_views import EnhancedGeneratePlanView
from .clustering_views import (
    ClusteringAnalysisView,
    VoronoiGenerationView,
    BuildingDistributionView,
    GeometryProcessingView
)
from .algorithms_views import (
    GraphAnalysisView,
    IntervalAnalysisView,
    MathematicsView,
    UtilitiesView
)

urlpatterns = [
    # Main planning endpoints
    path('planning/main/generateplan/', GeneratePlanView.as_view(), name='generate_plan'),
    path('planning/main/enhanced_generateplan/', EnhancedGeneratePlanView.as_view(), name='enhanced_generate_plan'),
    
    # Geometry analysis endpoints
    path('planning/geometry/analyze/', GeometryAnalysisView.as_view(), name='geometry_analysis'),
    path('planning/geometry/validate/', GeometryValidationView.as_view(), name='geometry_validation'),
    path('planning/geometry/offset/', PolygonOffsetView.as_view(), name='polygon_offset'),
    path('planning/geometry/intersection/', IntersectionTestView.as_view(), name='intersection_test'),
    path('planning/geometry/info/', GeometryInfoView.as_view(), name='geometry_info'),
    path('planning/geometry/process/', GeometryProcessingView.as_view(), name='geometry_processing'),
    
    # Enhanced clustering and distribution endpoints
    path('planning/clustering/analyze/', ClusteringAnalysisView.as_view(), name='clustering_analysis'),
    path('planning/clustering/voronoi/', VoronoiGenerationView.as_view(), name='voronoi_generation'),
    path('planning/clustering/distribution/', BuildingDistributionView.as_view(), name='building_distribution'),
    
    # Algorithm endpoints (converted from C#)
    path('planning/algorithms/graph/analysis/', GraphAnalysisView.as_view(), name='graph_analysis'),
    path('planning/algorithms/intervals/analysis/', IntervalAnalysisView.as_view(), name='interval_analysis'),
    path('planning/algorithms/mathematics/', MathematicsView.as_view(), name='mathematics'),
    path('planning/algorithms/utilities/', UtilitiesView.as_view(), name='utilities'),
    
    # Future algorithm endpoints (can be added as needed)
    # path('planning/algorithms/spatial/', SpatialAnalysisView.as_view(), name='spatial_analysis'),
    # path('planning/algorithms/optimization/', OptimizationView.as_view(), name='optimization'),
    # path('planning/algorithms/network/', NetworkAnalysisView.as_view(), name='network_analysis'),
]
