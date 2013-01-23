/*
 * @class
 * @param {_.template} template  compiled underscore.js template.
 * @param {_.template} editItemModalTemplate  compiled underscore.js template.
 */
var ItemView = Backbone.View.extend({

    tagName: 'li',

    initialize: function(options, lala) {
        this._template = options.template;
        this._imageTemplate = options.imageTemplate;
        this._modalTemplate = options.editItemModalTemplate;

        this._lightboxEl = $('<div></div>', {
            'class': 'item modal scrollable hide fade',
        }).appendTo('body').modal({ backdrop: true });

        _.bindAll(this, 'remove', 'render');
        this.model.bind('destroy', this.remove);
        this.model.bind('change', this.render);
    },

    events: {
        'click .delete': '_handleDelete'
    },

    _handleDelete: function() {
        this.model.destroy();
        return false;
    },

    lightbox: function(page) {
        if (!this.lightboxInitialized) {
            var imagesUrl = '/stores/api/v1/itemimage/?format=json&item=' + this.model.get('id');

            // Render lightbox
            var modalHtml = this._modalTemplate({
                item: this.model,
                imagesUrl: imagesUrl
            });
            this._lightboxEl.html(modalHtml);

            // Bind forms to this instance
            _(['name', 'description', 'price', 'discount',
               'quantity', 'discount_group']).each(_.bind(function(name) {
                this._lightboxEl.find('.item-pane *[name=' + name + ']').val(this.model.get(name));
            }, this));
            if (this.model.get('is_out_of_stock')) {
                this._lightboxEl.find('.item-pane input[name=is_out_of_stock]').attr('checked', true);
            }
            this._lightboxEl.find('.images-pane input[name=item]').val(this.model.get('id'));

            // Initialize images collection view
            var images = new ImageCollection;
            images.url = imagesUrl;

            images.fetch({
                success: _.bind(function() {
                    var imagesView = new ImagesView({
                        collection: images,
                        el: this._lightboxEl.find('.images-pane'),
                        imageTemplate: this._imageTemplate //_.template($('#item-image-template').text())
                    });

                    imagesView.bind('default_image_changed', _.bind(function() {
                        this.model.fetch();
                    }, this));
                }, this)
            });

            // Enliven item form
            new AjaxForm({
                form: this._lightboxEl.find('.item-pane form'),

                onSuccess: _(function(updatedItemData) {
                    this.model.set(updatedItemData);
                    this._lightboxEl.modal('hide');
                }).bind(this)
            });

            this.lightboxInitialized = true;
        }

        if (this._lightboxEl.is(':hidden')) {
            this._lightboxEl.modal('show').one('hidden', function() {
                app.navigate('#');
            });
        }

        // Deactivate all tabs and pans
        this._lightboxEl.find('.active').removeClass('active');
        // Activate current tab and pan (.images-pane and .images-tab, for example)
        this._lightboxEl.find('.' + page + '-pane, .' + page + '-tab').addClass('active');
        // Tell modal that his content changed
        this._lightboxEl.modal('fit');
    },
 
    render: function(template) {
        $(this.el).html(this._template(this.model.toJSON()));
        return this;
    }

});


/*
 * @class
 * @param {_.template} itemTemplate  compiled underscore.js template.
 * @param {_.template} editItemModalTemplate  compiled underscore.js template.
 * @param {_.template} paginatorTemplate  compiled underscore.js template.
 * @param {$|string} el  must contain `.pagination` and `.list`.
 */
var ItemsView = CollectionView.extend({

    initialize: function(options) {
        this._lightboxEl = $('<div></div>', {
            'class': 'item modal scrollable hide fade'
        }).appendTo('body').modal({ backdrop: true });
        this._paginatorEl = this.$('.pagination');
        this._itemsListEl = this.$('.list');
        
        this._itemTemplate = options.itemTemplate;
        this._imageTemplate = options.imageTemplate;
        this._modalTemplate = options.editItemModalTemplate; 
        this._paginatorTemplate = options.paginatorTemplate;

        this.constructor.__super__.initialize.apply(this, arguments);
        this.render();
    },

    events: {
        'click .pagination .prev': 'prevPage',
        'click .pagination .next': 'nextPage',
        'click .pagination .page-number': 'page'
    },

    page: function(e) {
        var pageNumber = $(e.target).data('number');
        this.collection.fetchPage(pageNumber);
        return false;
    },

    prevPage: function() {
        this.collection.fetchPrevPage();
        return false;
    },

    nextPage: function() {
        this.collection.fetchNextPage();
        return false;
    },
    
    _constructView: function(item) {
        return new ItemView({
            model: item,
            lightboxEl: this._lightboxEl,
            template: this._itemTemplate,
            imageTemplate: this._imageTemplate,
            editItemModalTemplate: this._modalTemplate
        });
    },

    _onAdd: function(view) {
        this._itemsListEl.prepend(view.render().el);
    },

    _onReset: function(view) {
        this.render();
    },

    render: function() {
        if (this.collection.length > 0) {
            this._paginatorEl.html(
                this._paginatorTemplate({
                    collection: this.collection,
                    pages: _.range(1, this.collection.pages + 1)
                })
            );
        }
        return this;
    }

});


/*
 * @class
 * @param {_.template} itemTemplate  compiled underscore.js template.
 * @param {_.template} createItemModalTemplate  compiled underscore.js template.
 * @param {_.template} editItemmodalTemplate  compiled underscore.js template.
 * @param {$|string} createButtonEl  click on this element will open lightbox with form.
 * @param {$|string} el  must contain `.list`.
 */
var NewItemsView = CollectionView.extend({

    initialize: function(options) {
        this._lightboxEl = $('<div></div>', {
            'class': 'item modal scrollable hide fade'
        }).appendTo('body').modal({ backdrop: true });
        this._itemsListEl = this.$('.list');
        
        this._itemTemplate = options.itemTemplate;
        this._imageTemplate = options.imageTemplate;
        this._createItemModalTemplate = options.createItemModalTemplate;
        this._editItemModalTemplate = options.editItemModalTemplate;

        this._createButtonEl = $(options.createButtonEl);
        this._createButtonEl.click(_.bind(this._handleCreate, this));

        this.constructor.__super__.initialize.apply(this, arguments);
    },

    _constructView: function(item) {
        return new ItemView({
            model: item,
            lightboxEl: this._lightboxEl,

            template: this._itemTemplate,
            imageTemplate: this._imageTemplate,
            editItemModalTemplate: this._editItemModalTemplate
        });
    },

    _onAdd: function(view) {
        this._itemsListEl.append(view.render().el);
        this.el.show();
    },

    _onRemove: function(view) {
        if (this.collection.length === 0) {
            this.el.hide();
        }
    },

    _handleCreate: function(html) {
        var modalHtml = this._createItemModalTemplate({
            action: this.collection.url,
        });
        this._lightboxEl.html(modalHtml).modal('show');
        var form = this._lightboxEl.find('form');

        new AjaxForm({
            form: form,

            onSuccess: _(function(createdItemData) {
                this.collection.add(createdItemData);
                this._lightboxEl.modal('hide');
                app.navigate('#!/');
            }).bind(this)
        });
        return false;
    }

});


/*
 * @class
 * @param {_.template} template  compiled underscore.js template.
 */
var ItemImageView = Backbone.View.extend({
    
    tagName: 'li',

    initialize: function(options) {
        this._template = options.template;

        _.bindAll(this, '_onChange', 'remove');
        this.model.bind('destroy', this.remove);
        this.model.bind('change', this._onChange);
    },

    events: {
        'click .is-default': '_handleIsDefaultChange',
        'click .delete': '_handleDelete'
    },

    _disable: function() {
        $(this.el).addClass('disabled');
    },

    _enable: function() {
        $(this.el).removeClass('disabled');
    },

    _update: function(attributes) {
        this._disable();
        this.model.save(attributes, {
            success: _.bind(this._enable, this)
        });
    },
    
    _onChange: function() {
        if (this.model.hasChanged('is_default')) {
            if (this.model.get('is_default')) {
                $(this.el).addClass('default');
            } else {
                $(this.el).removeClass('default');
            }
        }
    },

    _handleDelete: function() {
        this._disable();
        this.model.destroy({
            success: _.bind(this._enable, this)
        });
        return false;
    },

    _handleIsDefaultChange: function(e) {
        var isDefault = this.model.get('is_default');
        this._update({ is_default: !isDefault });
        return false;
    },

    render: function() {
        $(this.el).html(this._template(this.model.toJSON()));

        this.$('.thumb').css({
            'background-image': 'url(' + this.model.get('thumb') + ')'
        });

        if (this.model.get('is_default')) {
            $(this.el).addClass('default');
        }

        $(this.el).hover(function() {
            $('.controls', this).show();
        }, function() {
            $('.controls', this).hide();
        });
        return this;
    }

});


/*
 * @class
 * @param {$|string} el  must contain .list and image upload form.
 * @param {_.template} template  compiled underscore.js template.
 */
var ImagesView = CollectionView.extend({

    initialize: function(options) {
        this._formEl = this.$('form');
        this._listEl = this.$('.thumbnails');
        this._imageTemplate = options.imageTemplate;
        this._noImagesMessage = $('<li></li>', {
            html: 'Item has no images'
        });

        this.constructor.__super__.initialize.apply(this, arguments);

        if (this.collection.length === 0) {
            this._noImagesMessage.appendTo(this.listEl);
        }

        _.bindAll(this, '_onChange');
        this.collection.bind('change', this._onChange);

        // Set up the form
        new qq.AjaxFileForm({
            form: this._formEl,
            onSuccess: _.bind(function(_1, _2, newImages) {
                this.collection.add(newImages);
            }, this)
        });
    },

    _constructView: function(image) {
        return new ItemImageView({
            model: image,
            template: this._imageTemplate
        });
    },

    _onAdd: function(view) {
        this._listEl.append(view.render().el);
        this._noImagesMessage.remove();
    },

    _onRemove: function(view) {
        if (this.collection.length === 0) {
            this._noImagesMessage.appendTo(this._listEl);
        }
    },

    _onChange: function(changedImage) {
        if (changedImage.hasChanged('is_default') && changedImage.get('is_default')) {
            this.collection.chain().without(changedImage).each(_.bind(function(image) {
                if (image.get('is_default')) {
                    image.save(
                        { is_default: false },
                        { success: _.bind(function() { this.trigger('default_image_changed'); }, this) }
                    );
                }
            }, this));
        }
    }

});




/*
 * @class
 * @param {_.template} template  compiled _-template
 */
var DiscountView = Backbone.View.extend({

    tagName: 'tr',

    className: 'discount',

    initialize: function(options) {
        this.el = $(this.el);
        this._template = options.template;
        this._changedAttrs = {};
        this.model.bind('destroy', _.bind(this.remove, this));
    },

    events: {
        'click .delete': '_handleDelete',
        'click .save': '_handleSave',
        'click .cancel-changes': '_handleCancel',

        'change *': '_handleChange'
    },

    _handleSave: function() {
        if (this.el.hasClass('loading'))
            return;

        this.el.addClass('loading');
        this.model.save(this._changedAttrs, {
            success: _.bind(function() {
                this.el.removeClass('active');
                this.el.removeClass('loading');
            }, this),

            error: _.bind(function(model, errors) {
                this.el.removeClass('loading');
                this._renderErrors(model, errors);
           }, this)
        });
    },

    _handleCancel: function() {
        if (this.el.hasClass('loading'))
            return;

        $.each(this._changedAttrs, _.bind(function(name) {
            var field = this.$('[data-name=' + name + ']');
            field.html(this.model.get(name));
        }, this));
        this._changedAttrs = {};

        this.el.removeClass('active');
    },

    _handleDelete: function() {
        if (this.el.hasClass('loading'))
            return;

        var hasDiscountGroups = this.model.get('discount_groups').length > 0;
        if (!hasDiscountGroups ||
                confirm('There is a discount group that uses that discount. Are you sure you want delete it?')) {
            this.el.addClass('loading');
            this.model.destroy({
                // Still required since AJAX request may fail
                success: _.bind(function() {
                    this.el.removeClass('loading');
                }, this)
            });
        }
    },

    _handleChange: function(e) {
        if (this.el.hasClass('loading'))
            return;

        var field = $(e.target),
            name = field.data('name'),
            value = field.text();

        value = $.trim(value);
        field.html(value);

        this._changedAttrs[name] = value;

        this.el.addClass('active');
    },


    _renderErrors: function(model, errors) {
        $.each(errors, _.bind(function(name, error) {
            var field = this.$('[data-name=' + name + ']');

            // Show red background for 1 second, for example // TODO
            field.css('background', 'red');
            _.delay(function() { field.css('background', 'white'); }, 1000);
        }, this));
    },

    render: function() {
        $(this.el).html(this._template(this.model.toJSON()));
        return this;
    }
});




/*
 * @class
 * @param {_.template} template  compiled _-template
 */
var DiscountsView = CollectionView.extend({

    initialize: function(options) {
        this.el = $(this.el);
        this._template = options.template;
        this.constructor.__super__.initialize.apply(this, arguments);

        this.$('[contenteditable]').live('focus', function() {
            var $this = $(this);
            $this.data('before', $this.html());
            return $this;
        }).live('blur  keyup  paste', function() {
            var $this = $(this);
            if ($this.data('before') !== $this.html()) {
                $this.data('before', $this.html());
                $this.trigger('change');
            }
            return $this;
        });
    },

    _constructView: function(discount) {
        return new DiscountView({
            model: discount,
            template: this._template
        });
    },

    _onAdd: function(view) {
        this.el.append(view.render().el);
    }

});




/*
 * @class
 * @param {_.template} template  compiled _-template
 * @param {DiscountCollection} discounts  all discount models of store
 */
var DiscountGroupView = Backbone.View.extend({

    tagName: 'tr',

    events: {
        'click .controls .edit': 'select',
        'click .delete': '_delete'
    },

    initialize: function(options) {
        this.el = $(this.el);
        this._template = options.template;
        this._discounts = options.discounts;

        this._selected = false;
        this.model.bind('change', this.render, this);
    },

    _delete: function() {
        this.el.addClass('disabled');
        window.setTimeout(_.bind(function() {
        this.model.destroy();
        }, this), 2000);
        return false;
    },

    select: function() {
        this._selected = true;
        this.model.trigger('select', this.model);
        this.render();
    },

    deselect: function(options) {
        this._selected = false;
        if (!(options && options.silent)) {
            this.model.trigger('deselect', this.model);
        }
        this.render();
    },

    render: function() {
        var context = _.extend(this.model.toJSON(), {
            selected: this._selected,
            discount: this._discounts.get(this.model.get('discount')).toJSON()
        });
        $(this.el).empty().append(this._template(context));
        return this;
    }

});


/*
 * @class
 * @param {_.template} template  compiled _-template
 * @param {_.template} formTemplate  compiled _-template
 * @param {DiscountCollection} discounts  all discount models of store
 * @param {ItemCollection} items  all items of store
 */
var DiscountGroupsView = CollectionView.extend({

    initialize: function(options) {
        this.el = $(this.el);
        this._template = options.template;
        this._formEl = $('#discount-form'); // TODO
        log(this._formEl);
        this._formTemplate = options.formTemplate;
        this._discounts = options.discounts;
        this._items = options.items;
 
        this.constructor.__super__.initialize.apply(this, arguments);

        _.bindAll(this, '_select', '_deselect');
        this.collection.bind('select', this._select);
        this.collection.bind('deselect', this._deselect);

        this._deselect();
    },

    _getItemsOff: function() {
        return this.collection.chain().map(function(group) { 
            return group.get('items');
        }).union().value();
    },

    _buildForm: function(group) {
        var form;
        if (group) {
            form = $(this._formTemplate({
                url: group.get('resource_uri'),
                method: 'PUT',
                header: 'Edit <b>' + group.get('name') + '</b>',

                group: group,
                items: this._items,
                items_off: this._getItemsOff(),
                discounts: this._discounts,
                submit_value: 'Save'
            }));
        } else {
            form = $(this._formTemplate({
                url: '/stores/api/v1/discount_group/',
                method: 'POST',
                header: 'Create new discount group',

                group: undefined,
                items: this._items,
                items_off: this._getItemsOff(),
                discounts: this._discounts,
                submit_value: 'Create'
            }));
        }
        $('button[type="reset"]', form).click(this._deselect);
        return form;
    },

    _updateForm: function(group) {
        var form = this._buildForm(group);
        this._formEl.replaceWith(form);
        this._formEl = form;

        new AjaxForm({
            form: form,
            onSuccess: _.bind(function(newData) {
                if (group) {
                    group.set(newData);
                    this._deselect();
                } else {
                    form.get(0).reset();
                    this.collection.add(newData);
                }
            }, this)
        });
    },

    _select: function(group) {
        if (this._selectedGroup) {
            this.getViewFor(this._selectedGroup).deselect({ silent: true });
        }
        this._selectedGroup = group;
        this._updateForm(this._selectedGroup);
    },

    _deselect: function() {
        this._selectedGroup = null;
        this._updateForm();
    },

    _constructView: function(group) {
        return new DiscountGroupView({
            model: group,
            discounts: this._discounts,
            template: this._template
        });
    },

    _onAdd: function(view) {
        this.el.append(view.render().el);
        this._deselect();
        // this._select(view.model);
    },

    _onRemove: function(view) {
        if (view.model == this._selectedGroup) {
            this._deselect();
        } else {
          this._updateForm(this._selectedGroup);
        }
    }

});




// Obsolete, use as an example
var StoreImageView = Backbone.View.extend({

    tagName: 'li',

    initialize: function(options) {
        this.template = options.template;
        this.el = $(this.el);
        _.bindAll(this, 'disable', 'enable');
    },

    events: {
        'click .delete': 'delete'
    },

    disable: function() {
        this.el.addClass('disabled');
    },

    enable: function() {
        this.el.removeClass('enabled');
    },

    delete: function() {
        this.disable();
        this.model.destroy({
            success: this.enable
        });
    },

    render: function() {
        this.el.empty().append(this.template(this.model.toJSON()));
        var that = this;
        this.el.hover(function() {
            that.el.addClass('hover');
        }, function() {
            that.el.removeClass('hover');
        });
        return this;
    }
});

// Obsolete
var StoreImagesView = CollectionView.extend({

    /**
     * @param {Collection} collection  collection of images.
     * @param {string|$} el  image collection element selector.
     * @param {string|$} formEl  upload form element selector.
     * @param {string|$} [tmpl='.template']  element template selector.
     */
    initialize: function(options) {
        this.el = $(this.el);
        this.formEl = $(options.formEl);
        this.template = _.template(this.$(options.tmpl || 'script.image').html());

        new qq.AjaxFileForm({
            form: this.formEl,
            onSuccess: _.bind(function(_1, _2, new_images) {
                this.collection.add(new_images);
            }, this)
        });

        this.constructor.__super__.initialize.apply(this, arguments);
    },

    _constructView: function(image) {
        return new StoreImageView({
            model: image,
            template: this.template
        });
    }
});
