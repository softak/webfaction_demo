from django.db import transaction
from django.utils.decorators import method_decorator


class TryCompletePendingTransactionMiddleware(object):
    @method_decorator(transaction.commit_on_success)
    def process_request(self, request):
        user = request.user
        if not (user.is_authenticated() and user.profile.pending_transaction):
            return

        transaction = user.profile.pending_transaction
        transaction.try_complete()

        if not transaction.is_approved:
            transaction.cancel()
