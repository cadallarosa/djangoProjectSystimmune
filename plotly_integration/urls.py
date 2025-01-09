from django.urls import path
from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    # path('plotly_dash/', views.plotly_dash_view, name='plotly_dash_view'),
    path('time-series/', views.plot_time_series, name='plot_time_series'),
    path('dash/', views.dashboard, name='dashboard'),
    path('dash-app/', include('django_plotly_dash.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
