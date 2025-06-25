import React, { useState, useEffect } from 'react';
import GeometryService from '../../../Services/GeometryService';

export default function EnhancedGeometryValidation({ polylineController, addCallback, removeCallback }) {
    const parameters = polylineController.generatedPlanController?.parameters;
    const [validationInfo, setValidationInfo] = useState(null);
    const [geometryInfo, setGeometryInfo] = useState(null);
    const [isValidating, setIsValidating] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [autoValidate, setAutoValidate] = useState(true);
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [activeTab, setActiveTab] = useState('validation');
    const [backendStatus, setBackendStatus] = useState(null);

    // Advanced settings
    const [tolerance, setTolerance] = useState(1e-6);
    const [checkClosure, setCheckClosure] = useState(true);
    const [checkSelfIntersection, setCheckSelfIntersection] = useState(true);
    const [checkPlanarity, setCheckPlanarity] = useState(true);

    // Clustering settings
    const [clusterDiameter, setClusterDiameter] = useState(50.0);
    const [voronoiSeedCount, setVoronoiSeedCount] = useState(10);

    // Offset settings
    const [offsetDistance, setOffsetDistance] = useState(5.0);
    const [offsetType, setOffsetType] = useState('inward');

    useEffect(() => {
        initializeComponent();
    }, [polylineController, parameters]);

    const initializeComponent = async () => {
        // Get current validation and geometry info
        const validation = polylineController.validationInfo;
        const geometry = polylineController.geometryInfo;
        
        setValidationInfo(validation);
        setGeometryInfo(geometry);

        // Test backend connection
        try {
            const status = await GeometryService.testConnection();
            setBackendStatus(status);
        } catch (error) {
            setBackendStatus({ connected: false, error: error.message });
        }

        // Set initial parameters
        if (parameters) {
            const geomParams = parameters.getGeometryParameters?.() || {};
            setTolerance(geomParams.tolerance || 1e-6);
            setCheckClosure(geomParams.check_closure !== false);
            setCheckSelfIntersection(geomParams.check_self_intersection !== false);
            setCheckPlanarity(geomParams.check_planarity !== false);
            setAutoValidate(geomParams.validate_geometry !== false);
        }
    };

    const runValidation = async () => {
        setIsValidating(true);
        
        try {
            const flattenedVertices = polylineController.getFlattenedVertices();
            
            if (flattenedVertices.length < 9) {
                setValidationInfo({
                    is_valid: false,
                    errors: ['Insufficient vertices for validation (minimum 3 points required)'],
                    warnings: [],
                    polygon_area: 0,
                    polygon_perimeter: 0,
                    is_closed: false,
                    is_planar: false,
                    self_intersects: false
                });
                setIsValidating(false);
                return;
            }

            // Run validation with current settings
            const result = await GeometryService.validateGeometry(flattenedVertices, {
                tolerance,
                check_closure: checkClosure,
                check_self_intersection: checkSelfIntersection,
                check_planarity: checkPlanarity
            });

            setValidationInfo(result);
            
            // Also get geometry analysis
            try {
                const geoResult = await GeometryService.analyzeGeometry(flattenedVertices, 'analyze');
                setGeometryInfo(geoResult);
            } catch (error) {
                console.warn('Geometry analysis failed:', error);
            }
            
            // Update polyline visual feedback
            polylineController.updateVisualFeedback(result);
            
        } catch (error) {
            console.error('Validation failed:', error);
            setValidationInfo({
                is_valid: false,
                errors: [error.message],
                warnings: [],
                polygon_area: 0,
                polygon_perimeter: 0,
                is_closed: false,
                is_planar: false,
                self_intersects: false
            });
        }
        
        setIsValidating(false);
    };

    const createOffset = async () => {
        if (!backendStatus?.connected) {
            alert('Backend not connected - offset operation unavailable');
            return;
        }

        setIsProcessing(true);
        try {
            const offsetLine = await polylineController.createOffset(offsetDistance, offsetType);
            if (offsetLine && addCallback) {
                addCallback([{ objects: [offsetLine], built: true }]);
            }
        } catch (error) {
            console.error('Failed to create offset:', error);
            alert(`Failed to create offset: ${error.message}`);
        }
        setIsProcessing(false);
    };

    const runClusteringAnalysis = async () => {
        if (!backendStatus?.connected) {
            alert('Backend not connected - clustering analysis unavailable');
            return;
        }

        setIsProcessing(true);
        try {
            const result = await polylineController.analyzeBuildingClusters(clusterDiameter);
            if (result && addCallback) {
                // Add cluster visualizations to scene
                const clusterObjects = polylineController.clusterVisualizations.map(obj => ({
                    objects: [obj],
                    built: true
                }));
                addCallback(clusterObjects);
            }
        } catch (error) {
            console.error('Clustering analysis failed:', error);
            alert(`Clustering analysis failed: ${error.message}`);
        }
        setIsProcessing(false);
    };

    const generateVoronoiDiagram = async () => {
        if (!backendStatus?.connected) {
            alert('Backend not connected - Voronoi generation unavailable');
            return;
        }

        setIsProcessing(true);
        try {
            const result = await polylineController.generateVoronoiDiagram(voronoiSeedCount);
            if (result && addCallback) {
                // Add Voronoi visualizations to scene
                const voronoiObjects = polylineController.voronoiCells.map(obj => ({
                    objects: [obj],
                    built: true
                }));
                addCallback(voronoiObjects);
            }
        } catch (error) {
            console.error('Voronoi generation failed:', error);
            alert(`Voronoi generation failed: ${error.message}`);
        }
        setIsProcessing(false);
    };

    const optimizeDistribution = async () => {
        if (!backendStatus?.connected) {
            alert('Backend not connected - distribution optimization unavailable');
            return;
        }

        setIsProcessing(true);
        try {
            const result = await polylineController.optimizeBuildingDistribution({
                target_density: parameters?.density || 0.5,
                min_spacing: parameters?.min_building_spacing || 5.0
            });
            
            if (result) {
                alert(`Distribution optimized: ${result.optimized_analysis?.building_count || 'N/A'} buildings generated`);
            }
        } catch (error) {
            console.error('Distribution optimization failed:', error);
            alert(`Distribution optimization failed: ${error.message}`);
        }
        setIsProcessing(false);
    };

    const clearVisualizations = () => {
        polylineController.cleanupAllVisualizations();
        if (removeCallback) {
            // Remove visualization objects from scene
            removeCallback([]);
        }
    };

    const getQualityScore = () => {
        if (!validationInfo) return 0;
        return GeometryService.getGeometryQualityScore(validationInfo);
    };

    const getQualityColor = (score) => {
        if (score >= 90) return "#4CAF50";
        if (score >= 75) return "#8BC34A";
        if (score >= 60) return "#FFC107";
        if (score >= 40) return "#FF9800";
        return "#F44336";
    };

    const qualityScore = getQualityScore();

    const tabs = [
        { id: 'validation', label: 'Validation', icon: '✓' },
        { id: 'operations', label: 'Operations', icon: '⚙️' },
        { id: 'analysis', label: 'Analysis', icon: '📊' },
        { id: 'advanced', label: 'Advanced', icon: '🔧' }
    ];

    const getTabStyle = (tabId) => ({
        padding: '6px 10px',
        backgroundColor: activeTab === tabId ? '#007bff' : 'transparent',
        color: activeTab === tabId ? 'white' : '#007bff',
        border: '1px solid #007bff',
        borderRadius: '4px 4px 0 0',
        cursor: 'pointer',
        fontSize: '10px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px'
    });

    return (
        <div style={{
            position: 'static',
            display: 'grid',
            gridTemplateColumns: '1fr',
            width: '100%',
            height: 'auto',
            border: 'none',
            padding: '10px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            marginBottom: '10px'
        }}>
            {/* Header with Backend Status */}
            <div style={{ marginBottom: '15px' }}>
                <h4 style={{ 
                    margin: '0 0 10px 0',
                    color: '#333',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <span>Enhanced Geometry Tools</span>
                    {validationInfo && (
                        <span style={{ 
                            fontSize: '12px',
                            padding: '2px 8px',
                            backgroundColor: getQualityColor(qualityScore),
                            color: 'white',
                            borderRadius: '12px'
                        }}>
                            {qualityScore}%
                        </span>
                    )}
                </h4>
                
                {/* Backend Status */}
                {backendStatus && (
                    <div style={{
                        padding: '6px',
                        backgroundColor: backendStatus.connected ? '#d4edda' : '#f8d7da',
                        color: backendStatus.connected ? '#155724' : '#721c24',
                        fontSize: '10px',
                        borderRadius: '4px',
                        marginBottom: '10px'
                    }}>
                        {backendStatus.connected ? (
                            <span>✅ {backendStatus.engine} v{backendStatus.version} - {backendStatus.capabilities?.length || 0} features</span>
                        ) : (
                            <span>❌ Backend disconnected: {backendStatus.error}</span>
                        )}
                    </div>
                )}
            </div>

            {/* Tab Navigation */}
            <div style={{
                display: 'flex',
                backgroundColor: '#e9ecef',
                borderRadius: '4px 4px 0 0',
                marginBottom: '10px'
            }}>
                {tabs.map(tab => (
                    <div
                        key={tab.id}
                        style={getTabStyle(tab.id)}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        <span>{tab.icon}</span>
                        <span>{tab.label}</span>
                    </div>
                ))}
            </div>

            {/* Tab Content */}
            <div style={{ backgroundColor: 'white', padding: '10px', borderRadius: '0 0 4px 4px' }}>
                
                {/* Validation Tab */}
                {activeTab === 'validation' && (
                    <div>
                        {/* Validation Controls */}
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '15px' }}>
                            <button
                                onClick={runValidation}
                                disabled={isValidating}
                                style={{
                                    fontSize: '12px',
                                    padding: '6px 12px',
                                    backgroundColor: isValidating ? '#ccc' : '#007bff',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: isValidating ? 'not-allowed' : 'pointer'
                                }}
                            >
                                {isValidating ? 'Validating...' : 'Validate Geometry'}
                            </button>
                            
                            <label style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <input
                                    type="checkbox"
                                    checked={autoValidate}
                                    onChange={(e) => setAutoValidate(e.target.checked)}
                                />
                                Auto-validate
                            </label>
                        </div>

                        {/* Validation Results */}
                        {validationInfo && (
                            <div style={{ marginBottom: '15px' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                                    <div>
                                        <strong>Status:</strong><br />
                                        <span style={{ color: validationInfo.is_valid ? '#4CAF50' : '#F44336' }}>
                                            {validationInfo.is_valid ? '✓ Valid' : '✗ Invalid'}
                                        </span>
                                    </div>
                                    <div>
                                        <strong>Closed:</strong><br />
                                        <span style={{ color: validationInfo.is_closed ? '#4CAF50' : '#FF9800' }}>
                                            {validationInfo.is_closed ? '✓ Yes' : '⚠ No'}
                                        </span>
                                    </div>
                                    <div>
                                        <strong>Planar:</strong><br />
                                        <span style={{ color: validationInfo.is_planar ? '#4CAF50' : '#FF9800' }}>
                                            {validationInfo.is_planar ? '✓ Yes' : '⚠ No'}
                                        </span>
                                    </div>
                                    <div>
                                        <strong>Self-Intersects:</strong><br />
                                        <span style={{ color: validationInfo.self_intersects ? '#F44336' : '#4CAF50' }}>
                                            {validationInfo.self_intersects ? '✗ Yes' : '✓ No'}
                                        </span>
                                    </div>
                                </div>
                                
                                {geometryInfo && (
                                    <div style={{ marginTop: '10px', fontSize: '11px', color: '#666' }}>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                            <div><strong>Area:</strong> {GeometryService.formatArea(validationInfo.polygon_area || 0)}</div>
                                            <div><strong>Perimeter:</strong> {GeometryService.formatDistance(validationInfo.polygon_perimeter || 0)}</div>
                                        </div>
                                        {geometryInfo.centroid && (
                                            <div style={{ marginTop: '6px' }}>
                                                <strong>Centroid:</strong> ({geometryInfo.centroid.x?.toFixed(1)}, {geometryInfo.centroid.y?.toFixed(1)})
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Errors and Warnings */}
                        {validationInfo && validationInfo.errors && validationInfo.errors.length > 0 && (
                            <div style={{
                                fontSize: '11px',
                                color: '#F44336',
                                backgroundColor: '#ffebee',
                                padding: '6px',
                                borderRadius: '4px',
                                marginBottom: '8px',
                                border: '1px solid #ffcdd2'
                            }}>
                                <strong>❌ Errors:</strong><br />
                                {validationInfo.errors.map((error, index) => (
                                    <div key={index}>• {error}</div>
                                ))}
                            </div>
                        )}

                        {validationInfo && validationInfo.warnings && validationInfo.warnings.length > 0 && (
                            <div style={{
                                fontSize: '11px',
                                color: '#FF9800',
                                backgroundColor: '#fff3e0',
                                padding: '6px',
                                borderRadius: '4px',
                                marginBottom: '8px',
                                border: '1px solid #ffcc02'
                            }}>
                                <strong>⚠️ Warnings:</strong><br />
                                {validationInfo.warnings.map((warning, index) => (
                                    <div key={index}>• {warning}</div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Operations Tab */}
                {activeTab === 'operations' && (
                    <div>
                        {/* Offset Operations */}
                        <div style={{ marginBottom: '15px' }}>
                            <h5 style={{ margin: '0 0 8px 0', fontSize: '13px' }}>Polygon Offset</h5>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
                                <div>
                                    <label style={{ fontSize: '11px', display: 'block', marginBottom: '4px' }}>
                                        Distance (m):
                                    </label>
                                    <input
                                        type="number"
                                        value={offsetDistance}
                                        onChange={(e) => setOffsetDistance(parseFloat(e.target.value))}
                                        min="0.1"
                                        max="50"
                                        step="0.1"
                                        style={{ width: '100%', fontSize: '11px', padding: '4px' }}
                                    />
                                </div>
                                <div>
                                    <label style={{ fontSize: '11px', display: 'block', marginBottom: '4px' }}>
                                        Direction:
                                    </label>
                                    <select
                                        value={offsetType}
                                        onChange={(e) => setOffsetType(e.target.value)}
                                        style={{ width: '100%', fontSize: '11px', padding: '4px' }}
                                    >
                                        <option value="inward">Inward</option>
                                        <option value="outward">Outward</option>
                                    </select>
                                </div>
                            </div>
                            
                            <button
                                onClick={createOffset}
                                disabled={isProcessing || !backendStatus?.connected}
                                style={{
                                    fontSize: '11px',
                                    padding: '6px 12px',
                                    backgroundColor: (!backendStatus?.connected || isProcessing) ? '#ccc' : '#28a745',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: (!backendStatus?.connected || isProcessing) ? 'not-allowed' : 'pointer',
                                    width: '100%'
                                }}
                            >
                                {isProcessing ? 'Creating Offset...' : `Create ${offsetType} Offset`}
                            </button>
                        </div>

                        {/* Clear Visualizations */}
                        <div>
                            <button
                                onClick={clearVisualizations}
                                style={{
                                    fontSize: '11px',
                                    padding: '6px 12px',
                                    backgroundColor: '#dc3545',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    width: '100%'
                                }}
                            >
                                Clear All Visualizations
                            </button>
                        </div>
                    </div>
                )}

                {/* Analysis Tab */}
                {activeTab === 'analysis' && (
                    <div>
                        {/* Clustering Analysis */}
                        <div style={{ marginBottom: '15px' }}>
                            <h5 style={{ margin: '0 0 8px 0', fontSize: '13px' }}>Building Clustering</h5>
                            
                            <div style={{ marginBottom: '8px' }}>
                                <label style={{ fontSize: '11px', display: 'block', marginBottom: '4px' }}>
                                    Cluster Diameter (m):
                                </label>
                                <input
                                    type="range"
                                    min="10"
                                    max="200"
                                    value={clusterDiameter}
                                    onChange={(e) => setClusterDiameter(parseFloat(e.target.value))}
                                    style={{ width: '100%' }}
                                />
                                <div style={{ fontSize: '10px', color: '#666', textAlign: 'center' }}>
                                    {clusterDiameter.toFixed(1)}m
                                </div>
                            </div>
                            
                            <button
                                onClick={runClusteringAnalysis}
                                disabled={isProcessing || !backendStatus?.connected}
                                style={{
                                    fontSize: '11px',
                                    padding: '6px 12px',
                                    backgroundColor: (!backendStatus?.connected || isProcessing) ? '#ccc' : '#17a2b8',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: (!backendStatus?.connected || isProcessing) ? 'not-allowed' : 'pointer',
                                    width: '100%'
                                }}
                            >
                                {isProcessing ? 'Analyzing...' : 'Analyze Clusters'}
                            </button>
                        </div>

                        {/* Voronoi Analysis */}
                        <div style={{ marginBottom: '15px' }}>
                            <h5 style={{ margin: '0 0 8px 0', fontSize: '13px' }}>Voronoi Diagram</h5>
                            
                            <div style={{ marginBottom: '8px' }}>
                                <label style={{ fontSize: '11px', display: 'block', marginBottom: '4px' }}>
                                    Seed Count:
                                </label>
                                <input
                                    type="range"
                                    min="3"
                                    max="50"
                                    value={voronoiSeedCount}
                                    onChange={(e) => setVoronoiSeedCount(parseInt(e.target.value))}
                                    style={{ width: '100%' }}
                                />
                                <div style={{ fontSize: '10px', color: '#666', textAlign: 'center' }}>
                                    {voronoiSeedCount} seeds
                                </div>
                            </div>
                            
                            <button
                                onClick={generateVoronoiDiagram}
                                disabled={isProcessing || !backendStatus?.connected}
                                style={{
                                    fontSize: '11px',
                                    padding: '6px 12px',
                                    backgroundColor: (!backendStatus?.connected || isProcessing) ? '#ccc' : '#6f42c1',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: (!backendStatus?.connected || isProcessing) ? 'not-allowed' : 'pointer',
                                    width: '100%'
                                }}
                            >
                                {isProcessing ? 'Generating...' : 'Generate Voronoi'}
                            </button>
                        </div>

                        {/* Distribution Optimization */}
                        <div>
                            <h5 style={{ margin: '0 0 8px 0', fontSize: '13px' }}>Distribution Optimization</h5>
                            
                            <button
                                onClick={optimizeDistribution}
                                disabled={isProcessing || !backendStatus?.connected}
                                style={{
                                    fontSize: '11px',
                                    padding: '6px 12px',
                                    backgroundColor: (!backendStatus?.connected || isProcessing) ? '#ccc' : '#fd7e14',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: (!backendStatus?.connected || isProcessing) ? 'not-allowed' : 'pointer',
                                    width: '100%'
                                }}
                            >
                                {isProcessing ? 'Optimizing...' : 'Optimize Distribution'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Advanced Tab */}
                {activeTab === 'advanced' && (
                    <div>
                        <h5 style={{ margin: '0 0 10px 0', fontSize: '13px' }}>Advanced Settings</h5>
                        
                        {/* Validation Settings */}
                        <div style={{ marginBottom: '15px' }}>
                            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '8px' }}>
                                Validation Parameters:
                            </div>
                            
                            <div style={{ marginBottom: '8px' }}>
                                <label style={{ fontSize: '11px', display: 'block', marginBottom: '4px' }}>
                                    Tolerance:
                                </label>
                                <select
                                    value={tolerance}
                                    onChange={(e) => setTolerance(parseFloat(e.target.value))}
                                    style={{ width: '100%', fontSize: '10px', padding: '4px' }}
                                >
                                    <option value={1e-3}>Coarse (1e-3)</option>
                                    <option value={1e-6}>Normal (1e-6)</option>
                                    <option value={1e-9}>Fine (1e-9)</option>
                                    <option value={1e-12}>Ultra-fine (1e-12)</option>
                                </select>
                            </div>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <input
                                        type="checkbox"
                                        checked={checkClosure}
                                        onChange={(e) => setCheckClosure(e.target.checked)}
                                    />
                                    Check Closure
                                </label>
                                
                                <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <input
                                        type="checkbox"
                                        checked={checkSelfIntersection}
                                        onChange={(e) => setCheckSelfIntersection(e.target.checked)}
                                    />
                                    Self-Intersection
                                </label>
                                
                                <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <input
                                        type="checkbox"
                                        checked={checkPlanarity}
                                        onChange={(e) => setCheckPlanarity(e.target.checked)}
                                    />
                                    Check Planarity
                                </label>
                            </div>
                        </div>

                        {/* Backend Information */}
                        {backendStatus?.connected && (
                            <div style={{
                                fontSize: '10px',
                                color: '#495057',
                                backgroundColor: '#e9ecef',
                                padding: '8px',
                                borderRadius: '4px'
                            }}>
                                <strong>Backend Information:</strong><br />
                                Service: {backendStatus.engine}<br />
                                Version: {backendStatus.version}<br />
                                Capabilities: {backendStatus.capabilities?.length || 0} features<br />
                                Available: {backendStatus.capabilities?.join(', ') || 'None'}
                            </div>
                        )}

                        {/* Connection Test */}
                        <div style={{ marginTop: '10px' }}>
                            <button
                                onClick={initializeComponent}
                                style={{
                                    fontSize: '11px',
                                    padding: '6px 12px',
                                    backgroundColor: '#6c757d',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    width: '100%'
                                }}
                            >
                                Test Backend Connection
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Quality Recommendations */}
            {validationInfo && qualityScore < 80 && (
                <div style={{
                    fontSize: '11px',
                    color: '#0066cc',
                    backgroundColor: '#e6f3ff',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #b3d9ff',
                    marginTop: '10px'
                }}>
                    <strong>💡 Recommendations:</strong><br />
                    {!validationInfo.is_closed && <div>• Close the polygon by connecting the endpoints</div>}
                    {validationInfo.self_intersects && <div>• Remove self-intersections by redrawing crossing segments</div>}
                    {!validationInfo.is_planar && <div>• Ensure all points lie in the same plane</div>}
                    {validationInfo.polygon_area < 100 && <div>• Consider increasing polygon size for better building placement</div>}
                </div>
            )}
        </div>
    );
}