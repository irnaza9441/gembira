from django.urls import path
from . import views
from stores import views as stores_views
urlpatterns = [
    path('', views.index, name='home.index'),
    path('about', views.about, name='home.about'),
    path('cafe', stores_views.cafe, name='home.cafe'),

]