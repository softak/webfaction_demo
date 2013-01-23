$(document).ready(function() {

    window.models = [
        {
            id: 1,
            title: 'hello'
        },
        {
            id: 2,
            title: 'world'
        },
        {
            id: 3,
            title: 'bye'
        }
    ];


    module('CycleCollectionMixin');

    test('after', function() {
        var c = new Backbone.Collection(models);
        _(c).extend(CycleCollectionMixin);
        equals(c.after(c.at(0)), c.at(1));
        equals(c.after(c.at(1)), c.at(2));
        equals(c.after(c.at(2)), c.at(0));
    });

    test("before", function() {
        var c = new Backbone.Collection(models);
        _(c).extend(CycleCollectionMixin);
        equals(c.before(c.at(2)), c.at(1));
        equals(c.before(c.at(1)), c.at(0));
        equals(c.before(c.at(0)), c.at(2));
    });


    module('FilterCollectionMixin');

    test("addFilter", function() {
        var c = new Backbone.Collection(models);
        _(c).extend(FilterCollectionMixin);
        c.addFilter('excludeStore', function(item) {
            return item.get('id') != 1;
        });
        equals(c.length, 2);
        equals(c.at(0).get('id'), 2);
        equals(c.at(1).get('id'), 3);
    });

    test("removeFilter", function() {
        var c = new Backbone.Collection(models);
        _(c).extend(FilterCollectionMixin);
        c.addFilter('singleStore', function(item) {
          return item.get('id') == 1;
        });
        equals(c.length, 1);
        c.removeFilter('singleStore');
        equals(c.length, 3);
    });
});
