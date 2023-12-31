from django.urls import path

from . import views

urlpatterns = [
    path('api/get_services', views.get_services),
    path('api/set_user_info', views.set_user_info),
    path('api/get_user_info', views.get_user_info),
    path('api/do_checkin_gps', views.do_checkin_gps),
    path('api/checkin_activity', views.checkin_activity, name="checkin_activity"),
    path('api/checkin_activity_admin', views.checkin_activity_admin, name="checkin_activity_admin"),
    path('api/checkin_admin_feedback', views.checkin_feedback_admin, name="checkin_admin_feedback"),
    path('api/add_med', views.add_med),
    path('api/list_meds', views.list_meds),
    path('api/list_questions', views.list_questions),
    path('api/assign_tag', views.assign_tag),
    path('api/get_user_tags', views.get_tags, name="get_tags"),
    path('api/del_med/<int:med_id>', views.del_med),
    path('api/login-phone-number', views.confirm_phone_number,
        name='confirm_phone_number'),
    path('api/login-verify-2fa', views.verify_2fa,
        name='verify_2fa'),

    path('test-page/login', views.test_login,
        name='test_login'),
    path('api/member_session_start', views.member_session_start, name="member_session_start"),
    path('api/member_session_stop', views.member_session_stop, name="member_session_stop"),
    path('api/member_session_distance', views.member_session_distance, name="member_session_distance"),
    path('api/member_session_livedata', views.member_session_livedata, name="member_session_livedata"),
    path('api/places', views.Position.as_view(), name="places-home"),
    path('api/places/create/', views.createPosition, name="place-create"),
    path('api/place-update/<str:pk>/', views.updatePosition, name="task-update"),
    path('api/place-delete/<str:pk>/', views.deletePosition, name="task-delete"),
    # path('api/places/create', views.CreateLocationView.as_view(), name="crete_location"),
    # path('api/places/update/<pk>/', views.UpdateLocationView.as_view(), name="update_location"),

]
