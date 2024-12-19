from django.urls import path
from .views import home_page

urlpatterns = [
    path('', home_page, name='home'),
    # add your other paths here
]
