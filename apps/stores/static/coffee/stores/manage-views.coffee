window.ShippingRequestView = Backbone.View.extend
    tagName: 'li'

    initialize: (options) ->
        @el = $(@el)
        @_template = options.template
    
    events:
        'click .controls .cancel': '_cancel'
        'click .controls .set-price': '_showSetPriceForm'
        'click .set-price-form .cancel': '_hideSetPriceForm'
        'click .set-price-form .submit': '_setPrice'

    _cancel: ->
        if not window.confirm('Are you sure?') then return
        @el.addClass('loading')
        @model.destroy success: => @el.removeClass('loading')
    
    _setPrice: ->
        @el.addClass('loading')
        @model.save({
            price: @$('.set-price-form .postage-price').val()
        }, {
            success: =>
                @el.removeClass('loading')
                @.remove() # TODO ???
        })
        return false
    
    _showSetPriceForm: ->
        @el.addClass('setting-price')
        return false

    _hideSetPriceForm: ->
        @el.removeClass('setting-price')
        return false
    
    render: (template) ->
        @el.html(@_template(@model.toJSON()))
        @el.find('.money').formatMoney()
        return @
    

window.ShippingRequestsView = CollectionView.extend

    initialize: (options) ->
        @_template = options.template
        @constructor.__super__.initialize.apply(this, arguments)
    
    _constructView: (shippingRequest) ->
        return new ShippingRequestView
            model: shippingRequest
            template: @_template
    
    _onAdd: (view) ->
        @el.prepend(view.render().el)
