from django.conf import settings
from ikwen.foundation.core.context_processors import project_settings as ikwen_settings

from ikwen.foundation.core.views import IKWEN_BASE_URL


def project_settings(request):
    """
    Adds utility project url and ikwen base url context variable to the context.
    """
    carplot_settings = ikwen_settings(request)['settings']
    carplot_settings.update({
        # 'IS_PROVIDER': getattr(settings, 'IS_PROVIDER', False),
        # 'IS_RETAILER': getattr(settings, 'IS_RETAILER', False),
        # 'IS_DELIVERY_COMPANY': getattr(settings, 'IS_DELIVERY_COMPANY', False),
        # 'IS_PRO_VERSION': getattr(settings, 'IS_PRO_VERSION', False),
        # 'CHECKOUT_MIN': getattr(settings, 'CHECKOUT_MIN'),
        # 'TEMPLATE_WITH_HOME_TILES': getattr(settings, 'TEMPLATE_WITH_HOME_TILES', False),
    })
    return {
        'settings': carplot_settings
    }