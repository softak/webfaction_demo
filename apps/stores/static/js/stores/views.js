/* 
 * ImageView may have two states: active and selected.
 * Active state: user clicked on the carousel and sees enlarged image.
 * Selected state: user sees lightbox with current image.
 */

/*
 * @class
 * @param {string|$} activeImageEl  active image puts into background of this element.
 * @param {string|$} lightboxEl  lightbox element.
 */
var ImageView = Backbone.View.extend({

    initialize: function(options) {
        this._activeImageEl = $(options.activeImageEl);
        this._lightboxEl = $(options.lightboxEl);
    },

    events: {
        'click': 'activate'
    },

    activate: function() {
        $(this.el).addClass('active');
        this._activeImageEl.css({
            'background-image': 'url(' + this.model.get('thumb') + ')'
        });

        var namespace = 'image' + this.model.get('id');
        this._lightboxEl.bind('show.' + namespace, _(this.select).bind(this));
        this._lightboxEl.bind('hide.' + namespace, _(this.deselect).bind(this));

        this.trigger('activate', this);
    },

    deactivate: function() {
        var namespace = 'image' + this.model.get('id');
        this._lightboxEl.unbind('show.' + namespace);
        this._lightboxEl.unbind('hide.' + namespace);

        this.trigger('deactivate', this);
    },

    select: function() {
        var lightboxContent = $('.modal-content', this._lightboxEl);
        lightboxContent.empty().append($loader);

        var that = this;
        $('<img />').attr('src', this.model.get('image')).load(function() {
            $loader.remove();
            $(this).appendTo(lightboxContent);
            that._lightboxEl.modal('fit');
        });
        this.trigger('select', this);

    },

    deselect: function() {
        this.trigger('deselect', this);
    },

    render: function() {
        var img = $('<img />').attr('src', this.model.get('thumb')).resize(60);
        $(this.el).append(img);
        return this;
    }

});


/*
 * @class
 * @param {string|$} lightboxEl  lightbox element
 * @param {string|$} activeImageEl  active image puts into background of this element.
 */
var ImageCollectionView = Backbone.View.extend({

    initialize: function(options) {
        this._identifiers = new CycledList([]);
        this._views = {};

        this._activeImageEl = $(options.activeImageEl);
        this._lightboxEl = $(options.lightboxEl);

        $('.next', this._lightboxEl).click(_(this._selectNextImage).bind(this));
        $('.prev', this._lightboxEl).click(_(this._selectPrevImage).bind(this));
        
        this.collection.each(function(image) {
            var view = new ImageView({
                model: image,
                activeImageEl: this._activeImageEl,
                lightboxEl: this._lightboxEl
            });

            this._views[image.id] = view;
            this._identifiers.push(image.id);

            view.bind('activate', this._onActivate, this);
            view.bind('select', this._onSelect, this);
        }, this);
        var defaultImage = this.collection.find(function(image) {
           return image.get('is_default');
        });
        var defaultImageId = (defaultImage && defaultImage.id) || this.collection.at(0).id;
        var activeView = this._views[defaultImageId];
        activeView.activate();
    },

    _onActivate: function(imageView) {
        if (this._activeView) {
            this._activeView.deactivate();
        }
        this._activeView = imageView;
    },

    _onSelect: function(imageView) {
        if (this._selectedView) {
            this._selectedView.deselect();
        }
        this._selectedView = imageView;
        this._identifiers.setCurrent(this._selectedView.model.id);
    },

    _selectNextImage: function() {
        this._views[this._identifiers.next()].select();
    },

    _selectPrevImage: function() {
        this._views[this._identifiers.prev()].select();
    }

});


var ItemView = Backbone.View.extend({

    /**
     * @param {string} tmpl  template.
     */
    initialize: function(options) {
        this.el = $(this.el);
        this.template = options.tmpl;
    },

    render: function() {
        var context = this.model.toJSON();
        if (!context.best_offer_price) {
            this.el.addClass('no-offer');
            context.best_offer_finishes_in = '';
            context.best_offer_price = '';
        } else {
            var finishDate = moment(context.best_offer_finish_date, 'YYYY-MM-DDTHH:mm:ss');
            var now = new Date(); 
            var nowUtc = new Date(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),
                                  now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds());
            context.best_offer_finishes_in = finishDate.from(moment(nowUtc));
        }

        this.el.html(this.template(context)).find('.money').formatMoney();
        return this;
    }
});


var ItemListView = Backbone.View.extend({

    /**
     * @param {string|$} el  list container element selector.
     *
     * @param {string|$} [emptyListEl='.empty']  empty list notification
     *                   element.
     * @param {string|$} [emptyListReplaceEl='.product-list section']
     *                   element that is being replaced with empty list
     *                   notification element.
     * @param {string|$} [listEl='.items']  list element selector.
     * @param {string|$} [itemTmpl='.itemTemplate']  item template selector.
     *
     * @param {string|$} [paginatorEl='.pagination']  paginator selector.
     * @param {string|$} [paginatorTmpl='.paginatorTemplate']  paginator
     *                   template selector.
     */
    initialize: function(options) {
        this.el = $(this.el);
        this.emptyListEl = this.$(options.emptyListEl || '.empty');
        this.emptyListReplaceEl = this.$(options.emptyListReplaceEl || '.product-list section');
        this.listEl = this.$(options.listEl || '.items');
        this.itemTmpl = _.template(this.$(this.options.itemTmpl || '.itemTemplate').html());

        this._itemViews = {};
        this.collection.bind('reset', this._reset, this);

        this.paginatorEl = this.$(options.paginatorEl || '.pagination');
        this.paginatorTmpl = _.template(this.$(options.paginatorTmpl || '.paginatorTemplate').html());

        // `events` is called after `initialize` so we should do that way :(
        events = {};
        var selector = this.paginatorEl.selector;
        events['click ' + selector + ' .prev'] = 'prevPage';
        events['click ' + selector + ' .next'] = 'nextPage';
        events['click ' + selector + ' .page-number'] =  '_selectPage';
        this.delegateEvents(events);
    },

    _selectPage: function(e) {
        this.collection.fetchPage($(e.target).data('number'));
    },

    prevPage: function() {
        this.collection.fetchPrevPage();
    },

    nextPage: function() {
        this.collection.fetchNextPage();
    },

    render: function() {
        if (this.collection.pages <= 1 )
            this.paginatorEl.hide();
        else {
            this.paginatorEl.html(
                this.paginatorTmpl({
                    collection: this.collection,
                    pages: _.range(1, this.collection.pages + 1)
                })
            );
            this.paginatorEl.show();
        }
        if (!this.collection.length) {
          this.emptyListReplaceEl.hide();
          this.emptyListEl.show();
        }
        return this;
    },

    _reset: function(items) {
        _(this._itemViews).chain().each(function(view, key) {
            view.remove();
            delete this._itemViews[key];
        }, this);

        items.each(function(item) {
            var view = new ItemView({
                model: item,
                tagName: 'li',
                tmpl: this.itemTmpl
            });
            this.listEl.append(view.render().el);
            this._itemViews[item.cid] = view;
        }, this);
        this.render();
    },
});


var StoreInfoView = Backbone.View.extend({

    /**
     * @param {string|$} el  store information element selector.
     * @param {string|$} [tmpl='.storeTemplate']  store information template 
     *                   element selector.
     */
    initialize: function(options) {
        this.el = $(this.el);
        this._containers = [];
        this._tmpls = [];
        var that = this;
        this.$(options.tmpl || '.storeTemplate').each(function() {
            var $tmpl = $(this);
            that._containers.push($tmpl.parent());
            that._tmpls.push(_.template($tmpl.html()));
        });
        this.model.bind('change', this.render, this);
    },

    render: function() {
        _(this._tmpls).each(function($container, tmpl) {
            for (var i = 0,
                     $container,
                     tmpl;
                 $container = this._containers[i],
                 tmpl = this._tmpls[i++];)
            {
                $container.html(tmpl(this.model.attributes));
            }
        }, this);
        return this;
    }
});


var SearchResultsInfoView = Backbone.View.extend({

    initialize: function(options) {
        this.el = $(this.el);
        this._containers = [];
        this._tmpls = [];
        var that = this;
        this.$(options.tmpl || '.resultsTemplate').each(function() {
            var $tmpl = $(this);
            that._containers.push($tmpl.parent());
            that._tmpls.push(_.template($tmpl.html()));
        });
        this.collection.bind('reset', this.render, this);
    },

    render: function() {
        _(this._tmpls).each(function($container, tmpl) {
            for (var i = 0,
                     $container,
                     tmpl;
                 $container = this._containers[i],
                 tmpl = this._tmpls[i++];)
            {
                $container.html(tmpl({ 'collection': this.collection }));
            }
        }, this);
        return this;
    }
});
