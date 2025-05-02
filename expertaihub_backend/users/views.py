from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from users.tokens import custom_password_reset_token
from membership.models import Membership
from datetime import timedelta
from django.utils import timezone
from .models import CustomUser
from .serializers import RegisterSerializer

User = get_user_model()

class RegisterView(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            existing_user = CustomUser.objects.get(email=email)

            if not existing_user.is_active:
                uid = urlsafe_base64_encode(force_bytes(existing_user.pk))
                token = default_token_generator.make_token(existing_user)
                link = f"http://localhost:3000/verify-email/{uid}/{token}"

                html_content = render_to_string("emails/email_verification.html", {
                    "verification_link": link
                })

                email_obj = EmailMultiAlternatives(
                    subject="Resend Email Verification",
                    body="Verify your account",
                    from_email="no-reply@expertaihub.com",
                    to=[email]
                )
                email_obj.attach_alternative(html_content, "text/html")
                email_obj.send()

                return Response(
                    {"message": "Account already exists but not active. Verification email re-sent."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response({"email": ["A user with this email already exists."]}, status=400)

        except CustomUser.DoesNotExist:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                link = f"http://localhost:3000/verify-email/{uid}/{token}"

                html_content = render_to_string("emails/email_verification.html", {
                    "verification_link": link
                })

                email_obj = EmailMultiAlternatives(
                    subject="Verify your email",
                    body="Click the link to verify your email.",
                    from_email="no-reply@expertaihub.com",
                    to=[user.email]
                )
                email_obj.attach_alternative(html_content, "text/html")
                email_obj.send()

                return Response(
                    {"message": "Check your email to verify your account."},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmail(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)

            # Check token validity
            if not default_token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired verification link."}, status=400)

            # Check if user is already active
            if user.is_active:
                return Response({"message": "Email already verified."}, status=200)

            # Check created_at time (assuming your CustomUser model has created_at field)
            if hasattr(user, 'created_at'):
                expiration_time = user.created_at + timedelta(minutes=10)
                if timezone.now() > expiration_time:
                    user.delete()
                    return Response({"error": "Verification link expired. Please register again."}, status=400)

            # Activate user
            user.is_active = True
            user.save()

            return Response({"message": "Email verified successfully."}, status=200)

        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid user."}, status=400)
        except Exception as e:
            return Response({"error": "Something went wrong."}, status=400)


class ResendVerificationEmail(APIView):
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({"error": "Email is required."}, status=400)

        try:
            user = CustomUser.objects.get(email=email)

            if user.is_active:
                return Response({"message": "Account is already active."}, status=200)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"http://localhost:3000/verify-email/{uid}/{token}"

            html_content = render_to_string("emails/email_verification.html", {
                "verification_link": link
            })

            email_obj = EmailMultiAlternatives(
                subject="Resend Email Verification",
                body="Please verify your email",
                from_email="no-reply@expertaihub.com",
                to=[email]
            )
            email_obj.attach_alternative(html_content, "text/html")
            email_obj.send()

            return Response({"message": "Verification email re-sent."}, status=200)

        except CustomUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=404)
        except Exception:
            return Response({"error": "Something went wrong while resending email."}, status=500)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email and not password:
            return Response({'error': 'Email and Password are required.'}, status=400)
        elif not email:
            return Response({'error': 'Please enter your email.'}, status=400)
        elif not password:
            return Response({'error': 'Please enter your password.'}, status=400)

        user = authenticate(email=email, password=password)  # ✅ YOUR ORIGINAL LINE (untouched)

        if user:
            refresh = RefreshToken.for_user(user)
            response = Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
            response.set_cookie('access_token', str(refresh.access_token), httponly=True)
            response.set_cookie('refresh_token', str(refresh), httponly=True)
            return response

        else:
            # Now smart validation without touching authenticate()
            from users.models import CustomUser
            try:
                user_obj = CustomUser.objects.get(email=email)
                # Email exists but wrong password
                return Response({'error': 'Incorrect password. Please check your password.'}, status=401)
            except CustomUser.DoesNotExist:
                # Email does not exist
                return Response({'error': 'User does not exist. Please signup.'}, status=404)

        # Final fallback (should not happen usually)
        return Response({'error': 'Invalid credentials.'}, status=401)

class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required."}, status=400)

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"http://localhost:3000/reset-password-confirm/{uid}/{token}/"

            html_content = render_to_string("emails/password_reset.html", {
                "reset_link": link
            })

            email_obj = EmailMultiAlternatives(
                subject="Reset Your Password",
                body="Click the link to reset your password.",
                from_email="no-reply@expertaihub.com",
                to=[email]
            )
            email_obj.attach_alternative(html_content, "text/html")
            email_obj.send()

            return Response({"message": "Password reset link sent."}, status=200)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)



class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

            if not custom_password_reset_token.check_token(user, token):
                return Response({"error": "Invalid or expired token."}, status=400)

            password = request.data.get('password')
            confirm_password = request.data.get('confirm_password')

            if not password or not confirm_password:
                return Response({"error": "Both password fields are required."}, status=400)

            if password != confirm_password:
                return Response({"error": "Passwords do not match."}, status=400)

            if len(password) < 8:
                return Response({"error": "Password must be at least 8 characters long."}, status=400)

            if user.check_password(password):
                return Response({"error": "You cannot use your previous password. Please choose a new one."}, status=400)

            try:
                validate_password(password, user=user)
            except ValidationError as ve:
                return Response({"error": ve.messages[0]}, status=400)

            user.set_password(password)
            user.save()

            return Response({"message": "Password reset successful."}, status=200)

        except User.DoesNotExist:
            return Response({"error": "Invalid user."}, status=404)
        except Exception:
            return Response({"error": "Invalid link or user."}, status=400)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_me_view(request):
    user = request.user

    # Try to pull the OneToOne Membership; fall back to free defaults if missing/expired
    try:
        membership = user.membership
        # If it has an end_date in the past or is_active==False, treat as free
        if not membership.is_active or (membership.end_date and membership.end_date < timezone.now()):
            raise Membership.DoesNotExist
        membership_data = {
            "membership_type": membership.membership_type,
            "start_date":      membership.start_date,
            "end_date":        membership.end_date,
            "is_active":       membership.is_active,
        }
    except Membership.DoesNotExist:
        membership_data = {
            "membership_type": "free",
            "start_date":      None,
            "end_date":        None,
            "is_active":       True,
        }

    return Response({
        "id":            user.id,
        "full_name":     user.full_name,
        "email":         user.email,
        "membership":    membership_data,
    })