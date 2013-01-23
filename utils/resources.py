from tastypie.authorization import Authorization
import commonware.log


log = commonware.log.getLogger('utils')


# Waiting for better times when tastypie guys make row-level permissions right
class AuthorityAuthorization(Authorization):

    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')

    def __init__(self, allowed_methods=None):
        if allowed_methods is not None:
            self.allowed_methods = allowed_methods

    def is_authorized(self, request, object=None):
        if object is None:
            return True

        if request.method == 'GET':
            return True

        klass = self.resource_meta.object_class

        # cannot check permissions if we don't know the model
        if not klass or not getattr(klass, '_meta', None):
            return True

        if request.method not in self.allowed_methods:
            return False

        # user must be logged in to check permissions
        # authentication backend must set request.user
        if not hasattr(request, 'user'):
            return False

        return self.is_author(request.user, object)

    def is_author(self, user, object):
        raise NotImplemented


def authority(rule):
    class auth_class(AuthorityAuthorization):
        def is_author(self, user, object):
            return rule(user, object)
    return auth_class()
