from . import views
from django.urls import path

urlpatterns = [
    path('quadtree/clear', views.clear, name ='index'),
    path('quadtree/sync', views.sync, name ='index1'),
    path('quadtree/create_random_user', views.create_random_user, name='index2'),
    path('quadtree/create_random_user/<int:count>', views.create_random_user, name='index3'),
    path('quadtree/view', views.visual, name='index4'),
    path('quadtree/get_nearby_users', views.get_nearby_users, name='index5'),
]
