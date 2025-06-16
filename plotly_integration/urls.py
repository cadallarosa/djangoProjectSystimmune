from django.urls import path
from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
# from .views import trigger_opc_import

urlpatterns = [
    # path('plotly_dash/', views.plotly_dash_view, name='plotly_dash_view'),
    # path("api/trigger-opc-import/", trigger_opc_import, name="trigger_opc_import"),
    path('dash-app/', include('django_plotly_dash.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
