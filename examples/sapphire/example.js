// Add some initial configuration data. Each widget's `metric` or `metrics`
// will contain data once the corresponding ajax request has been made.
var data = {
  url: 'http://go.vumi.org/api/v1/go/metrics/',
  token: 'token12345',
  step: 10000,
  widgets: {
    a: {
      results: [],
      title: 'A (last 30 days)',
      key: 'stores.store1.a.last',
      from: '-30d',
      interval: '1d',
      nulls: 'omit'
    },
    b: {
      results: [],
      title: 'B (last 30 days)',
      key: 'stores.store1.b.last',
      from: '-30d',
      interval: '1d',
      nulls: 'omit'
    },
    c: {
      results: [],
      title: 'C (last 30 days)',
      key: 'stores.store1.c.last',
      from: '-30d',
      interval: '1d',
      nulls: 'omit'
    },
    all: {
      from: '-1d',
      interval: '1h',
      nulls: 'omit',
      title: 'A, B and C today',
      metrics: [{
        results: [],
        title: 'A',
        key: 'stores.store1.a.last',
      }, {
        results: [],
        title: 'B',
        key: 'stores.store1.b.last'
      }, {
        results: [],
        title: 'C',
        key: 'stores.store1.c.last'
      }],
    }
  }
};


// Create the widget components. Widget configuration would be done here.
var last = sapphire.widgets.last();
var lines = sapphire.widgets.lines();


// Update the dashboard on page load, then every `data.step` milliseconds.
update();
setInterval(update, data.step);


// Select each widget element by id, then draw it using the sapphire components
// we created above
function draw() {
  d3.select('#a')
    .datum(data.widgets.a)
    .call(last);

  d3.select('#b')
    .datum(data.widgets.b)
    .call(last);

  d3.select('#c')
    .datum(data.widgets.c)
    .call(last);

  d3.select('#all')
    .datum(data.widgets.all)
    .call(lines);
}


// Updates each widget's metrics one by one, then draws the dashboard.
function update() {
  var i = -1;
  var widgets = d3.values(data.widgets);

  function next(err) {
    if (err) return console.error(err);
    if (++i < widgets.length) updateWidget(widgets[i], next);
  }

  next();
}


// Update a single widget's values by making an ajax request, then invokes a
// callback when done.
//
// 1. Create the request object as a json request to the configured url, with
// the from and interval parameters relevant to the widget and the auth token
// associated with the vumi-go account.
//
// 2. Add each of the widget's metrics to the query
//
// 3. Make the request
//
// 4. Update the widget's metrics with the response
//
// 5. Invoke the `done` callback so the next metric request or draw can happen
function updateWidget(widget, done) {
  d3.json(metricsUrl(widget))
    .header('Authorization', ['Bearer', data.token].join(' '))
    .get(function(err, result) {
      if (err) return done(err);
      updateMetrics(widget, result);
      draw();
      done();
    });
}


function metricsUrl(widget) {
  return data.url + '?' + queryString.stringify({
    from: widget.from,
    interval: widget.interval,
    nulls: widget.nulls,
    m: metrics(widget).map(function(d) { return d.key; })
  });
}


// Updates a widget's metric values using the given api response data.
function updateMetrics(widget, data) {
  metrics(widget)
    .forEach(function(d) {
      d.values = data[d.key] || [];
    });
}


// Accesses a widget's metric data.
//
// `last` widgets only have a single metric. This function simplifies things
// by allowing us to treat all widgets as having multiple widgets.
//
// Note that the `last` widget could have also been configured to handle this
// distinction. Using this approach instead just means less widget
// configuration is needed.
function metrics(widget) {
  return widget.metrics
    ? widget.metrics
    : [widget];
}
