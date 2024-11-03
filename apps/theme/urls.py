from django.urls import path
from apps.theme import views

urlpatterns = [
    path('api/theme/', views.get_user_theme, name='get_user_theme'),
    path('api/theme/<int:theme_id>/', views.set_user_theme, name='set_user_theme'),
]
