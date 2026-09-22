from django.conf import settings

from .registries import EmailContextType


class CoreEmailContextType(EmailContextType):
    """
    An `EmailContextType` represents a context in which an email can be sent.
    """

    type = "core"

    def get_context(self):
        return {
            "public_backend_hostname": settings.PUBLIC_BACKEND_HOSTNAME,
            "public_backend_url": settings.PUBLIC_BACKEND_URL,
            "public_web_frontend_hostname": settings.PUBLIC_WEB_FRONTEND_HOSTNAME,
            "public_web_frontend_url": settings.PUBLIC_WEB_FRONTEND_URL,
            "jadawel_embedded_share_url": settings.JADAWEL_EMBEDDED_SHARE_URL,
            "jadawel_embedded_share_hostname": settings.JADAWEL_EMBEDDED_SHARE_HOSTNAME,
            "logo_url": settings.PUBLIC_WEB_FRONTEND_URL + "/img/logo.png",
            "logo_additional_text": "",
            "show_jadawel_description": True,
        }
