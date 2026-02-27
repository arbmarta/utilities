// 0) Geometry (Oxford)
var geometry = ee.Geometry.Polygon(
  [[
    [-1.3302124313083241, 51.70665641633338],
    [-1.1606109908786366, 51.70665641633338],
    [-1.1606109908786366, 51.79847234686127],
    [-1.3302124313083241, 51.79847234686127],
    [-1.3302124313083241, 51.70665641633338]
  ]],
  null,
  false
);

// --------------------
// User parameters
// --------------------
var minMonth = 6;   // June
var maxMonth = 8;   // August
var minYear = 2020;
var maxYear = 2025;

// AOI cloud-fraction threshold (percent)
var maxAoiCloudPct = 15; // keep images with AOI cloud fraction < 15%

// Colour palette
var palette = [
  '040274','2c7bb6','00a6ca','00ccbc','90eb9d',
  'ffff8c','f9d057','f29e2e','e76818','d7191c'
];

// 1) Load collection and coarse calendar filtering
var collection0 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(geometry)
  .sort('system:time_start');

var monthFilter = ee.Filter.calendarRange(minMonth, maxMonth, 'month');
var yearFilter = ee.Filter.calendarRange(minYear, maxYear, 'year');

var collectionFiltered = collection0.filter(monthFilter).filter(yearFilter);

// 2) Compute AOI cloud fraction per image using QA_PIXEL and keep images < threshold
// Bits used (Collection 2 QA_PIXEL, CFMask-like):
//  bit 1 = Dilated_Cloud
//  bit 3 = Cloud (high confidence)
//  bit 4 = Cloud_Shadow
var dilatedCloudBit = 1 << 1; // 2
var cloudBit = 1 << 3;        // 8
var cloudShadowBit = 1 << 4;  // 16

// Function to add AOI cloud percentage property to each image
function addAoiCloudPct(image) {
  var qa = image.select('QA_PIXEL');
  // boolean cloud mask where any of the chosen bits are set
  var cloudMask = qa.bitwiseAnd(dilatedCloudBit).neq(0)
                    .or(qa.bitwiseAnd(cloudBit).neq(0))
                    .or(qa.bitwiseAnd(cloudShadowBit).neq(0));
  // Compute mean (fraction of pixels flagged cloudy) over AOI at 30 m
  var fracDict = cloudMask.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geometry,
    scale: 30,
    maxPixels: 1e13
  });
  // The band name will be 'QA_PIXEL' (same as the source band)
  var frac = ee.Number(fracDict.get('QA_PIXEL'));
  // Convert to percent (0-100). If null, set to 100 (conservative)
  var pct = ee.Algorithms.If(frac, frac.multiply(100), 100);
  return image.set('aoi_cloud_pct', pct);
}

// Map the property computation (server-side)
var withCloudPct = collectionFiltered.map(addAoiCloudPct);

// Now filter by AOI cloud fraction < maxAoiCloudPct
var collectionLowCloudAOI = withCloudPct.filter(ee.Filter.lt('aoi_cloud_pct', maxAoiCloudPct));

// 3) Keep only scenes whose footprint fully contains the AOI (optional but kept)
var collectionContained = collectionLowCloudAOI.filter(ee.Filter.contains({
  leftField: '.geo',
  rightValue: geometry
}));

// 4) Apply scaling (optical + thermal) and keep aoi_cloud_pct property
function applyScaleFactors(image) {
  var optical = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  var thermal = image.select('ST_B.*').multiply(0.00341802).add(149.0);
  return image.addBands(optical, null, true)
              .addBands(thermal, null, true)
              .copyProperties(image, ['system:time_start', 'system:id', 'aoi_cloud_pct']);
}
var collection = collectionContained.map(applyScaleFactors);

// Ensure we have images after AOI cloud filtering
var nImages = collection.size().getInfo();
if (nImages === 0) {
  throw new Error('No images found after calendar, AOI-cloud (< ' + maxAoiCloudPct +
                  '%) and footprint filters. Try widening the windows or increasing maxAoiCloudPct.');
}

// 5) Compute collection-wide ST_B10 per-pixel min/max at 30 m and enforce min = -5°C
var stMinImage = collection.select('ST_B10').min();
var stMaxImage = collection.select('ST_B10').max();

var globalMinDict = stMinImage.reduceRegion({
  reducer: ee.Reducer.min(),
  geometry: geometry,
  scale: 30,
  maxPixels: 1e13
});
var globalMaxDict = stMaxImage.reduceRegion({
  reducer: ee.Reducer.max(),
  geometry: geometry,
  scale: 30,
  maxPixels: 1e13
});

// Pull to client and convert to Celsius (K -> °C)
var stMinK = globalMinDict.get('ST_B10') ? globalMinDict.get('ST_B10').getInfo() : null;
var stMaxK = globalMaxDict.get('ST_B10') ? globalMaxDict.get('ST_B10').getInfo() : null;

if (stMinK === null || stMaxK === null) {
  print('Warning: could not compute collection min/max — falling back to defaults (-5–25 °C).');
  stMinK = 268.15; // -5°C in K
  stMaxK = 298.15; // 25°C in K
}

var stMinC_computed = stMinK - 273.15;
var stMaxC = stMaxK - 273.15;

// Enforce minimum Celsius to at least -5°C
var stMinC = Math.max(stMinC_computed, -5.0);

print('Computed collection ST_B10 range (°C):', stMinC_computed, stMaxC);
print('Enforced min (°C) used for visualization:', stMinC);

// 6) Prepare date labels and AOI cloud pct CLIENT-SIDE arrays (no NaN in titles)
// Pull arrays client-side
var timeArray = collection.aggregate_array('system:time_start').getInfo(); // list of millis
var cloudPctArray = collection.aggregate_array('aoi_cloud_pct').getInfo(); // list of numbers or null

// Build readable date labels and cloud labels (client-side)
var dateLabels = timeArray.map(function(ts) {
  return new Date(ts).toLocaleDateString('en-GB', { month: 'long', day: 'numeric', year: 'numeric' });
});

// Cloud labels: if value is null or undefined -> 'NA', else format to one decimal
var cloudLabels = cloudPctArray.map(function(v) {
  if (v === null || v === undefined) return 'NA';
  var n = Number(v);
  if (isNaN(n)) return 'NA';
  return n.toFixed(1);
});

// Server-side list for ee access by index
var n = collection.size().getInfo();
var collList = collection.toList(n);

// 7) Map context (RGB median) and AOI
Map.clear();
Map.centerObject(geometry, 12);
Map.addLayer(geometry, {color: 'red'}, 'AOI');

var rgbMedian = collection.select(['SR_B4','SR_B3','SR_B2']).median().clip(geometry);
Map.addLayer(rgbMedian, {bands: ['SR_B4','SR_B3','SR_B2'], min: 0.0, max: 0.3}, 'True Color (median)');

// 8) Add per-scene layers (hidden by default) and build export descriptors
var thermalVis = {min: stMinC, max: stMaxC, palette: palette};

// Client-side array of export descriptors {name, image (ee.Image), scale}
var exportDescriptors = [];

for (var i = 0; i < n; i++) {
  (function(idx) {
    var img = ee.Image(collList.get(idx));
    // Convert to Celsius and rename band for clarity
    var tempC = img.select('ST_B10').subtract(273.15).rename('ST_B10_Celsius').clip(geometry);
    // Use client-side cloud label and date label arrays
    var cloudLabel = cloudLabels[idx];
    var dateLabel = dateLabels[idx];
    var layerName = dateLabel + ' - heat map' + (cloudLabel !== 'NA' ? (' (AOI cloud: ' + cloudLabel + '%)') : '');
    Map.addLayer(tempC, thermalVis, layerName, false);
    exportDescriptors.push({
      name: layerName,
      image: tempC,  // Celsius image ready for export
      scale: 30
    });
  })(i);
}

// 9) Legend (minimal UI)
function makeColorBar(palette, min, max) {
  var gradient = ee.Image.pixelLonLat().select('longitude')
    .multiply((max - min) / 255.0).add(min);
  var colorBar = gradient.visualize({min: min, max: max, palette: palette});
  return ui.Thumbnail({
    image: colorBar,
    params: {bbox: [0, 0, 1, 256], dimensions: '10x256'},
    style: {stretch: 'vertical', margin: '0 8px 0 0'}
  });
}

var legend = ui.Panel({
  widgets: [
    ui.Label('Surface Temperature (°C)', {fontWeight: 'bold'}),
    ui.Panel([
      makeColorBar(palette, stMinC, stMaxC),
      ui.Panel([
        ui.Label(stMinC.toFixed(2) + ' °C', {margin: '6px 0 0 0'}),
        ui.Label(stMaxC.toFixed(2) + ' °C', {margin: '6px 0 0 0'})
      ], ui.Panel.Layout.Flow('vertical'))
    ], ui.Panel.Layout.Flow('horizontal'))
  ],
  style: {position: 'bottom-left', padding: '8px'}
});
ui.root.insert(0, legend);

// 10) Export buttons panel (one per scene)

// Small panel at top-right
var exportPanel = ui.Panel({style: {position: 'top-right', padding: '8px', width: '360px'}});
exportPanel.add(ui.Label('Exports (click to create Drive task)', {fontWeight: 'bold'}));

for (var j = 0; j < exportDescriptors.length; j++) {
  (function(k) {
    var desc = exportDescriptors[k];
    var displayName = desc.name;
    var btn = ui.Button({
      label: 'Export: ' + displayName,
      onClick: function() {
        // Build a safe filename
        var safe = displayName.replace(/[^A-Za-z0-9]/g, '_').slice(0, 60);
        var filename = 'L8_STB10C_' + safe;
        // Export using correct region: use geometry.bounds()
        Export.image.toDrive({
          image: desc.image,
          description: 'Export_' + filename,
          folder: 'EarthEngineExports',
          fileNamePrefix: filename,
          region: geometry.bounds(),
          scale: desc.scale,
          crs: 'EPSG:3857',
          maxPixels: 1e13
        });
        print('Export task created for:', displayName, ' (scale: ' + desc.scale + ' m)');
      },
      style: {stretch: 'horizontal', margin: '6px 0 0 0'}
    });
    exportPanel.add(btn);
  })(j);
}

// Add the export panel to the UI
ui.root.insert(1, exportPanel);
