var API_URL = '/stores/api/v1/';

_.templateSettings = {
    interpolate: /__(.+?)__/g,
    evaluate: /<%(.+?)%>/g
}

Backbone.Model.prototype.isNew = function() {
    return this.id == null && !this.has('id');
}
