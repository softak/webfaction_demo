/**
 * Represent framed collection on the map arranging current frame's stores.
 */
var StoreMapView = Backbone.View.extend({

  /**
   * @param {Collection<Store>} collection  collection of stores.
   * @param {string|$} el  map element selector.
   * @param {array} [mapOptions]  Google Map options extending defaults.
   */
  initialize: function(options) {
    this.el = $(this.el);
    this._showIcons = options.showIcons || false;

    var first = this.collection.first();
    var center = first && new google.maps.LatLng(first.get('lat'),
                                                 first.get('lng')) ||
                          new google.maps.LatLng(-33.90, 151.20);
    var mapOptions = _.extend({
      center: center,
      zoom: 4,
      mapTypeId: google.maps.MapTypeId.ROADMAP,
      scrollwheel: false
    }, options.mapOptions | {});
    this.map = new google.maps.Map(this.el.get(0), mapOptions);

    this._markers = {};
    this.collection.each(function(store) {
      var icon = this._showIcons ? new google.maps.MarkerImage(store.get('marker')) : undefined;
      var marker = new google.maps.Marker({
        map: this.map,
        position: new google.maps.LatLng(store.get('lat'),
                                         store.get('lng')),
        title: store.get('name'),
        icon: icon
      });
      marker.iconUrl = store.get('marker');
      this._markers[store.cid] = marker;

      var that = this;
      google.maps.event.addListener(marker, 'click', function(e) {
          that._select(store, marker);
      });
    }, this);

    this.collection.bind('reset', this.render, this);
    this.collection.bind('frame', this.render, this);
  },


  render: function() {
    var frame = _(this.collection.getFrame());

    // Reset map view
    if (frame.size() > 1) {
      var bounds = new google.maps.LatLngBounds();

      frame.each(function(store) {
        bounds.extend(new google.maps.LatLng(store.get('lat'),
                                             store.get('lng')));
      });
      this.map.fitBounds(bounds);
    } else if (frame.size() == 1) {
      var store = frame.first();
      this.map.setCenter(new google.maps.LatLng(store.get('lat'),
                                                store.get('lng')));
    }

    // Hide all markers
    for (id in this._markers) {
      var marker = this._markers[id];
      marker.setVisible(false);
    }
    // Show filtered only
    var selectedFound = false;
    frame.each(function(store) {
        var marker = this._markers[store.cid];
        var icon = new google.maps.MarkerImage(marker.iconUrl);
        marker.setIcon(icon);
        marker.setVisible(true);
        if (this.selected == store)
            selectedFound = true;
    }, this);
    if (!selectedFound) {
        this.deselect();
    }

  },

  _select: function(store, marker) {
      this.deselect();

      this.selected = store;
      var icon = new google.maps.MarkerImage(
        marker.iconUrl, null, null, null, new google.maps.Size(64,74)
      );
      marker.setIcon(icon);

      this.trigger('select', store);
  },

  select: function(store) {
      var ordinal = this.collection.indexOf(store) + 1;
      this.collection.setFrameFor(ordinal);
      return this._select(store, this._markers[store.cid]);
  },

  deselect: function() {
      if (this.selected) {
        var marker = this._markers[this.selected.cid];
        var icon = new google.maps.MarkerImage(marker.iconUrl);
        marker.setIcon(icon);
        this.selected = null;
        this.trigger('deselect');
      }
  },

  selectById: function(id) {
      return this.select(this.collection.getByAttr('id', id));
  },

  prevFrame: function() {
    if (this.collection.hasPrevFrame()) {
      this.deselect();
      this.collection.prevFrame();
    }
  },

  nextFrame: function() {
    if (this.collection.hasNextFrame()) {
      this.deselect();
      this.collection.nextFrame();
    }
  },

  prevStore: function() {
    if (this.selected) {
      this.select(this.collection.before(this.selected));
    } else {
      this.select(this.collection.at(this.collection.getFrameTo()-1));
    }
  },

  nextStore: function() {
    if (this.selected) {
      this.select(this.collection.after(this.selected));
    } else {
      this.select(this.collection.at(this.collection.getFrameFrom()-1));
    }
  }
});



