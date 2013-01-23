window.ItemPageView = Backbone.View.extend

    initialize: (options) ->
        @_priceTemplate = options.priceTemplate
        @el = $(options.el)

        itemData = options.item
        buys = options.item.buys
        delete itemData['buys']

        @_item = new Item(itemData)

        personalTag = if itemData.personal_tag then new ItemPersonalTag(itemData.personal_tag)
        if personalTag then personalTag.set(item: @_item)

        socialBuys = new ItemSocialBuyCollection(buys)
        socialBuys.each (buy) => buy.set(item: @_item)

        images = new ImageCollection(options.images)

        tagView = new ItemPersonalTagView
            model: personalTag
            item: @_item
            el: @$('.personal-tag')

        socialBuysView = new ItemSocialBuysView
            collection: socialBuys
            el: @$('.buy-list')

            createFormEl: @$('.start-social-buy-form')
            createFormModalEl: @$('#start-buy-modal')
            item: @_item

            template: getTemplate('buy-list')
            buyTemplate: getTemplate('social-buy-template')

        imagesView = new ImageCollectionView
            collection: images
            activeImageEl: @$('.thumb')
            lightboxEl: @$('#gallery')

        @.render()

    render: ->
        itemPrice = @_item.get('price')
        discountedPrice = @_item.get('discounted_price')
        delta = Math.round((itemPrice - discountedPrice) * 100) / 100
        deltaInPercent = Math.round((1 - discountedPrice / itemPrice) * 100)
        @$('.buy-now .price').html(@_priceTemplate({
            original_price: itemPrice
            your_price: discountedPrice
            delta: delta
            deltaInPercent: deltaInPercent
        })).find('.money').formatMoney()
