from appointments.views import AppointmentViewSet, AvailableSlotsView
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import (
    ActivateAccountView,
    ChangePasswordView,
    CheckStudentView,
    LogoutView,
    MyTokenObtainPairView,
    ProfileView,
)

router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth
    path("api/token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/login/", MyTokenObtainPairView.as_view(), name="auth_login"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth_logout"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "api/auth/change-password/",
        ChangePasswordView.as_view(),
        name="change_password",
    ),
    path("api/auth/check-student/", CheckStudentView.as_view(), name="check_student"),
    path("api/auth/activate/", ActivateAccountView.as_view(), name="activate"),
    # Slots Availability
    path("api/slots/", AvailableSlotsView.as_view(), name="slots_availability"),
    # Appointments
    path("api/", include(router.urls)),
    # User Profile
    path("api/auth/profile/", ProfileView.as_view(), name="profile"),
]
