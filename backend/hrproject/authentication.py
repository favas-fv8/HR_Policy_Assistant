from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """Authenticates requests using the ``Authorization: Bearer <token>`` header.

    The React frontend sends the dj_rest_auth token with a ``Bearer`` prefix,
    which is the convention it already uses across all API services.
    """

    keyword = "Bearer"
