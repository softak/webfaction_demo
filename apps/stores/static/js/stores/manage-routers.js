var DiscountManageRouter = Backbone.Router.extend({

    routes: {
        '': 'start',
    },

    start: function () { },

    initialize: function(options) {
        var discounts = new DiscountCollection(options.discounts);
        var discountsView = new DiscountsView({
            collection: discounts,
            el: $('.discounts'),
            template: _.template($('#discount-template').text())
        });

        var form = $('#create-discount');

        new AjaxForm({
            form: form,

            onSuccess: function(discount) {
                console.log('Success! :)');
                form.get(0).reset();
                discounts.add(discount);
            },

            onError: function() {
                console.log('Error :(');
            }
        });
    }

});


var DiscountGroupManageRouter = Backbone.Router.extend({

    routes: {
        '': 'start',
    },

    start: function () { },

    initialize: function(options) {
        var groupsView = new DiscountGroupsView({
            collection: new DiscountGroupCollection(options.discount_groups),
            discounts: new DiscountCollection(options.discounts),
            items: new ItemCollection(options.items),

            el: $('.discount-groups'),

            template: _.template($('#discount-group-template').text()),
            formTemplate: _.template($('#create-discount-group-form-template').text())
        });
    }
});


var ItemManageRouter = Backbone.Router.extend({

    routes: {
        '': 'start',
        ':id/:page/': 'page',
        ':id/': 'page'
    },

    start: function() { },

    _putItemInCollection: function(id, callback) {
        var alreadyInItems = this.items.getByAttr('id', id) !== undefined;
        var alreadyInCreatedItems = this.createdItems.getByAttr('id', id) !== undefined;
        var item;
            log('here', alreadyInItems, alreadyInCreatedItems, id, '!');
        if (!alreadyInItems && !alreadyInCreatedItems) {
            item = new Item({ id: id });
            item.fetch({
                success: _.bind(function(item) {
                    this.items.add(item);
                    var view = this.itemsView.getViewFor(this.items.getByAttr('id', id));
                    callback(view);
                }, this)
            });
        } else if (alreadyInItems) {
            view = this.itemsView.getViewFor(this.items.getByAttr('id', id));
            callback(view);
        } else if (alreadyInCreatedItems) {
            view = this.newItemsView.getViewFor(this.createdItems.getByAttr('id', id));
            callback(view);
        }
    },

    page: function(id, page) {
        log('id', id, 'page', page);
        this._putItemInCollection(id, _.bind(function(itemView) {
            itemView.lightbox(page || 'item');
        }, this));
    },

    initialize: function(options) {
        this.storeId = options.id;

        this.items = new PaginatedItemCollection(options.items, {
            perPage: options.perPage,
            total: options.itemsTotal
        });
        this.createdItems = new ItemCollection([]);

        this.items.url = this.createdItems.url = API_URL + 'item/?store=' + this.storeId;
        this.items.comparator = this.createdItems.comparator = function(chapter) {
            return parseInt(chapter.get('id'), 10);
        };

        this.itemsView = new ItemsView({
            collection: this.items,
            el: $('.items'),

            itemTemplate:           getTemplate('item-template'),
            imageTemplate:          getTemplate('item-image-template'),
            paginatorTemplate:      getTemplate('paginator-template'),
            editItemModalTemplate:  getTemplate('edit-item-modal-template')
        });

        this.newItemsView = new NewItemsView({
            collection: this.createdItems,
            el: $('.new-items'),
            createButtonEl: $('.create-item'),

            itemTemplate:               getTemplate('item-template'),
            imageTemplate:              getTemplate('item-image-template'),
            createItemModalTemplate:    getTemplate('create-item-modal-template'),
            editItemModalTemplate:      getTemplate('edit-item-modal-template')
        });
    }

});
