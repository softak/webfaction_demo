from stores.forms import ItemSearchForm


def has_store(request):
    if request.user.is_authenticated():
        request.user.has_store = hasattr(request.user, 'store')

    return {
        'search_form': ItemSearchForm(request.GET)
    }
