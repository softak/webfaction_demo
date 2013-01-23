window.ShippingRequestsManageRouter = Backbone.Router.extend

    routes:
        '': 'start'

    start: ->

    initialize: (options) ->
        new ShippingRequestsView
            collection: new ShippingRequestCollection(options.shipping_requests)
            el: $('.shipping-requests')
            template: getTemplate('shipping-request-template')
