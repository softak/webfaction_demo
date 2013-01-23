/**
 * @example
 * var c = new Backbone.Collection(models);
 * _(c).extend(CycleCollectionMixin);
 */
var CycleCollectionMixin = {

    after: function(model) {
        var next = this.detect(function(model) {
            if (this.found) return true;
            this.found = this.pivot == model;
        }, {
            pivot: model,
            found: false
        });
        if (!next) next = this.first();
        return next;
    },

    before: function(model) {
        trap = {
            prev: null
        }
        this.detect(function(_model) {
            if (_model == model) return true;
            this.prev = _model;
        }, trap);
        if (!trap.prev) trap.prev = this.last();
        return trap.prev;
    }
};




/**
 * @example
 * var c = new Backbone.Collection(models);
 * _(c).extend(FilterCollectionMixin);
 */
var FilterCollectionMixin = {

    _init: function() {
        if (!this._models)
            this._models = _(this.models).clone();
        if (!this._filters)
            this._filters = {}
    },

    addFilter: function(name, filter) {
        this._init();
        this._filters[name] = filter;
        this._filter();
    },

    removeFilter: function(name) {
        this._init();
        delete this._filters[name];
        this._filter();
    },

    _filter: function() {
        this.remove(this._models, {silent: true});
        this.add(_(this._models).reject(function(model) {
            for (var name in this._filters) {
                var filter = this._filters[name];
                if (!filter(model))
                    return true;
            }
            return false;
        }, this), {silent: true});
        this.trigger('reset');
    }
};




var FramedCollection = Backbone.Collection.extend({

    /**
     * @param {integer} [perFrame=20]  items per frame.
     */
    initialize: function(models, options) {
        options = _.extend({ perFrame: 20 }, options);
        this.perFrame = options.perFrame || 20;
        this.frame = 1;
        this.bind('reset', function() {
            this.frame = 1;
        }, this);
    },

    setFrame: function(number) {
        if (number > 0 && this.length >= (number-1)*this.perFrame) {
            this.frame = number;
            this.trigger('frame');
        }
    },

    setFrameFor: function(ordinal) {
        if (ordinal > 0 && ordinal <= this.length) {
            this.setFrame(Math.ceil(ordinal/this.perFrame));
        }
    },

    nextFrame: function() {
        this.setFrame(this.frame + 1);
    },

    prevFrame: function() {
        this.setFrame(this.frame - 1);
    },

    hasNextFrame: function() {
        return this.frame < this.getFrameCount();
    },

    hasPrevFrame: function() {
        return this.frame > 1;
    },

    getFrameFrom: function() {
        return (this.frame-1)*this.perFrame + 1;
    },

    getFrameTo: function() {
        return Math.min(this.frame*this.perFrame, this.length);
    },

    getFrame: function() {
        return this.models.slice((this.frame-1)*this.perFrame, this.frame*this.perFrame);
    },

    getFrameCount: function() {
        return Math.ceil(this.length / this.perFrame);
    }
});




var PaginatedCollection = Backbone.Collection.extend({

    /**
     * @param {integer} [perPage=20]  item per page.
     */
    initialize: function(models, options) {
        options = _.extend({ perPage: 20 }, options);
        this.perPage = options.perPage;
        if (options.total) {
            this.total = options.total;
            this.pages = Math.ceil(this.total / this.perPage);
        }
        this.page = 1;
    },

    fetch: function(options) {
        options = _.extend({ data: {} }, options);
        _.extend(options.data, {
            limit: this.perPage,
            offset: (this.page - 1) * this.perPage
        });

        return Backbone.Collection.prototype.fetch.call(this, options);
    },

    parse: function(response) {
        this.total = response.meta.total_count;
        this.pages = Math.ceil(this.total / this.perPage);
        return response.objects;
    },

    hasNextPage: function() { return this.page + 1 <= this.pages; },

    hasPrevPage: function() { return this.page - 1 > 0; },

    fetchPage: function(number, options) {
        this.page = number;
        this.fetch(options);
        this.trigger('page', this.page);
    },

    fetchNextPage: function(options) {
        if (this.hasNextPage()) {
            this.page++;
            this.trigger('page', this.page);
            return this.fetch(options);
        } else {
          return false;
        }
    },

    fetchPrevPage: function(options) {
        if (this.hasPrevPage()) {
            this.page--;
            this.trigger('page', this.page);
            return this.fetch(options);
        } else {
          return false;
        }
    }
});
