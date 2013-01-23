var Item = Backbone.RelationalModel.extend({
    url: function() {
        return API_URL + 'item/' + this.get('id') + '/'; // trailing slash is important
    }
});


var PaginatedItemCollection = PaginatedCollection.extend({
    model: Item,
    url: API_URL + 'item/'
});


var ItemCollection = Backbone.Collection.extend({
    model: Item,
    url: API_URL + 'item/'
});


/**
 * @class
 * @property {integer} id  identifier of the image.
 * @property {string} image  image url.
 * @property {boolean} is_default  true, if this image may be considered
 *                                 as default.
 * @property {strgin} thumb  thumbnail url.
 */
var Image = Backbone.Model.extend({
    url: function() {
        return API_URL + 'itemimage/' + this.get('id') + '/';
    }
});


var ImageCollection = Backbone.Collection.extend({
    model: Image
});




var StoreImage = Backbone.Model.extend({

    url: function() {
        return API_URL + 'storeimage/' + this.get('id') + '/';
    }
});




var StoreImageCollection = Backbone.Collection.extend({

    model: StoreImage
});




var Discount = Backbone.Model.extend({

    url: function() {
        return API_URL + 'discount/' + this.get('id') + '/';
    },

    _validate: function(name, value) {
        switch(name) {
            case 'name':
                if (value.length > 100) {
                    return { name: name, message: 'This field too long!' };
                }
                break;
            case 'for_additional_item':
            case 'for_additional_buyer':
            case 'lower_bound':
                if (typeof(value) == 'string' && !value.match(/^\d{1,2}(\.\d{1,2})?$/)) {
                    return { name: name, message: 'This field isn\'t decimal!' };
                }
                break;
        }
    },

    validate: function(attrs) {
        var errors = {}, isValid = true;

        $.each(attrs, _.bind(function(name, value) {
            var error = this._validate(name, value);
            if (error) {
                errors[error.name] = error.message;
                isValid = false;
            }
        }, this));

        if (!isValid) { return errors; }
    }

});


var DiscountCollection = Backbone.Collection.extend({
    model: Discount
});


var DiscountGroup = Backbone.Model.extend({

    url: function() {
        return API_URL + 'discount_group/' + this.get('id') + '/';
    },

    _validate: function(name, value) {
        
    },

    validate: function(attrs) {
        var errors = {}, isValid = true;

        $.each(attrs, _.bind(function(name, value) {
            var error = this._validate(name, value);
            if (error) {
                errors[error.name] = error.message;
                isValid = false;
            }
        }, this));

        if (!isValid) { return errors; }
    }

});


var DiscountGroupCollection = Backbone.Collection.extend({
    model: DiscountGroup
});
