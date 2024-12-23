from django.urls import path, include
from . import views
from .views import database_sample_view, handle_submit
from .views import handle_submit


urlpatterns = [
    # path('', views.view, name='analytics'),  # updated path to handle both forms
    # path('new/', views.new_page, name='new_page'),
    # path('plot/', plotly_dash_view, name='plot'),
    # path('plot_data/', database_sample_view, name='plot_data_view'),
    path('', views.reports_page, name='analytics'),
    path('submit-report/', handle_submit, name='submit_report'),

]
