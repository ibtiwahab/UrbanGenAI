import * as THREE from 'three';
import GridController from './GridController';
import Polyline from './ObjectControllers/Polyline';
import GeometryService from '../Services/GeometryService';

export default class EnhancedController {
    constructor(objectControllers) {
        this._gridController = new GridController();
        this._objectControllers = objectControllers || [];
        this._geometryHelpers = [];
        this._analysisResults = new Map();
        this._backendConnected = false;
        this._visualizationLayers = {
            centroids: [],
            boundingBoxes: [],
            offsets: [],
            clusters: [],
            voronoi: [],
            intersections: []
        };
        
        // Initialize backend connection
        this.initializeBackend();
    }

    async initializeBackend() {
        try {
            const connectionInfo = await GeometryService.testConnection();
            this._backendConnected = connectionInfo.connected;
            console.log('Enhanced Controller - Backend status:', connectionInfo);
        } catch (error) {
            console.error('Failed to test backend connection:', error);
            this._backendConnected = false;
        }
    }

    initializeAndGetObjects() {
        return [...this._gridController.initializeAndGetGrid(), ...this._geometryHelpers];
    }

    getIntersectionToGrid(rayCaster) {
        return this._gridController.getIntersection(rayCaster);
    }

    getIntersection(rayCaster) {
        let closestIntersect = null;

        for (const controller of this._objectControllers) {
            if (!controller.built) continue;
            const intersect = controller.getClosestIntersection(rayCaster);

            if (intersect && (!closestIntersect || rayCaster.ray.origin.distanceTo(intersect) < rayCaster.ray.origin.distanceTo(closestIntersect))) {
                closestIntersect = intersect;
            }
        }

        return closestIntersect || this._gridController.getIntersection(rayCaster);
    }

    getIntersectingObjectController(rayCaster) {
        let closestIntersect = null;
        let objectController = null;

        for (const controller of this._objectControllers) {
            if (!controller.built) continue;
            const intersect = controller.getClosestIntersection(rayCaster);

            if (intersect && (!closestIntersect || rayCaster.ray.origin.distanceTo(intersect) < rayCaster.ray.origin.distanceTo(closestIntersect))) {
                closestIntersect = intersect;
                objectController = controller;
            }
        }

        return objectController;
    }

    add(object) {
        this._objectControllers.push(object);
        
        // Enhanced automatic analysis for polylines
        if (object instanceof Polyline) {
            this.analyzePolylineGeometry(object);
        }
    }

    remove(object) {
        this._objectControllers = this._objectControllers.filter(controller => controller !== object);
        
        // Enhanced cleanup
        this.removeGeometryHelpers(object);
        this.removeAnalysisResults(object);
    }

    // Enhanced geometry analysis with backend integration
    async analyzePolylineGeometry(polyline) {
        try {
            if (typeof polyline.analyzeGeometry === 'function') {
                const analysis = await polyline.analyzeGeometry();
                
                // Store analysis results
                this._analysisResults.set(polyline, {
                    geometry: analysis,
                    validation: polyline.validationInfo,
                    timestamp: Date.now()
                });

                console.log('Enhanced geometry analysis completed:', {
                    area: polyline.getArea ? polyline.getArea() : 'N/A',
                    perimeter: polyline.getPerimeter ? polyline.getPerimeter() : 'N/A',
                    isValid: polyline.isValidGeometry ? polyline.isValidGeometry() : 'N/A',
                    isClosed: polyline.isClosed ? polyline.isClosed() : 'N/A',
                    hasSelfIntersections: polyline.hasSelfIntersections ? polyline.hasSelfIntersections() : 'N/A',
                    qualityScore: polyline.getGeometryQuality ? polyline.getGeometryQuality() : 'N/A',
                    backendConnected: polyline.backendConnected
                });

                return analysis;
            }
        } catch (error) {
            console.error('Failed to analyze polyline geometry:', error);
        }
    }

    // Enhanced validation for all geometries
    async validateAllGeometry() {
        const polylines = this._objectControllers.filter(obj => obj instanceof Polyline);
        const results = [];
        
        for (const polyline of polylines) {
            try {
                if (typeof polyline.validateGeometry === 'function') {
                    const validation = await polyline.validateGeometry();
                    results.push({
                        polyline: polyline,
                        validation: validation,
                        quality: polyline.getGeometryQuality ? polyline.getGeometryQuality() : 0
                    });
                }
            } catch (error) {
                console.error('Failed to validate polyline geometry:', error);
                results.push({
                    polyline: polyline,
                    validation: { is_valid: false, errors: [error.message] },
                    quality: 0
                });
            }
        }

        // Generate summary report
        const summary = this.generateValidationSummary(results);
        console.log('Validation Summary:', summary);
        
        return results;
    }

    generateValidationSummary(results) {
        const total = results.length;
        const valid = results.filter(r => r.validation.is_valid).length;
        const avgQuality = results.reduce((sum, r) => sum + r.quality, 0) / total;
        
        return {
            total: total,
            valid: valid,
            invalid: total - valid,
            validPercentage: ((valid / total) * 100).toFixed(1),
            averageQuality: avgQuality.toFixed(1),
            criticalIssues: results.filter(r => r.quality < 40).length,
            warnings: results.filter(r => r.quality >= 40 && r.quality < 75).length,
            excellent: results.filter(r => r.quality >= 90).length
        };
    }

    // Enhanced offset creation with visualization
    async createOffsetForPolyline(polyline, offsetDistance, offsetType = 'inward') {
        try {
            if (typeof polyline.createOffset === 'function') {
                const offsetLine = await polyline.createOffset(offsetDistance, offsetType);
                
                if (offsetLine) {
                    // Enhanced visualization
                    this.addToVisualizationLayer('offsets', offsetLine);
                    this._geometryHelpers.push(offsetLine);
                    
                    console.log(`Created ${offsetType} offset polyline with distance: ${offsetDistance}`);
                    return offsetLine;
                }
            }
            
            return null;
        } catch (error) {
            console.error('Failed to create offset:', error);
            return null;
        }
    }

    // Enhanced clustering analysis
    async analyzeBuildings(polyline, clusterDiameter = 50.0) {
        if (!this._backendConnected) {
            console.warn('Backend not connected - clustering unavailable');
            return null;
        }

        try {
            if (typeof polyline.analyzeBuildingClusters === 'function') {
                const result = await polyline.analyzeBuildingClusters(clusterDiameter);
                
                if (result && result.clusters) {
                    // Add cluster visualizations to helpers
                    const clusterObjects = polyline.clusterVisualizations;
                    clusterObjects.forEach(obj => {
                        this.addToVisualizationLayer('clusters', obj);
                        this._geometryHelpers.push(obj);
                    });
                    
                    console.log(`Clustering analysis: ${result.cluster_count} clusters found`);
                    return result;
                }
            }
        } catch (error) {
            console.error('Clustering analysis failed:', error);
        }
        
        return null;
    }

    // Enhanced Voronoi generation
    async generateVoronoiDiagram(polyline, seedCount = 10) {
        if (!this._backendConnected) {
            console.warn('Backend not connected - Voronoi generation unavailable');
            return null;
        }

        try {
            if (typeof polyline.generateVoronoiDiagram === 'function') {
                const result = await polyline.generateVoronoiDiagram(seedCount);
                
                if (result && result.cells) {
                    // Add Voronoi visualizations to helpers
                    const voronoiObjects = polyline.voronoiCells;
                    voronoiObjects.forEach(obj => {
                        this.addToVisualizationLayer('voronoi', obj);
                        this._geometryHelpers.push(obj);
                    });
                    
                    console.log(`Voronoi diagram: ${result.site_count} cells generated`);
                    return result;
                }
            }
        } catch (error) {
            console.error('Voronoi generation failed:', error);
        }
        
        return null;
    }

    // Enhanced intersection testing between polylines
    async testPolylineIntersections(polylineA, polylineB) {
        if (!this._backendConnected) {
            console.warn('Backend not connected - intersection testing unavailable');
            return { intersects: false, intersection_type: 'unavailable' };
        }

        try {
            if (typeof polylineA.testIntersectionWith === 'function') {
                const result = await polylineA.testIntersectionWith(polylineB);
                
                // Visualize intersection points if any
                if (result.intersects && result.intersection_points) {
                    this.visualizeIntersectionPoints(result.intersection_points);
                }
                
                console.log('Intersection test completed:', result);
                return result;
            }
        } catch (error) {
            console.error('Intersection test failed:', error);
        }
        
        return { intersects: false, intersection_type: 'error' };
    }

    // Visualization layer management
    addToVisualizationLayer(layerName, object) {
        if (this._visualizationLayers[layerName]) {
            this._visualizationLayers[layerName].push(object);
        }
    }

    clearVisualizationLayer(layerName) {
        if (this._visualizationLayers[layerName]) {
            this._visualizationLayers[layerName].forEach(obj => {
                if (obj.parent) obj.parent.remove(obj);
                if (obj.geometry) obj.geometry.dispose();
                if (obj.material) obj.material.dispose();
            });
            this._visualizationLayers[layerName] = [];
        }
    }

    toggleVisualizationLayer(layerName, visible) {
        if (this._visualizationLayers[layerName]) {
            this._visualizationLayers[layerName].forEach(obj => {
                obj.visible = visible;
            });
        }
    }

    // Enhanced centroid visualization
    showCentroids() {
        this.clearVisualizationLayer('centroids');
        
        const polylines = this._objectControllers.filter(obj => obj instanceof Polyline);
        
        polylines.forEach((polyline, index) => {
            if (typeof polyline.getCentroid === 'function') {
                const centroid = polyline.getCentroid();
                if (centroid) {
                    // Enhanced centroid marker
                    const geometry = new THREE.SphereGeometry(1.5, 12, 8);
                    const material = new THREE.MeshBasicMaterial({ 
                        color: 'yellow',
                        transparent: true,
                        opacity: 0.8
                    });
                    const sphere = new THREE.Mesh(geometry, material);
                    
                    sphere.position.set(centroid.x, centroid.y, centroid.z + 1);
                    
                    // Add text label
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.width = 128;
                    canvas.height = 64;
                    context.fillStyle = 'rgba(0, 0, 0, 0.8)';
                    context.fillRect(0, 0, 128, 64);
                    context.fillStyle = 'white';
                    context.font = '16px Arial';
                    context.textAlign = 'center';
                    context.fillText(`C${index + 1}`, 64, 32);
                    context.fillText(`(${centroid.x.toFixed(1)}, ${centroid.y.toFixed(1)})`, 64, 48);
                    
                    const texture = new THREE.CanvasTexture(canvas);
                    const labelMaterial = new THREE.SpriteMaterial({ map: texture });
                    const sprite = new THREE.Sprite(labelMaterial);
                    sprite.position.set(centroid.x, centroid.y, centroid.z + 3);
                    sprite.scale.set(8, 4, 1);
                    
                    this.addToVisualizationLayer('centroids', sphere);
                    this.addToVisualizationLayer('centroids', sprite);
                    this._geometryHelpers.push(sphere, sprite);
                }
            }
        });
    }

    hideCentroids() {
        this.clearVisualizationLayer('centroids');
        this._geometryHelpers = this._geometryHelpers.filter(helper => {
            return !(helper instanceof THREE.Mesh && helper.geometry instanceof THREE.SphereGeometry);
        });
    }

    // Enhanced bounding box visualization
    showBoundingBoxes() {
        this.clearVisualizationLayer('boundingBoxes');
        
        this._objectControllers.forEach((controller, index) => {
            if (controller.objects) {
                controller.objects.forEach(obj => {
                    // Create enhanced bounding box
                    const box = new THREE.Box3().setFromObject(obj);
                    const helper = new THREE.Box3Helper(box, 0xffff00);
                    helper.material.transparent = true;
                    helper.material.opacity = 0.5;
                    
                    // Add dimensions text
                    const size = box.getSize(new THREE.Vector3());
                    const center = box.getCenter(new THREE.Vector3());
                    
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.width = 256;
                    canvas.height = 128;
                    context.fillStyle = 'rgba(0, 0, 0, 0.8)';
                    context.fillRect(0, 0, 256, 128);
                    context.fillStyle = 'yellow';
                    context.font = '14px Arial';
                    context.textAlign = 'center';
                    context.fillText(`Object ${index + 1}`, 128, 30);
                    context.fillText(`W: ${size.x.toFixed(1)}m`, 64, 60);
                    context.fillText(`H: ${size.y.toFixed(1)}m`, 128, 60);
                    context.fillText(`D: ${size.z.toFixed(1)}m`, 192, 60);
                    context.fillText(`Vol: ${(size.x * size.y * size.z).toFixed(1)}m³`, 128, 90);
                    
                    const texture = new THREE.CanvasTexture(canvas);
                    const labelMaterial = new THREE.SpriteMaterial({ map: texture });
                    const sprite = new THREE.Sprite(labelMaterial);
                    sprite.position.copy(center);
                    sprite.position.z += size.z / 2 + 2;
                    sprite.scale.set(12, 6, 1);
                    
                    this.addToVisualizationLayer('boundingBoxes', helper);
                    this.addToVisualizationLayer('boundingBoxes', sprite);
                    this._geometryHelpers.push(helper, sprite);
                });
            }
        });
    }

    hideBoundingBoxes() {
        this.clearVisualizationLayer('boundingBoxes');
        this._geometryHelpers = this._geometryHelpers.filter(helper => {
            return !(helper instanceof THREE.Box3Helper);
        });
    }

    // Enhanced statistics with backend integration
    getGeometryStatistics() {
        const polylines = this._objectControllers.filter(obj => obj instanceof Polyline);
        
        const stats = {
            totalPolylines: polylines.length,
            validPolylines: 0,
            closedPolylines: 0,
            selfIntersectingPolylines: 0,
            totalArea: 0,
            totalPerimeter: 0,
            averageArea: 0,
            averagePerimeter: 0,
            qualityDistribution: {
                excellent: 0,  // 90-100%
                good: 0,       // 75-89%
                fair: 0,       // 60-74%
                poor: 0,       // 40-59%
                critical: 0    // 0-39%
            },
            backendConnected: this._backendConnected,
            analysisResults: this._analysisResults.size
        };

        polylines.forEach(polyline => {
            if (polyline.isValidGeometry && polyline.isValidGeometry()) stats.validPolylines++;
            if (polyline.isClosed && polyline.isClosed()) stats.closedPolylines++;
            if (polyline.hasSelfIntersections && polyline.hasSelfIntersections()) stats.selfIntersectingPolylines++;
            
            if (polyline.getArea) stats.totalArea += polyline.getArea();
            if (polyline.getPerimeter) stats.totalPerimeter += polyline.getPerimeter();
            
            // Quality distribution
            if (polyline.getGeometryQuality) {
                const quality = polyline.getGeometryQuality();
                if (quality >= 90) stats.qualityDistribution.excellent++;
                else if (quality >= 75) stats.qualityDistribution.good++;
                else if (quality >= 60) stats.qualityDistribution.fair++;
                else if (quality >= 40) stats.qualityDistribution.poor++;
                else stats.qualityDistribution.critical++;
            }
        });

        if (polylines.length > 0) {
            stats.averageArea = stats.totalArea / polylines.length;
            stats.averagePerimeter = stats.totalPerimeter / polylines.length;
        }

        return stats;
    }

    // Advanced analysis methods
    async performBatchAnalysis() {
        console.log('Starting batch analysis of all geometries...');
        
        const polylines = this._objectControllers.filter(obj => obj instanceof Polyline);
        const results = {
            geometryAnalysis: [],
            validationResults: [],
            intersectionMatrix: [],
            clusteringResults: null,
            summary: null
        };

        // Geometry analysis for each polyline
        for (const polyline of polylines) {
            try {
                const analysis = await this.analyzePolylineGeometry(polyline);
                results.geometryAnalysis.push({
                    polyline: polyline,
                    analysis: analysis
                });
            } catch (error) {
                console.error('Batch analysis failed for polyline:', error);
            }
        }

        // Validation analysis
        results.validationResults = await this.validateAllGeometry();

        // Intersection matrix (if backend connected)
        if (this._backendConnected && polylines.length > 1) {
            results.intersectionMatrix = await this.generateIntersectionMatrix(polylines);
        }

        // Generate summary
        results.summary = this.generateAnalysisSummary(results);
        
        console.log('Batch analysis completed:', results.summary);
        return results;
    }

    async generateIntersectionMatrix(polylines) {
        const matrix = [];
        
        for (let i = 0; i < polylines.length; i++) {
            matrix[i] = [];
            for (let j = 0; j < polylines.length; j++) {
                if (i === j) {
                    matrix[i][j] = { intersects: false, intersection_type: 'self' };
                } else if (j < i) {
                    // Use symmetric result
                    matrix[i][j] = matrix[j][i];
                } else {
                    try {
                        const result = await this.testPolylineIntersections(polylines[i], polylines[j]);
                        matrix[i][j] = result;
                    } catch (error) {
                        matrix[i][j] = { intersects: false, intersection_type: 'error' };
                    }
                }
            }
        }
        
        return matrix;
    }

    generateAnalysisSummary(results) {
        const summary = {
            timestamp: new Date().toISOString(),
            geometriesAnalyzed: results.geometryAnalysis.length,
            validGeometries: results.validationResults.filter(r => r.validation.is_valid).length,
            intersections: 0,
            averageQuality: 0,
            recommendations: []
        };

        // Count intersections
        if (results.intersectionMatrix) {
            summary.intersections = results.intersectionMatrix.flat().filter(r => r.intersects).length;
        }

        // Calculate average quality
        const qualities = results.validationResults.map(r => r.quality);
        if (qualities.length > 0) {
            summary.averageQuality = qualities.reduce((sum, q) => sum + q, 0) / qualities.length;
        }

        // Generate recommendations
        if (summary.averageQuality < 60) {
            summary.recommendations.push('Consider reviewing geometry quality - many polygons have issues');
        }
        if (summary.intersections > 0) {
            summary.recommendations.push('Resolve polygon intersections to avoid generation conflicts');
        }
        if (summary.validGeometries < summary.geometriesAnalyzed) {
            summary.recommendations.push('Fix invalid geometries before proceeding with plan generation');
        }

        return summary;
    }

    // Intersection point visualization
    visualizeIntersectionPoints(points) {
        this.clearVisualizationLayer('intersections');
        
        points.forEach((point, index) => {
            const geometry = new THREE.SphereGeometry(0.5, 8, 6);
            const material = new THREE.MeshBasicMaterial({ color: 'red' });
            const sphere = new THREE.Mesh(geometry, material);
            
            sphere.position.set(point[0], point[1], point[2] || 0);
            
            this.addToVisualizationLayer('intersections', sphere);
            this._geometryHelpers.push(sphere);
        });
    }

    // Enhanced cleanup methods
    clearGeometryHelpers() {
        this._geometryHelpers.forEach(helper => {
            if (helper.parent) helper.parent.remove(helper);
            if (helper.geometry) helper.geometry.dispose();
            if (helper.material) helper.material.dispose();
        });
        this._geometryHelpers = [];
        
        // Clear all visualization layers
        Object.keys(this._visualizationLayers).forEach(layerName => {
            this.clearVisualizationLayer(layerName);
        });
    }

    removeGeometryHelpers(object) {
        // Enhanced cleanup for specific object
        if (object instanceof Polyline) {
            // Remove object-specific visualizations
            object.cleanupAllVisualizations();
        }
        
        // Remove from analysis results
        this.removeAnalysisResults(object);
    }

    removeAnalysisResults(object) {
        this._analysisResults.delete(object);
    }

    // Method to refresh all geometry analyses
    async refreshAllGeometry() {
        const polylines = this._objectControllers.filter(obj => obj instanceof Polyline);
        
        for (const polyline of polylines) {
            try {
                if (typeof polyline.refreshGeometryAnalysis === 'function') {
                    await polyline.refreshGeometryAnalysis();
                    
                    // Update stored analysis
                    const analysis = {
                        geometry: polyline.geometryInfo,
                        validation: polyline.validationInfo,
                        timestamp: Date.now()
                    };
                    this._analysisResults.set(polyline, analysis);
                }
            } catch (error) {
                console.error('Failed to refresh geometry for polyline:', error);
            }
        }
    }

    // Enhanced getters for visualization layers
    get geometryHelpers() {
        return this._geometryHelpers;
    }

    get visualizationLayers() {
        return this._visualizationLayers;
    }

    get analysisResults() {
        return this._analysisResults;
    }

    get backendConnected() {
        return this._backendConnected;
    }

    // Layer management utilities
    getLayerObjects(layerName) {
        return this._visualizationLayers[layerName] || [];
    }

    getLayerCount(layerName) {
        return this.getLayerObjects(layerName).length;
    }

    getAllVisualizationObjects() {
        return Object.values(this._visualizationLayers).flat();
    }

    // Enhanced debugging and monitoring
    getSystemStatus() {
        return {
            backendConnected: this._backendConnected,
            totalObjects: this._objectControllers.length,
            polylineCount: this._objectControllers.filter(obj => obj instanceof Polyline).length,
            helperCount: this._geometryHelpers.length,
            analysisResultsCount: this._analysisResults.size,
            visualizationLayers: Object.fromEntries(
                Object.entries(this._visualizationLayers).map(([key, value]) => [key, value.length])
            ),
            memoryUsage: this.estimateMemoryUsage()
        };
    }

    estimateMemoryUsage() {
        let triangleCount = 0;
        let vertexCount = 0;
        
        [...this._objectControllers, ...this._geometryHelpers].forEach(obj => {
            if (obj.objects) {
                obj.objects.forEach(subObj => {
                    if (subObj.geometry) {
                        const positions = subObj.geometry.getAttribute('position');
                        if (positions) vertexCount += positions.count;
                        const indices = subObj.geometry.getIndex();
                        if (indices) triangleCount += indices.count / 3;
                    }
                });
            } else if (obj.geometry) {
                const positions = obj.geometry.getAttribute('position');
                if (positions) vertexCount += positions.count;
                const indices = obj.geometry.getIndex();
                if (indices) triangleCount += indices.count / 3;
            }
        });
        
        return {
            vertices: vertexCount,
            triangles: triangleCount,
            estimatedMB: ((vertexCount * 12 + triangleCount * 12) / (1024 * 1024)).toFixed(2)
        };
    }
}