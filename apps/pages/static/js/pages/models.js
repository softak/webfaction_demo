/**
 * @class
 * @property {string} name  store name.
 * @property {integer} category_id  identifier of the store's category.
 * @property {float} lat  latitude.
 * @property {float} lng  longitude.
 * @property {string} html  HTML content of the store. Fetched.
 */
var Store = Backbone.Model.extend({

    url: function() {
      return API_URL + 'store/' + this.get('id') + '/';
    }
});




var StoreCollection = FramedCollection.extend({

    model: Store
});
_(StoreCollection.prototype).extend(CycleCollectionMixin, FilterCollectionMixin);
