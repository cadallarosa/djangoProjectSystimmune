from django.urls import path
from .views import plot_view
from . import views
# from .views import database_sample_view, view

urlpatterns = [
    # path('', views.view, name='analytics'),  # updated path to handle both forms
    # path('new/', views.new_page, name='new_page'),
    # path('plot/', plot_view, name='plot_view'),
    # path('plot_data/', database_sample_view, name='plot_data_view'),
    path('', views.reports_page, name='analytics'),
]
