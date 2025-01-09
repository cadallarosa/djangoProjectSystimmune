from django.urls import path
from .views import home_page

urlpatterns = [
    path('', home_page, name='hometest'),
    # add your other paths here
]
