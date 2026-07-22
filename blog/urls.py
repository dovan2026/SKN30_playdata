from django.urls import path
from . import views

# Create your views here.
urlpatterns = [
    path('api/posts/', views.post_api, name='post_api'),
    path('', views.post_list, name='post_list'),
    path('create/', views.post_create, name='post_create'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    path('<int:pk>/update/', views.post_update, name='post_update'),
    path('<int:pk>/delete/', views.post_delete, name='post_delete')
]