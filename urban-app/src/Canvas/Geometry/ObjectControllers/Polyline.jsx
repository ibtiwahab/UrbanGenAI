import * as THREE from 'three';
import Base from './Base';
import EqualHeightsPolygon from './EqualHeightsPolygon';
import FlatPolygon from './FlatPolygon';
import GeneratedPlan from './GeneratedPlan/Controller';
import GeneratePlanOption from '../../Popup/Options/GeneratePlan';
import EnhancedGeneratedPlanParameters from './GeneratedPlan/Parameters';
import GeneratedPlanSettingsMenuComponent from './Settings/Menus/GeneratedPlan/Component';
import GeometryService from '../../Services/GeometryService';

export default class Polyline extends Base {
    static DEFAULT_LINE_COLOR = "green";
    static VALID_COLOR = "green";
    static WARNING_COLOR = "orange";
    static ERROR_COLOR = "red";
    static ANALYZING_COLOR = "blue";
    static PROCESSING_COLOR = "purple";

    constructor(line, settingsComponent) {
        line.material = new THREE.LineBasicMaterial({ color: Polyline.DEFAULT_LINE_COLOR });
        super([line], [], settingsComponent);
        this._line = line;
        this._generatedPlanController = null;
        this._geometryCache = null;
        this._validationCache = null;
        this._offsetLines = [];
        this._triangles = [];
        this._voronoiCells = [];
        this._clusterVisualizations = [];
        this._isAnalyzing = false;
        this._isProcessing = false;
        this._backendConnected = false;
        
        // Enhanced caching system
        this._cacheExpiry = 300000; // 5 minutes
        this._lastCacheUpdate = 0;
        
        // Initialize and test backend connection
        this.initializeBackendConnection();
    }

    async initializeBackendConnection() {
        try {
            const connectionInfo = await GeometryService.testConnection();
            this._backendConnected = connectionInfo.connected;
            
            if (this._backendConnected) {
                console.log('Backend connected:', connectionInfo);
                await this.analyzeGeometry();
            } else {
                console.warn('Backend not available:', connectionInfo.error);
            }
        } catch (error) {
            console.error('Failed to test backend connection:', error);
            this._backendConnected = false;
        }
    }

    getFlattenedVertices() {
        const geometry = this._line.geometry;
        const positions = geometry.getAttribute('position');
        return positions ? Array.from(positions.array) : [];
    }

    // Enhanced geometry analysis with caching
    async analyzeGeometry() {
        if (this._isAnalyzing) return this._geometryCache;
        
        // Check cache first
        if (this._geometryCache && 
            Date.now() - this._lastCacheUpdate < this._cacheExpiry) {
            return this._geometryCache;
        }
        
        this._isAnalyzing = true;
        this.highlight(Polyline.ANALYZING_COLOR);

        try {
            const flattenedVertices = this.getFlattenedVertices();
            
            if (flattenedVertices.length < 9) {
                console.warn('Insufficient vertices for geometry analysis');
                this.unhighlight();
                this._isAnalyzing = false;
                return {};
            }

            GeometryService.validateVertices(flattenedVertices);

            if (!this._backendConnected) {
                // Use mock analysis if backend not available
                this._geometryCache = this.getMockGeometryAnalysis(flattenedVertices);
            } else {
                // Use backend analysis
                const result = await GeometryService.analyzeGeometry(flattenedVertices, 'analyze');
                this._geometryCache = result;
            }
            
            this._lastCacheUpdate = Date.now();
            console.log('Geometry analysis result:', this._geometryCache);
            
            // Update visual feedback
            await this.validateGeometry(); // This will update the visual feedback
            
            this._isAnalyzing = false;
            return this._geometryCache;
            
        } catch (error) {
            console.error('Geometry analysis failed:', error);
            this.highlight(Polyline.ERROR_COLOR);
            this._isAnalyzing = false;
            return {};
        }
    }

    // Enhanced geometry validation
    async validateGeometry() {
        if (!this._backendConnected) {
            // Use mock validation
            this._validationCache = this.getMockValidation();
            this.updateVisualFeedback(this._validationCache);
            return this._validationCache;
        }

        try {
            const flattenedVertices = this.getFlattenedVertices();
            GeometryService.validateVertices(flattenedVertices);

            const result = await GeometryService.validateGeometry(flattenedVertices, {
                tolerance: 1e-6,
                check_closure: true,
                check_self_intersection: true,
                check_planarity: true
            });

            this._validationCache = result;
            console.log('Geometry validation result:', result);
            
            this.updateVisualFeedback(result);
            return result;
            
        } catch (error) {
            console.error('Geometry validation failed:', error);
            this.highlight(Polyline.ERROR_COLOR);
            return { is_valid: false, errors: [error.message] };
        }
    }

    // Enhanced offset creation with better error handling
    async createOffset(offsetDistance, offsetType = 'inward') {
        if (!this._backendConnected) {
            console.warn('Backend not connected - offset operation unavailable');
            return null;
        }

        try {
            this.highlight(Polyline.PROCESSING_COLOR);
            
            const flattenedVertices = this.getFlattenedVertices();
            GeometryService.validateVertices(flattenedVertices);

            const result = await GeometryService.createOffset(flattenedVertices, offsetDistance, {
                offset_type: offsetType,
                tolerance: 1e-6
            });

            if (result.success && result.offset_vertices && result.offset_vertices.length >= 9) {
                const offsetGeometry = new THREE.BufferGeometry();
                const positions = new Float32Array(result.offset_vertices);
                offsetGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
                
                const offsetMaterial = new THREE.LineBasicMaterial({ 
                    color: offsetType === 'inward' ? 'blue' : 'purple',
                    linewidth: 2 
                });
                
                const offsetLine = new THREE.Line(offsetGeometry, offsetMaterial);
                this._offsetLines.push(offsetLine);
                
                console.log(`Created ${offsetType} offset polyline with distance ${offsetDistance}`);
                this.unhighlight();
                return offsetLine;
            } else {
                console.warn('Offset operation failed:', result.error_message);
                this.unhighlight();
                return null;
            }
            
        } catch (error) {
            console.error('Geometry offset failed:', error);
            this.unhighlight();
            return null;
        }
    }

    // Enhanced intersection testing
    async testIntersectionWith(otherPolyline) {
        if (!this._backendConnected) {
            console.warn('Backend not connected - intersection testing unavailable');
            return { intersects: false, intersection_type: 'unavailable' };
        }

        try {
            const verticesA = this.getFlattenedVertices();
            const verticesB = otherPolyline.getFlattenedVertices();
            
            GeometryService.validateVertices(verticesA);
            GeometryService.validateVertices(verticesB);

            const result = await GeometryService.testIntersection(verticesA, verticesB, {
                tolerance: 1e-6
            });

            console.log('Intersection test result:', result);
            return result;
            
        } catch (error) {
            console.error('Intersection test failed:', error);
            return { intersects: false, intersection_type: 'error' };
        }
    }

    // Building clustering analysis
    async analyzeBuildingClusters(clusterDiameter = 50.0) {
        if (!this._backendConnected) {
            console.warn('Backend not connected - clustering analysis unavailable');
            return null;
        }

        try {
            this.highlight(Polyline.PROCESSING_COLOR);
            
            const flattenedVertices = this.getFlattenedVertices();
            GeometryService.validateVertices(flattenedVertices);

            const result = await GeometryService.analyzeBuildings(flattenedVertices, {
                cluster_diameter: clusterDiameter
            });

            if (result.success && result.clusters) {
                console.log(`Building clustering: ${result.cluster_count} clusters found`);
                
                // Visualize clusters
                this.visualizeClusters(result.clusters);
                this.unhighlight();
                return result;
            } else {
                console.warn('Clustering analysis failed');
                this.unhighlight();
                return null;
            }
            
        } catch (error) {
            console.error('Clustering analysis failed:', error);
            this.unhighlight();
            return null;
        }
    }

    // Voronoi diagram generation
    async generateVoronoiDiagram(seedCount = 10) {
        if (!this._backendConnected) {
            console.warn('Backend not connected - Voronoi generation unavailable');
            return null;
        }

        try {
            this.highlight(Polyline.PROCESSING_COLOR);
            
            const flattenedVertices = this.getFlattenedVertices();
            GeometryService.validateVertices(flattenedVertices);

            const result = await GeometryService.generateVoronoi(flattenedVertices, {
                seed_count: seedCount
            });

            if (result.success && result.cells) {
                console.log(`Voronoi diagram: ${result.site_count} cells generated`);
                
                // Visualize Voronoi cells
                this.visualizeVoronoi(result.cells);
                this.unhighlight();
                return result;
            } else {
                console.warn('Voronoi generation failed');
                this.unhighlight();
                return null;
            }
            
        } catch (error) {
            console.error('Voronoi generation failed:', error);
            this.unhighlight();
            return null;
        }
    }

    // Building distribution optimization
    async optimizeBuildingDistribution(options = {}) {
        if (!this._backendConnected) {
            console.warn('Backend not connected - distribution optimization unavailable');
            return null;
        }

        try {
            this.highlight(Polyline.PROCESSING_COLOR);
            
            const flattenedVertices = this.getFlattenedVertices();
            GeometryService.validateVertices(flattenedVertices);

            const result = await GeometryService.optimizeBuildingDistribution(flattenedVertices, {
                target_density: options.target_density || 0.5,
                min_spacing: options.min_spacing || 5.0,
                building_positions: options.building_positions || []
            });

            if (result.success) {
                console.log('Building distribution optimized:', result);
                this.unhighlight();
                return result;
            } else {
                console.warn('Distribution optimization failed');
                this.unhighlight();
                return null;
            }
            
        } catch (error) {
            console.error('Distribution optimization failed:', error);
            this.unhighlight();
            return null;
        }
    }

    // Advanced geometry processing
    async processGeometry(operation, options = {}) {
        if (!this._backendConnected) {
            console.warn('Backend not connected - advanced processing unavailable');
            return null;
        }

        try {
            this.highlight(Polyline.PROCESSING_COLOR);
            
            const flattenedVertices = this.getFlattenedVertices();
            GeometryService.validateVertices(flattenedVertices);

            const result = await GeometryService.processGeometry(flattenedVertices, operation, options);

            if (result.success) {
                console.log(`Geometry ${operation} completed:`, result);
                this.unhighlight();
                return result;
            } else {
                console.warn(`Geometry ${operation} failed:`, result.error_message);
                this.unhighlight();
                return null;
            }
            
        } catch (error) {
            console.error(`Geometry ${operation} failed:`, error);
            this.unhighlight();
            return null;
        }
    }

    // Enhanced plan generation with all backend features
    async generateAndGetPlan(generatedPlanParameters) {
        const flattenedVertices = this.getFlattenedVertices();

        if (flattenedVertices.length < 9) {
            throw new Error('Insufficient vertices for plan generation (minimum 3 points required)');
        }

        // Enhanced validation before plan generation
        if (this._backendConnected) {
            const validation = await this.validateGeometry();
            if (validation.self_intersects) {
                throw new Error('Cannot generate plan: polygon self-intersects. Please fix the geometry first.');
            }

            if (!validation.is_valid) {
                const errorMsg = validation.errors ? validation.errors.join(', ') : 'Invalid geometry';
                throw new Error(`Cannot generate plan: ${errorMsg}`);
            }

            if (!validation.is_closed) {
                console.warn('Warning: Polygon is not closed. Results may be unexpected.');
            }
        }

        try {
            // Use enhanced plan generation
            const result = await GeometryService.generatePlan(flattenedVertices, generatedPlanParameters);
            console.log('Enhanced plan generation response:', result);
            return result;
        } catch (error) {
            let errorMessage = error.message;
            
            if (errorMessage.includes('self-intersects')) {
                errorMessage += '\n\nGeometry Issue: The polygon intersects itself. Please redraw without crossing lines.';
            } else if (errorMessage.includes('Insufficient vertices')) {
                errorMessage += '\n\nGeometry Issue: Need at least 3 points to create a valid polygon.';
            } else if (errorMessage.includes('Unable to connect') || errorMessage.includes('timeout')) {
                errorMessage += '\n\nConnection Issue: Please check that the Django server is running on http://localhost:8000';
            }
            
            throw new Error(errorMessage);
        }
    }

    // Visualization methods for advanced features
    visualizeClusters(clusters) {
        this.clearClusterVisualizations();
        
        clusters.forEach((cluster, index) => {
            // Create sphere at cluster centroid
            const geometry = new THREE.SphereGeometry(2, 16, 12);
            const material = new THREE.MeshBasicMaterial({ 
                color: this.getClusterColor(index),
                transparent: true,
                opacity: 0.7
            });
            const sphere = new THREE.Mesh(geometry, material);
            
            sphere.position.set(cluster.centroid.x, cluster.centroid.y, cluster.centroid.z);
            this._clusterVisualizations.push(sphere);

            // Create circle to show cluster diameter
            const circleGeometry = new THREE.RingGeometry(
                cluster.diameter / 2 - 0.5, 
                cluster.diameter / 2, 
                32
            );
            const circleMaterial = new THREE.MeshBasicMaterial({ 
                color: this.getClusterColor(index),
                transparent: true,
                opacity: 0.3,
                side: THREE.DoubleSide
            });
            const circle = new THREE.Mesh(circleGeometry, circleMaterial);
            
            circle.position.set(cluster.centroid.x, cluster.centroid.y, cluster.centroid.z);
            circle.rotation.x = -Math.PI / 2; // Lay flat
            this._clusterVisualizations.push(circle);
        });
    }

    visualizeVoronoi(cells) {
        this.clearVoronoiVisualizations();
        
        cells.forEach((cell, index) => {
            if (cell.vertices && cell.vertices.length >= 9) {
                // Create geometry from cell vertices
                const geometry = new THREE.BufferGeometry();
                const positions = new Float32Array(cell.vertices);
                geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
                
                // Create wireframe for cell boundaries
                const edges = new THREE.EdgesGeometry(geometry);
                const lineMaterial = new THREE.LineBasicMaterial({ 
                    color: this.getVoronoiColor(index),
                    transparent: true,
                    opacity: 0.8
                });
                const wireframe = new THREE.LineSegments(edges, lineMaterial);
                this._voronoiCells.push(wireframe);

                // Create filled polygon for cell area
                const fillMaterial = new THREE.MeshBasicMaterial({ 
                    color: this.getVoronoiColor(index),
                    transparent: true,
                    opacity: 0.2,
                    side: THREE.DoubleSide
                });
                
                // Simple triangulation for fill (assumes convex polygon)
                if (cell.vertices.length >= 9) {
                    const indices = [];
                    for (let i = 1; i < (cell.vertices.length / 3) - 1; i++) {
                        indices.push(0, i, i + 1);
                    }
                    geometry.setIndex(indices);
                    
                    const fill = new THREE.Mesh(geometry, fillMaterial);
                    this._voronoiCells.push(fill);
                }

                // Add site marker
                if (cell.site) {
                    const siteGeometry = new THREE.CircleGeometry(1, 8);
                    const siteMaterial = new THREE.MeshBasicMaterial({ 
                        color: 'red'
                    });
                    const siteMarker = new THREE.Mesh(siteGeometry, siteMaterial);
                    siteMarker.position.set(cell.site.x, cell.site.y, 0.1);
                    this._voronoiCells.push(siteMarker);
                }
            }
        });
    }

    // Color utilities for visualizations
    getClusterColor(index) {
        const colors = [
            0xff6b6b, 0x4ecdc4, 0x45b7d1, 0xf9ca24, 
            0xf0932b, 0xeb4d4b, 0x6ab04c, 0x9b59b6
        ];
        return colors[index % colors.length];
    }

    getVoronoiColor(index) {
        const colors = [
            0x74b9ff, 0x0984e3, 0xa29bfe, 0x6c5ce7,
            0xfd79a8, 0xe17055, 0x00b894, 0x00cec9
        ];
        return colors[index % colors.length];
    }

    // Cleanup methods
    clearClusterVisualizations() {
        this._clusterVisualizations.forEach(obj => {
            if (obj.parent) obj.parent.remove(obj);
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) obj.material.dispose();
        });
        this._clusterVisualizations = [];
    }

    clearVoronoiVisualizations() {
        this._voronoiCells.forEach(obj => {
            if (obj.parent) obj.parent.remove(obj);
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) obj.material.dispose();
        });
        this._voronoiCells = [];
    }

    cleanupOffsetLines() {
        this._offsetLines.forEach(line => {
            if (line.parent) line.parent.remove(line);
            if (line.geometry) line.geometry.dispose();
            if (line.material) line.material.dispose();
        });
        this._offsetLines = [];
    }

    cleanupTriangles() {
        this._triangles.forEach(triangle => {
            if (triangle.parent) triangle.parent.remove(triangle);
            if (triangle.geometry) triangle.geometry.dispose();
            if (triangle.material) triangle.material.dispose();
        });
        this._triangles = [];
    }

    cleanupAllVisualizations() {
        this.cleanupOffsetLines();
        this.cleanupTriangles();
        this.clearClusterVisualizations();
        this.clearVoronoiVisualizations();
    }

    // Mock methods for when backend is not available
    getMockGeometryAnalysis(flattenedVertices) {
        const points = [];
        for (let i = 0; i < flattenedVertices.length; i += 3) {
            points.push({
                x: flattenedVertices[i],
                y: flattenedVertices[i + 1],
                z: flattenedVertices[i + 2]
            });
        }

        // Calculate area using shoelace formula
        let area = 0;
        for (let i = 0; i < points.length - 1; i++) {
            area += (points[i].x * points[i + 1].y - points[i + 1].x * points[i].y);
        }
        area = Math.abs(area) / 2;

        // Calculate perimeter
        let perimeter = 0;
        for (let i = 0; i < points.length - 1; i++) {
            const dx = points[i + 1].x - points[i].x;
            const dy = points[i + 1].y - points[i].y;
            perimeter += Math.sqrt(dx * dx + dy * dy);
        }

        // Calculate centroid
        const centroid = {
            x: points.reduce((sum, p) => sum + p.x, 0) / points.length,
            y: points.reduce((sum, p) => sum + p.y, 0) / points.length,
            z: points.reduce((sum, p) => sum + p.z, 0) / points.length
        };

        return {
            area: area,
            perimeter: perimeter,
            centroid: centroid,
            is_valid: points.length >= 3,
            main_orientation: 0.0 // Simplified
        };
    }

    getMockValidation() {
        const geometryInfo = this._geometryCache || {};
        return {
            is_valid: true,
            errors: [],
            warnings: [],
            polygon_area: geometryInfo.area || 0,
            polygon_perimeter: geometryInfo.perimeter || 0,
            is_closed: true,
            is_planar: true,
            self_intersects: false
        };
    }

    // Enhanced visual feedback
    updateVisualFeedback(geometryInfo) {
        if (!geometryInfo) {
            this.unhighlight();
            return;
        }

        // Priority: Errors > Warnings > Valid
        if (geometryInfo.self_intersects || (geometryInfo.errors && geometryInfo.errors.length > 0)) {
            this.highlight(Polyline.ERROR_COLOR);
        } else if (!geometryInfo.is_closed || (geometryInfo.warnings && geometryInfo.warnings.length > 0)) {
            this.highlight(Polyline.WARNING_COLOR);
        } else if (geometryInfo.is_valid) {
            this.highlight(Polyline.VALID_COLOR);
        } else {
            this.unhighlight();
        }
    }

    // Enhanced plan generation method
    generatePlan(addCallback, removeCallback) {
        let generatedPlanParameters = new EnhancedGeneratedPlanParameters();
        if (this._generatedPlanController) {
            generatedPlanParameters = this._generatedPlanController.parameters;
        }

        console.log('Generating plan with enhanced backend...', generatedPlanParameters.toBackendFormat());

        this.generateAndGetPlan(generatedPlanParameters).then(result => {
            console.log('Enhanced plan generated successfully:', result);
            
            const objectControllers = [];
            const buildingLayers = [];

            // Process building layers with enhanced error handling
            try {
                for (let i = 0; i < result.buildingLayersVertices.length; i++) {
                    for (let j = 0; j < result.buildingLayersVertices[i].length; j++) {
                        const vertices = [];
                        let z = 0;
                        const height = result.buildingLayersHeights[i][j];

                        if (result.buildingLayersVertices[i][j].length % 3 !== 0) {
                            console.warn(`Invalid vertices array length for building ${i}, floor ${j}`);
                            continue;
                        }

                        for (let k = 0; k < result.buildingLayersVertices[i][j].length; k += 3) {
                            vertices.push(new THREE.Vector2(
                                result.buildingLayersVertices[i][j][k],
                                result.buildingLayersVertices[i][j][k + 1]
                            ));
                            z = result.buildingLayersVertices[i][j][k + 2];
                        }

                        if (vertices.length >= 3) {
                            const buildingLayer = new EqualHeightsPolygon(
                                this._settingsComponent, 
                                vertices, 
                                height, 
                                'red', 
                                z
                            );
                            buildingLayer.built = true;
                            buildingLayers.push(buildingLayer);
                            objectControllers.push(buildingLayer);
                        }
                    }
                }
            } catch (error) {
                console.error('Error processing building layers:', error);
            }

            // Process sub-sites
            const subSites = [];
            try {
                for (let i = 0; i < result.subSiteVertices.length; i++) {
                    const vertices = [];
                    let z = 0;

                    if (result.subSiteVertices[i].length % 3 !== 0) {
                        console.warn(`Invalid sub-site vertices array length for site ${i}`);
                        continue;
                    }

                    for (let j = 0; j < result.subSiteVertices[i].length; j += 3) {
                        vertices.push(new THREE.Vector2(
                            result.subSiteVertices[i][j],
                            result.subSiteVertices[i][j + 1]
                        ));
                        z = result.subSiteVertices[i][j + 2];
                    }

                    if (vertices.length >= 3) {
                        const subSite = new FlatPolygon(this._settingsComponent, vertices, 'grey', z);
                        subSite.built = true;
                        subSites.push(subSite);
                        objectControllers.push(subSite);
                    }
                }
            } catch (error) {
                console.error('Error processing sub-sites:', error);
            }

            // Process setbacks
            const subSiteSetbacks = [];
            try {
                for (let i = 0; i < result.subSiteSetbackVertices.length; i++) {
                    const vertices = [];
                    let z = 0;

                    if (result.subSiteSetbackVertices[i].length % 3 !== 0) {
                        console.warn(`Invalid setback vertices array length for setback ${i}`);
                        continue;
                    }

                    for (let j = 0; j < result.subSiteSetbackVertices[i].length; j += 3) {
                        vertices.push(new THREE.Vector2(
                            result.subSiteSetbackVertices[i][j],
                            result.subSiteSetbackVertices[i][j + 1]
                        ));
                        z = result.subSiteSetbackVertices[i][j + 2];
                    }

                    if (vertices.length >= 3) {
                        const subSiteSetback = new FlatPolygon(this._settingsComponent, vertices, 'green', z);
                        subSiteSetback.built = true;
                        subSiteSetbacks.push(subSiteSetback);
                        objectControllers.push(subSiteSetback);
                    }
                }
            } catch (error) {
                console.error('Error processing setbacks:', error);
            }

            // Update the generated plan controller
            if (this._generatedPlanController) removeCallback([this._generatedPlanController]);
            this._generatedPlanController = new GeneratedPlan(
                this._settingsComponent, 
                generatedPlanParameters, 
                buildingLayers, 
                subSites, 
                subSiteSetbacks
            );
            addCallback(objectControllers);
            
        }).catch(error => {
            console.error('Enhanced plan generation failed:', error);
            alert(error.message);
        });
    }

    // Getters for frontend integration
    get polyline() {
        return this._line;
    }

    get generatedPlanController() {
        return this._generatedPlanController;
    }

    get geometryInfo() {
        return this._geometryCache;
    }

    get validationInfo() {
        return this._validationCache;
    }

    get backendConnected() {
        return this._backendConnected;
    }

    get offsetLines() {
        return this._offsetLines;
    }

    get clusterVisualizations() {
        return this._clusterVisualizations;
    }

    get voronoiCells() {
        return this._voronoiCells;
    }

    // Enhanced popup options
    getPopupOptions() {
        const options = super.getPopupOptions();

        const flattenedVertices = this.getFlattenedVertices();
        if (flattenedVertices.length >= 9) {
            options.push(new GeneratePlanOption(this));
        }

        return options;
    }

    // Enhanced highlight methods
    highlight(color) {
        this._line.material = new THREE.LineBasicMaterial({ color });
    }

    unhighlight() {
        this._line.material = new THREE.LineBasicMaterial({ color: Polyline.DEFAULT_LINE_COLOR });
    }

    // Settings integration
    populateAndActivateSettingsComponent(addCallback, removeCallback) {
        if (!this._generatedPlanController) {
            this._settingsComponent.setMenus([]);
            return;
        }

        const generatedPlanSettingsMenuComponent = (
            <GeneratedPlanSettingsMenuComponent 
                polylineController={this} 
                addCallback={addCallback} 
                removeCallback={removeCallback} 
            />
        );
        this._settingsComponent.setMenus([generatedPlanSettingsMenuComponent]);
    }

    // Enhanced geometry methods for frontend use
    getArea() {
        return this._geometryCache?.area || 0;
    }

    getPerimeter() {
        return this._geometryCache?.perimeter || 0;
    }

    getCentroid() {
        return this._geometryCache?.centroid || null;
    }

    isValidGeometry() {
        return this._validationCache?.is_valid || false;
    }

    isClosed() {
        return this._validationCache?.is_closed || false;
    }

    hasSelfIntersections() {
        return this._validationCache?.self_intersects || false;
    }

    getMainOrientation() {
        return this._geometryCache?.main_orientation || 0;
    }

    getGeometryQuality() {
        if (!this._validationCache) return 0;
        return GeometryService.getGeometryQualityScore(this._validationCache);
    }

    getGeometryStatus() {
        if (!this._validationCache) return 'Unknown';
        return GeometryService.getGeometryStatusDescription(this._validationCache);
    }

    getFormattedArea() {
        return GeometryService.formatArea(this.getArea());
    }

    getFormattedPerimeter() {
        return GeometryService.formatDistance(this.getPerimeter());
    }

    // Method to refresh geometry analysis
    async refreshGeometryAnalysis() {
        this._geometryCache = null;
        this._validationCache = null;
        this._lastCacheUpdate = 0;
        await this.analyzeGeometry();
        await this.validateGeometry();
    }

    // Enhanced cleanup method
    dispose() {
        this.cleanupAllVisualizations();
        if (this._line) {
            if (this._line.geometry) this._line.geometry.dispose();
            if (this._line.material) this._line.material.dispose();
        }
    }
}