from django.urls import path
from . import views

urlpatterns = [
    path('plotly_dash/', views.plotly_dash_view, name='plotly_dash_view'),
]
