from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

# from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path('advisors',views.show_home, name='advisors'),
    path('get_favorites',views.favorites, name='get_favorites'),

    path('signup',views.signup, name='signup'),
    # path('signup_submit',views.signup_submit, name='signup_submit'),
    
    path('signin',views.signin, name='signin'),
    # path('signin_submit',views.signin_submit, name='signin_submit'),

    # forget password start
    path('forget-password',views.forget_password, name='forget-password'),
    path('forget-password-submit',views.forget_password, name='send_email_view'),
    path('change-password',views.change_password, name='change-password'),

    



    # path('chatlayout/<str:chat_id>/',views.show_chat_screen, name='chatlayout'),
    path('chat/<str:advisor_id>/',views.show_chat_screen, name='chat'),
    path('get',views.get_openai_response, name='get'),
    path('get-card-id',views.get_Card_ID, name='get-card-id'),
    path('get-selected-category',views.get_selected_category, name='get-selected-category'),
    path('logout', views.logout, name='logout'),
    # path('logout', views.logout_view, name='logout'),
    path('aboutus', views.about, name='about'),
    path('get-info', views.get_info, name='get_info'),
    path('create-professional-panel', views.prof_panel, name='create-professional-panel'),
    path('create-custom-advisor', views.custom_advisor, name='create-custom-advisor'),
    # path('create-professional-panel-submit', views.prof_panel_submit, name='create-professional-panel-submit'),
    path('prof_simple_panel_submit', views.prof_simple_panel_submit, name='prof_simple_panel_submit'),

    path('custom_advisor_submit', views.custom_advisor_submit, name='custom_advisor_submit'),
    path('update_custom_advisor', views.update_custom_advisor, name='update_custom_advisor'),
    path('delete_custom_advisor', views.delete_custom_advisor, name='delete_custom_advisor'),

    path('chats', views.chats, name='chats'),
    path('chat-open/<str:panel_id>/', views.chat_open),
    path('get-panel-chat-response',views.get_openai_response_group, name='get-panel-chat-response'),


    path('group_chat/', views.group_chat, name='group_chat'),
    
    path('', views.load_home_search, name='home'),

    path('ask_question/', views.ask_question, name='ask_question'),
    path('card_delete_chat/', views.card_delete_chat, name='card_delete_chat'),
    path('card_delete_panelchat/', views.card_delete_panelchat, name='card_delete_panelchat'),
    path('favorite/', views.favorite, name='favorite'),
    
    
    path('start_ai_chat/',views.start_ai_chat, name='start_ai_chat'),
    
    path('ask_advisor/',views.ask_advisor, name='ask_advisor'),
    
    path('profile/',views.profile, name='profile'),
    
    path('update-profile/',views.update_profile, name='update-profile'),

    path('changepassword/', views.changepassword, name='changepassword'),
    path('create-profession-advisor-panel', views.create_profession_advisor_panel, name='create-profession-advisor-panel'),

    path('clear-cache/', views.clear_cache, name='clear_cache'),

    path('delete-advisor-panel/', views.delete_advisor_from_panel, name='delete_advisor_from_panel'),

    # api start here
    path('api/all-advisors/', views.all_advisors_api, name='all_advisors_api'),

    path('add-advisor-panel/', views.add_advisor_panel, name='add_advisor_panel'),
    path('documentation/', views.documentation, name='documentation'),





    
    
    
    

    



    
    
    

    
    
    # path('get',views.get_openai_response, name='get'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)