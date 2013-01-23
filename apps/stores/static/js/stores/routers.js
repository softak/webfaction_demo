var ItemRouter = Backbone.Router.extend({

    routes: {
        '': 'start',
        '!/': 'start'
    },

    start: function () {
    },

    initialize: function(options) {
        var itemPageView = new ItemPageView({
            el: $('#store-item'),
            priceTemplate: getTemplate('price-template'),
            item: options.item,
            images: options.images
        });
    }

});


var StoreRouter = Backbone.Router.extend({

    routes: {
        '': 'start',
        ':page': 'start'
    },

    start: function(page) {
        if (page) {
            try {
              this.items.page = parseInt(page);
            } catch(e) {}
        }

        this.$loader.show();
        this.items.fetch();
        this.store.fetch();
    },

    initialize: function(options) {
        this.storeId = options.id;
        this.$loader = $('#store .loader');

        this.items = new PaginatedItemCollection([], {
            perPage: 8
        });
        this.items.url = API_URL + 'item/?store=' + this.storeId;
        this.items.bind('reset', function() {
            if (this.items.page == 1) {
                this.navigate();
            } else {
                this.navigate(this.items.page.toString());
            }
        }, this).bind('page', function() {
            this.$loader.show();
        }, this).bind('reset', function() {
            this.$loader.hide();
        }, this);
        this.itemListView = new ItemListView({ 
            collection: this.items,
            el: '#store'
        });

        this.store = new Store({ id: this.storeId });
        this.storeInfoView = new StoreInfoView({
            model: this.store,
            el: '#store'
        });
    }

});


var SearchResultsRouter = Backbone.Router.extend({

    routes: {
        '': 'start',
        ':page': 'start'
    },

    start: function(page) {
        if (page) {
            try {
                this.items.page = parseInt(page);
            } catch(e) {}
        }
        this.$loader.show();
        this.items.fetch();
    },

    initialize: function(options) {
        this.$loader = $('#search-results .loader');
        this.query = options.query
        this.items = new PaginatedItemCollection([], { perPage: 8 });
        this.items.url = API_URL + 'item/?query=' + options.query
        this.items.bind('reset', function() {
            if (this.items.page == 1) {
                this.navigate();
            } else {
                this.navigate(this.items.page.toString());
            }
        }, this).bind('page', function() {
            this.$loader.show();
        }, this).bind('reset', function() {
            this.$loader.hide();
        }, this);
        this.itemListView = new ItemListView({
            collection: this.items,
            el: '#search-results'
        });
        this.resultsInfoView = new SearchResultsInfoView({
            collection: this.items,
            el: '#search-results'
        });
    }
});
