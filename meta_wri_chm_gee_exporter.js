// Define the canopy height image and apply a mask for canopy height >= 1 meter
var canopyHeight = ee.ImageCollection('projects/meta-forest-monitoring-okw37/assets/CanopyHeight').mosaic();
var maskedCanopyHeight = canopyHeight.updateMask(canopyHeight.gte(1));  // Mask out values < 1

// Center the map on the specified geometry region
Map.centerObject(geometry, 10);  // Adjust zoom as needed

// Visualization settings
var palettes = require('users/gena/packages:palettes');

// Other layers for reference (optional)
var ethcanopyheight = ee.Image('users/nlang/ETH_GlobalCanopyHeight_2020_10m_v1');
Map.addLayer(ethcanopyheight.clip(geometry), {
    min: 0,
    max: 25,
    palette: palettes.matplotlib.viridis[7]
}, 'Canopy Height Lang 2022 98%', false);

var umdheight = ee.ImageCollection("users/potapovpeter/GEDI_V27").mosaic();
Map.addLayer(umdheight.clip(geometry), {
    min: 0,
    max: 25,
    palette: palettes.matplotlib.viridis[7]
}, 'Canopy Height Potapov 2021 95%', false);

// Our layers (display maskedCanopyHeight)
Map.addLayer(maskedCanopyHeight.clip(geometry), {
    min: 0,
    max: 25,
    palette: palettes.matplotlib.viridis[7]
}, 'Canopy Height >= 1 [meters]');


// Export function
function exportCanopyHeight() {
    Export.image.toDrive({
        image: maskedCanopyHeight.clip(geometry),  // Use masked image for export
        description: 'CanopyHeight_Export',
        folder: 'EarthEngineExports',
        region: geometry,
        scale: 1,
        fileFormat: 'GeoTIFF',
        maxPixels: 1e13
    });
}

// Create export button (this is optional; you can just run `exportCanopyHeight` directly)
var exportButton = ui.Button({
    label: 'Export Canopy Height to Drive',
    style: {width: '200px', color: '#4CAF50'},
    onClick: exportCanopyHeight
});

// Display the export button (optional)
var controlPanel = ui.Panel({widgets: [exportButton]});
ui.root.add(controlPanel);
