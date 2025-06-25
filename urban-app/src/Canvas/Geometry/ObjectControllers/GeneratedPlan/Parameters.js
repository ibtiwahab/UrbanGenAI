// Enhanced Parameters component for the frontend - GeneratedPlanParameters.js

export default class EnhancedGeneratedPlanParameters {
    constructor() {
        // Standard parameters
        this.site_type = 0;
        this.density = 0.5;
        this.far = 3.0;
        this.mix_ratio = 2.0;
        this.building_style = 5;
        this.orientation = 0.0;
        
        // Enhanced clustering and distribution parameters
        this.use_clustering = true;
        this.cluster_diameter = 50.0;
        this.use_voronoi = false;
        this.building_variation = 0.3;
        this.max_buildings = 100;
        
        // Advanced spacing and layout parameters
        this.min_building_spacing = 5.0;
        this.setback_distance = 3.0;
        this.use_grid_layout = false;
        this.adaptive_orientation = true;
        
        // Building size and shape parameters
        this.size_variation_enabled = true;
        this.height_variation_enabled = true;
        this.shape_variation_enabled = true;
        
        // Area filling parameters
        this.fill_strategy = 'adaptive'; // 'grid', 'organic', 'clustered', 'voronoi', 'adaptive'
        this.target_coverage = 0.7; // Target percentage of buildable area to fill
        this.minimum_building_count = 5;
        this.force_area_filling = true;
    }
    
    // Standard parameter setters with validation
    setSiteType(value) {
        this.site_type = Math.max(0, Math.min(4, Math.floor(value)));
        this._updateDependentParameters();
    }
    
    setDensity(value) {
        this.density = Math.max(0.01, Math.min(0.99, parseFloat(value)));
        this._updateDependentParameters();
    }
    
    setFAR(value) {
        this.far = Math.max(0.1, Math.min(10.0, parseFloat(value)));
        this._updateDependentParameters();
    }
    
    setMixRatio(value) {
        this.mix_ratio = Math.max(0.0, Math.min(0.99, parseFloat(value)));
    }
    
    setBuildingStyle(value) {
        this.building_style = Math.max(0, Math.min(3, Math.floor(value)));
        this._updateDependentParameters();
    }
    
    setOrientation(value) {
        this.orientation = Math.max(0.0, Math.min(180.0, parseFloat(value)));
    }
    
    // Enhanced parameter setters
    setUseClustering(value) {
        this.use_clustering = Boolean(value);
        if (this.use_clustering) {
            this.use_voronoi = false; // Mutually exclusive
            this.use_grid_layout = false;
        }
    }
    
    setClusterDiameter(value) {
        this.cluster_diameter = Math.max(10.0, Math.min(200.0, parseFloat(value)));
    }
    
    setUseVoronoi(value) {
        this.use_voronoi = Boolean(value);
        if (this.use_voronoi) {
            this.use_clustering = false; // Mutually exclusive
            this.use_grid_layout = false;
        }
    }
    
    setBuildingVariation(value) {
        this.building_variation = Math.max(0.0, Math.min(1.0, parseFloat(value)));
    }
    
    setMaxBuildings(value) {
        this.max_buildings = Math.max(5, Math.min(200, Math.floor(value)));
    }
    
    setMinBuildingSpacing(value) {
        this.min_building_spacing = Math.max(2.0, Math.min(20.0, parseFloat(value)));
    }
    
    setSetbackDistance(value) {
        this.setback_distance = Math.max(0.0, Math.min(15.0, parseFloat(value)));
    }
    
    setUseGridLayout(value) {
        this.use_grid_layout = Boolean(value);
        if (this.use_grid_layout) {
            this.use_clustering = false;
            this.use_voronoi = false;
        }
    }
    
    setAdaptiveOrientation(value) {
        this.adaptive_orientation = Boolean(value);
    }
    
    setFillStrategy(value) {
        const validStrategies = ['grid', 'organic', 'clustered', 'voronoi', 'adaptive'];
        if (validStrategies.includes(value)) {
            this.fill_strategy = value;
            this._updateStrategyDependentParameters();
        }
    }
    
    setTargetCoverage(value) {
        this.target_coverage = Math.max(0.1, Math.min(0.95, parseFloat(value)));
    }
    
    setForceAreaFilling(value) {
        this.force_area_filling = Boolean(value);
    }
    
    // Auto-update dependent parameters based on current settings
    _updateDependentParameters() {
        // Update clustering settings based on density
        if (this.density > 0.7) {
            this.use_clustering = true;
            this.use_grid_layout = false;
        } else if (this.density < 0.3) {
            this.use_voronoi = this.site_type === 3; // Mixed use sites
            this.use_clustering = false;
        }
        
        // Update spacing based on density and site type
        const baseSpacing = this._getBaseSpacing();
        this.min_building_spacing = baseSpacing * (1.2 - this.density * 0.5);
        
        // Update setback based on FAR
        const baseSetback = this._getBaseSetback();
        this.setback_distance = baseSetback * (1.0 + this.far / 10.0);
        
        // Update max buildings based on density and FAR
        this._updateMaxBuildings();
        
        // Update cluster diameter based on site characteristics
        if (this.use_clustering) {
            this.cluster_diameter = Math.max(20.0, 60.0 - this.density * 30.0);
        }
        
        console.log('Updated dependent parameters:', {
            use_clustering: this.use_clustering,
            use_voronoi: this.use_voronoi,
            min_building_spacing: this.min_building_spacing.toFixed(1),
            setback_distance: this.setback_distance.toFixed(1),
            max_buildings: this.max_buildings
        });
    }
    
    _updateStrategyDependentParameters() {
        switch (this.fill_strategy) {
            case 'grid':
                this.use_grid_layout = true;
                this.use_clustering = false;
                this.use_voronoi = false;
                this.building_variation = Math.min(0.2, this.building_variation);
                break;
                
            case 'clustered':
                this.use_clustering = true;
                this.use_grid_layout = false;
                this.use_voronoi = false;
                this.building_variation = Math.max(0.3, this.building_variation);
                break;
                
            case 'voronoi':
                this.use_voronoi = true;
                this.use_clustering = false;
                this.use_grid_layout = false;
                this.building_variation = Math.max(0.4, this.building_variation);
                break;
                
            case 'organic':
                this.use_clustering = false;
                this.use_grid_layout = false;
                this.use_voronoi = false;
                this.building_variation = Math.max(0.5, this.building_variation);
                break;
                
            case 'adaptive':
            default:
                // Let density determine the strategy
                this._updateDependentParameters();
                break;
        }
    }
    
    _getBaseSpacing() {
        const spacingByType = {
            0: 6.0,   // Residential
            1: 8.0,   // Commercial
            2: 7.0,   // Office
            3: 7.5,   // Mixed
            4: 10.0   // Industrial
        };
        return spacingByType[this.site_type] || 6.0;
    }
    
    _getBaseSetback() {
        const setbackByType = {
            0: 3.0,   // Residential
            1: 4.0,   // Commercial
            2: 3.5,   // Office
            3: 3.5,   // Mixed
            4: 5.0    // Industrial
        };
        return setbackByType[this.site_type] || 3.0;
    }
    
    _updateMaxBuildings() {
        // Calculate reasonable max buildings based on density and FAR
        const baseBuildingCount = {
            0: 20,   // Residential
            1: 15,   // Commercial
            2: 25,   // Office
            3: 30,   // Mixed
            4: 10    // Industrial
        }[this.site_type] || 20;
        
        const densityMultiplier = 0.5 + this.density * 1.5; // 0.5 to 2.0
        const farMultiplier = Math.min(2.0, 1.0 + this.far / 5.0); // 1.0 to 2.0
        
        this.max_buildings = Math.floor(baseBuildingCount * densityMultiplier * farMultiplier);
        this.max_buildings = Math.max(this.minimum_building_count, Math.min(200, this.max_buildings));
    }
    
    // Get building parameters for size calculations
    getBuildingParameters() {
        const baseDimensions = {
            0: { base_width: 15, base_depth: 12 },   // Residential
            1: { base_width: 22, base_depth: 16 },   // Commercial
            2: { base_width: 18, base_depth: 14 },   // Office
            3: { base_width: 16, base_depth: 13 },   // Mixed
            4: { base_width: 25, base_depth: 18 }    // Industrial
        }[this.site_type] || { base_width: 15, base_depth: 12 };
        
        // Apply style multipliers
        const styleMultipliers = {
            0: { width: 1.0, depth: 1.0 },     // Standard
            1: { width: 1.3, depth: 1.1 },     // Large
            2: { width: 0.8, depth: 0.9 },     // Compact
            3: { width: 1.1, depth: 1.2 }      // Extended
        }[this.building_style] || { width: 1.0, depth: 1.0 };
        
        // Apply density scaling
        const densityScale = 0.8 + (this.density * 0.6); // 0.8 to 1.4
        
        return {
            base_width: baseDimensions.base_width * styleMultipliers.width * densityScale,
            base_depth: baseDimensions.base_depth * styleMultipliers.depth * densityScale,
            min_spacing: this.min_building_spacing,
            setback: this.setback_distance
        };
    }
    
    // Get strategy description for UI
    getStrategyDescription() {
        const descriptions = {
            'grid': 'Regular grid layout with uniform spacing',
            'organic': 'Natural, irregular placement with varied spacing',
            'clustered': 'Buildings grouped in clusters with open spaces',
            'voronoi': 'Efficient space division with varied building sizes',
            'adaptive': 'Automatically selects best strategy based on parameters'
        };
        
        return descriptions[this.fill_strategy] || descriptions['adaptive'];
    }
    
    // Get current strategy being used
    getCurrentStrategy() {
        if (this.fill_strategy === 'adaptive') {
            if (this.use_grid_layout) return 'grid';
            if (this.use_clustering) return 'clustered';
            if (this.use_voronoi) return 'voronoi';
            return 'organic';
        }
        return this.fill_strategy;
    }
    
    // Validate all parameters
    validate() {
        const errors = [];
        
        if (this.density <= 0 || this.density >= 1) {
            errors.push('Density must be between 0 and 1');
        }
        
        if (this.far <= 0 || this.far > 10) {
            errors.push('FAR must be between 0 and 10');
        }
        
        if (this.max_buildings < this.minimum_building_count) {
            errors.push(`Max buildings must be at least ${this.minimum_building_count}`);
        }
        
        if (this.min_building_spacing < 2.0) {
            errors.push('Minimum building spacing must be at least 2.0m');
        }
        
        if (this.cluster_diameter < 10.0 && this.use_clustering) {
            errors.push('Cluster diameter must be at least 10.0m when clustering is enabled');
        }
        
        return errors;
    }
    
    // Export parameters for backend
    toBackendFormat() {
        return {
            // Standard parameters
            site_type: this.site_type,
            density: this.density,
            far: this.far,
            mix_ratio: this.mix_ratio,
            building_style: this.building_style,
            orientation: this.orientation,
            
            // Enhanced parameters
            use_clustering: this.use_clustering,
            cluster_diameter: this.cluster_diameter,
            use_voronoi: this.use_voronoi,
            building_variation: this.building_variation,
            max_buildings: this.max_buildings,
            min_building_spacing: this.min_building_spacing,
            setback_distance: this.setback_distance,
            use_grid_layout: this.use_grid_layout,
            adaptive_orientation: this.adaptive_orientation,
            
            // Area filling parameters
            fill_strategy: this.fill_strategy,
            target_coverage: this.target_coverage,
            force_area_filling: this.force_area_filling,
            
            // Building variation parameters
            size_variation_enabled: this.size_variation_enabled,
            height_variation_enabled: this.height_variation_enabled,
            shape_variation_enabled: this.shape_variation_enabled
        };
    }
    
    // Import parameters from backend or UI
    fromObject(obj) {
        if (!obj) return;
        
        // Standard parameters
        if ('site_type' in obj) this.setSiteType(obj.site_type);
        if ('density' in obj) this.setDensity(obj.density);
        if ('far' in obj) this.setFAR(obj.far);
        if ('mix_ratio' in obj) this.setMixRatio(obj.mix_ratio);
        if ('building_style' in obj) this.setBuildingStyle(obj.building_style);
        if ('orientation' in obj) this.setOrientation(obj.orientation);
        
        // Enhanced parameters
        if ('use_clustering' in obj) this.setUseClustering(obj.use_clustering);
        if ('cluster_diameter' in obj) this.setClusterDiameter(obj.cluster_diameter);
        if ('use_voronoi' in obj) this.setUseVoronoi(obj.use_voronoi);
        if ('building_variation' in obj) this.setBuildingVariation(obj.building_variation);
        if ('max_buildings' in obj) this.setMaxBuildings(obj.max_buildings);
        if ('min_building_spacing' in obj) this.setMinBuildingSpacing(obj.min_building_spacing);
        if ('setback_distance' in obj) this.setSetbackDistance(obj.setback_distance);
        if ('use_grid_layout' in obj) this.setUseGridLayout(obj.use_grid_layout);
        if ('adaptive_orientation' in obj) this.setAdaptiveOrientation(obj.adaptive_orientation);
        
        // Area filling parameters
        if ('fill_strategy' in obj) this.setFillStrategy(obj.fill_strategy);
        if ('target_coverage' in obj) this.setTargetCoverage(obj.target_coverage);
        if ('force_area_filling' in obj) this.setForceAreaFilling(obj.force_area_filling);
        
        // Building variation parameters
        if ('size_variation_enabled' in obj) this.size_variation_enabled = Boolean(obj.size_variation_enabled);
        if ('height_variation_enabled' in obj) this.height_variation_enabled = Boolean(obj.height_variation_enabled);
        if ('shape_variation_enabled' in obj) this.shape_variation_enabled = Boolean(obj.shape_variation_enabled);
    }
    
    // Get summary for display
    getSummary() {
        const strategy = this.getCurrentStrategy();
        const buildingParams = this.getBuildingParameters();
        
        return {
            strategy: strategy,
            strategyDescription: this.getStrategyDescription(),
            expectedBuildings: this.max_buildings,
            buildingSize: `${buildingParams.base_width.toFixed(1)}×${buildingParams.base_depth.toFixed(1)}m`,
            spacing: `${this.min_building_spacing.toFixed(1)}m`,
            setback: `${this.setback_distance.toFixed(1)}m`,
            variation: `${(this.building_variation * 100).toFixed(0)}%`,
            coverage: `${(this.target_coverage * 100).toFixed(0)}%`
        };
    }
    
    // Reset to defaults
    reset() {
        this.site_type = 0;
        this.density = 0.5;
        this.far = 3.0;
        this.mix_ratio = 0.0;
        this.building_style = 0;
        this.orientation = 0.0;
        this.use_clustering = true;
        this.cluster_diameter = 50.0;
        this.use_voronoi = false;
        this.building_variation = 0.3;
        this.max_buildings = 100;
        this.min_building_spacing = 5.0;
        this.setback_distance = 3.0;
        this.use_grid_layout = false;
        this.adaptive_orientation = true;
        this.size_variation_enabled = true;
        this.height_variation_enabled = true;
        this.shape_variation_enabled = true;
        this.fill_strategy = 'adaptive';
        this.target_coverage = 0.7;
        this.minimum_building_count = 5;
        this.force_area_filling = true;
        
        this._updateDependentParameters();
    }
    
    // Clone parameters
    clone() {
        const clone = new EnhancedGeneratedPlanParameters();
        clone.fromObject(this.toBackendFormat());
        return clone;
    }
}