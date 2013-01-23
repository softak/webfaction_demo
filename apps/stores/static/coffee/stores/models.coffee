# TODO Introduce modules?

# ShippingRequest
window.ShippingRequest = Backbone.RelationalModel.extend
    relations: [{
            type: Backbone.HasOne
            key: 'social_buy'
            relatedModel: 'ShippingRequestSocialBuy'
            reverseRelation:
                key: 'shipping_request'
                type: Backbone.HasOne
        }]
    url: -> @.get('resource_uri')


window.ShippingRequestCollection = Backbone.Collection.extend
    model: ShippingRequest
# / ShippingRequest

window.ShippingRequestSocialBuy = Backbone.RelationalModel.extend
    relations: [{
            type: Backbone.HasMany
            key: 'tags'
            relatedModel: 'ShippingRequestSocialTag'
            collectionType: 'ShippingRequestSocialTagCollection'
            reverseRelation: {
                key: 'buy'
            }
        }]

# ShippingRequestSocialTag
window.ShippingRequestSocialTag = Backbone.RelationalModel.extend({ })

window.ShippingRequestSocialTagCollection = Backbone.Collection.extend
    model: ShippingRequestSocialTag
    comparator: (tag) -> return tag.get('item_name')
# / ShippingRequestSocialTag
