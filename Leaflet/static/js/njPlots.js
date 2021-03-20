function buildMetadata(county) {
  d3.json("static/data/myCounties.json").then((data) => {
    var metadata = data.metadata[0];
    // Filter the data for the object with the desired sample number
    var resultArray = metadata.filter(countyObj => countyObj.County == county);
    var result = resultArray[0];
    // Use d3 to select the panel with id of `#sample-metadata`
    var PANEL = d3.select("#sample-metadata");

    // Use `.html("") to clear any existing metadata
    PANEL.html("");

    // Use `Object.entries` to add each key and value pair to the panel
    // Hint: Inside the loop, you will need to use d3 to append new
    // tags for each key-value in the metadata.
    Object.entries(result).forEach(([key, value]) => {
      PANEL.append("h6").text(`${key.toUpperCase()}: ${value}`);
    });

    // BONUS: Build the Gauge Chart
    buildGauge(result.tax_rate);
  });
}

function buildCharts(county) {
  d3.json("static/data/myCounties.json").then((data) => {
    var county = data.County;
    var resultArray = samples.filter(countyObj => countyObj.id == county);
    var result = resultArray[0];

    var crimes = result.crimes;
    var crimeRate = result.crimes_values;

    // Build a Bubble Chart
    var bubbleLayout = {
      title: "Crimes Per County",
      margin: { t: 0 },
      hovermode: "closest",
      xaxis: { title: "County ID" },
      margin: { t: 30}
    };
    var bubbleData = [
      {
        x: crimes,
        y: crimeRate,
        text: crimes,
        mode: "markers",
        marker: {
          size: crimes_values,
          color: crimes,
          colorscale: "Earth"
        }
      }
    ];

    Plotly.newPlot("bubble", bubbleData, bubbleLayout);

    var yticks = otu_ids.slice(0, 10).map(otuID => `OTU ${otuID}`).reverse();
    var barData = [
      {
        y: yticks,
        x: crime_values.slice(0, 10).reverse(),
        text: crimes.slice(0, 10).reverse(),
        type: "bar",
        orientation: "h",
      }
    ];

    var barLayout = {
      title: "Top Crimes per County",
      margin: { t: 30, l: 150 }
    };

    Plotly.newPlot("bar", barData, barLayout);
  });
}

function init() {
  // Grab a reference to the dropdown select element
  var selector = d3.select("#selDataset");

  // Use the list of sample names to populate the select options
  d3.json("myCounties.json").then((data) => {
    var countyNames = data.County;

    countyNames.forEach((sample) => {
      selector
        .append("option")
        .text(sample)
        .property("value", sample);
    });

    // Use the first sample from the list to build the initial plots
    var firstSample = sampleNames[0];
    buildCharts(firstSample);
    buildMetadata(firstSample);
  });
}

function optionChanged(newSample) {
  // Fetch new data each time a new sample is selected
  buildCharts(newSample);
  buildMetadata(newSample);
}

// Initialize the dashboard
init();