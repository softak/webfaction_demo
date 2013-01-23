var CollectionView = Backbone.View.extend({

    initialize: function(options) {
        this.el = $(this.el);
        this._views = {};
        this.collection.each(this._add, this);

        // Useful for subclasses (ex. DealSliderView)
        if (options.itemTmpl) {
            this.itemTemplate = _.template(this.$(options.itemTmpl).html());
        }

        _.bindAll(this, '_add', '_remove', '_reset');
        this.collection.bind('add', this._add);
        this.collection.bind('remove', this._remove);
        this.collection.bind('reset', this._reset);
    },

    _onAdd: function(view) {
        $(view.render().el).appendTo(this.el);
    },

    _add: function(model) {
        if (!this._views.hasOwnProperty(model.cid)) { // prevent duplicate views
            var view = this._constructView(model);
            this._views[model.cid] = view;
            if (this._onAdd) { this._onAdd(view); }
        }
    },

    _remove: function(model) {
        var view = this._views[model.cid];
        view.remove();
        if (this._onRemove) { this._onRemove(view); }
        delete this._views[model.cid];
    },

    _reset: function(models) {
        _(this._views).each(function(view, key) {
            view.remove();
            delete this._views[key];
        }, this);
        if (this._onReset) { this._onReset(); }
        models.each(this._add, this);
    },

    getViewFor: function(item) {
        return this._views[item.cid];
    }

});


var EditableViewMixin = {

    _turnOnEditable: function(editableArea, options) {
        var editableArea = $(editableArea),
            value = editableArea.html(),
            name = editableArea.data('name');

        var input = $('<input></input>', { type: 'text', name: name, value: value });
        var saveButton = $('<a></a>', { html: 'Save', 'class': 'save btn' });
        var cancelButton = $('<a></a>', { html: 'Cancel', 'class': 'cancel btn' });

        var that = this;

        editableArea.empty().append(input, saveButton, cancelButton);

        cancelButton.click(function() {
            editableArea.empty().html(value);
            if (options && options.onCancel) { options.onCancel(); }
            return false;
        });

        saveButton.click(function() {
            var attrs = {};
            attrs[name] = input.val();

            that.model.save(attrs, {
                error: function(model, errors) {
                    if (options && options.onError) { options.onError(model, errors); }
                },
                success: function(model) {
                    editableArea.empty().html(that.model.get(name));
                    if (options && options.onSuccess) { options.onSuccess(model); }
                }
            });
            return false;
        });
    }

};




var DropdownItemView = Backbone.View.extend({

    tagName: 'li',

    initialize: function(options) {
        this.el = $(this.el);
        this.modelAttr = options.modelAttr || 'name';
    },

    events: {
        'click': 'activate'
    },

    render: function() {
        this.el.html('<a href="#">' + this.model.get(this.modelAttr) + '</a>');
        return this;
    },

    activate: function() {
        this.el.addClass('active');
        this.trigger('activate', this);
    },

    deactivate: function() {
        this.el.removeClass('active');
        this.trigger('deactivate', this);
    }
});




var DropdownView = Backbone.View.extend({

    /**
     * @param {string|$} el  dropdown element selector.
     * @param {string|$} [toggleEl='.dropdown-toggle']  dropdown toggle element
     *                                                  selector.
     * @param {string} [activeClass='active']  class for an active toggle
     *                                         element.
     * @param {string|$} [menuEl='.dropdown-menu']  dropdown menu element 
     *                                              selector.
     * @param {string} [modelAttr='name']  model attribute to use for items
     *                                     content.
     * @param {string} [allOption='All']  text to display for "All" item.
     */
    initialize: function(options) {
        this.el = $(options.el);
        this.toggleEl = this.$(options.toggleEl || '.dropdown-toggle');
        this.activeClass = options.activeClass || 'active';
        this.menuEl = this.$(options.menuEl || '.dropdown-menu');
        this.modelAttr = options.modelAttr || 'name';

        this._views = this.collection.map(function(item) {
            var view = new DropdownItemView({
                model: item,
                modelAttr: this.modelAttr
            });

            view.bind('activate', this._select, this);

            this.menuEl.append(view.render().el);
            return view;
        }, this);

        var allAttrs = {};
        allAttrs[this.modelAttr] = options.allOption || 'All';
        var all = new Backbone.Model(allAttrs);
        var allView = new DropdownItemView({ model: all });
        allView.activate();
        allView.bind('activate', this._selectAll, this);

        if (this.collection.length > 0)
            this.menuEl.prepend('<li class="divider"></li>');
        this.menuEl.prepend(allView.render().el);
        this._views.unshift(allView);

        this._toggleAll = this.toggleEl.html(); // used in _selectAll

        this.render();
    },

    _deactivateOthers: function(view) {
        _(this._views).each(function(_view) {
            if (_view !== view)
                _view.deactivate();
        });
    },

    _select: function(view) {
        this.toggleEl.html(view.model.get(this.modelAttr));
        this.toggleEl.addClass(this.activeClass);
        this._deactivateOthers(view);
        this.trigger('select', view.model);
    },

    _selectAll: function() {
        this.toggleEl.html(this._toggleAll);
        this.toggleEl.removeClass(this.activeClass);
        this._deactivateOthers(this._views[0]);
        this.trigger('selectAll');
    }
});




var SelectView = Backbone.View.extend({

    initialize: function(options) {

        this.el = $(this.el);
        this.modelAttr = options.modelAttr || 'name';
        this.collection.each(function(model) {
            var $option = $('<option></option>');
            $option.html(model.get(this.modelAttr));
            $option.data('model', model);
            this.el.append($option);
        }, this);
    },

    events: {
        'change': '_select'
    },

    _select: function() {
        var model = this.$(':selected').data('model');
        console.log(model);
        if (model)
            this.trigger('select', model);
        else
            this.trigger('selectAll');
    }
});
