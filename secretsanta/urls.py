from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('', views.GameListView.as_view(), name='game_list'),
    path('game/add/', views.GameCreateView.as_view(), name='game_add'),
    path('game/<int:pk>/', views.GameDetailView.as_view(), name='game_detail'),
    path('game/<int:pk>/edit/', views.GameUpdateView.as_view(), name='game_edit'),
    path('game/<int:pk>/draw/', views.draw_game, name='game_draw'),
    path('game/<int:pk>/reset/', views.reset_draw, name='game_reset'),
    path('game/<int:pk>/send-emails/', views.send_emails, name='game_send_emails'),
    path('game/<int:pk>/email-errors/', views.EmailErrorListView.as_view(), name='email_errors'),
    path('player/<int:pk>/update-email/', views.PlayerEmailUpdateView.as_view(), name='player_update_email'),
    path('email-log/<int:pk>/retry/', views.retry_email_view, name='email_retry'),
    
    path('game/<int:game_pk>/player/add/', views.PlayerCreateView.as_view(), name='player_add'),
    path('game/<int:game_pk>/player/import/', views.player_import, name='player_import'),
    path('player/<int:pk>/edit/', views.PlayerUpdateView.as_view(), name='player_edit'),
    path('player/<int:pk>/delete/', views.PlayerDeleteView.as_view(), name='player_delete'),
    
    path('game/<int:game_pk>/forbidden/add/', views.ForbiddenPairCreateView.as_view(), name='forbidden_add'),
    path('forbidden/<int:pk>/delete/', views.ForbiddenPairDeleteView.as_view(), name='forbidden_delete'),
]
