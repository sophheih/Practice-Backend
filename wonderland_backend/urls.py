from django.urls import include, path

from wonderland_backend.views import get_system_status

urlpatterns = [
    path('', get_system_status),
    path('member/', include('member_api.urls')),
    path('service/', include('service_api.urls')),
    path('reservation/', include('reservation_api.urls')),
    path('order/', include('order_api.urls')),
    path('timetable/', include('timetable_api.urls')),
]
