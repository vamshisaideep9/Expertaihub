from django.urls import path
from .views import RegisterView, LoginView, VerifyEmail, RequestPasswordResetView, PasswordResetConfirmView, ResendVerificationEmail, user_me_view

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('verify-email/<uidb64>/<token>/', VerifyEmail.as_view(), name="verify-email"),
    path('resend-verification/', ResendVerificationEmail.as_view(), name='resend-verification'),
    # Add password reset routes later
]


urlpatterns += [
    path('request-password-reset/', RequestPasswordResetView.as_view()),
    path('reset-password-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view()),
]


urlpatterns += [
    path('me/', user_me_view, name='user-me')
]
