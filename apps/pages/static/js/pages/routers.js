var NavigatorRouter = Backbone.Router.extend({

  routes: {
    '': 'start'
  },

  start: function() {
    this.navigator.render();
  },

  initialize: function(options) {
    this.stores = new StoreCollection(options.stores, { perPage: 5 });
    this.navigator = new StoreMapView({
      el: '#navigator .map .canvas',
      collection: this.stores,
      showIcons: true
    });
  }
});
