# region imports
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.crypto import get_random_string
from rest_framework import status, generics, permissions, filters
from .models import User, CompanyProfile, EmployeeProfile, VideoRecording
from .serializers import (
    UserSerializer,
    CompanyProfileSerializer,
    EmployeeProfileSerializer,
    VideoRecordingSerializer
)
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from .models import Membership
from .serializers import MembershipSerializer
from rest_framework_simplejwt.tokens import RefreshToken
import re
import requests
from rest_framework.permissions import AllowAny
# endregion

BUNNY_STORAGE_ZONE = 'CaptureApp'
BUNNY_API_KEY = '1ade0733-3a01-4e3e-a8918b231011-2270-4549'
BUNNY_STORAGE_ENDPOINT = f'https://storage.bunnycdn.com/{BUNNY_STORAGE_ZONE}'

class VideoRecordingView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Retrieve all recordings for the logged-in user."""
        recordings = VideoRecording.objects.filter(user=request.user)
        serializer = VideoRecordingSerializer(recordings, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Upload a video recording."""
        title = request.data.get('title')
        video_file = request.FILES.get('video')

        if not title or not video_file:
            return Response({"error": "Title and video file are required."}, status=status.HTTP_400_BAD_REQUEST)

        file_name = video_file.name
        headers = {'AccessKey': BUNNY_API_KEY}
        upload_url = f"{BUNNY_STORAGE_ENDPOINT}/{file_name}"

        # Upload to Bunny.net
        response = requests.put(upload_url, headers=headers, files={'file': (file_name, video_file)})

        if response.status_code == 201:
            video_url = f"https://{BUNNY_STORAGE_ZONE}.b-cdn.net/{file_name}"

            # Save video metadata in the database
            recording = VideoRecording.objects.create(
                user=request.user,
                title=title,
                file_name=file_name,
                video_url=video_url
            )
            serializer = VideoRecordingSerializer(recording)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({"error": "Failed to upload to Bunny.net"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# region add employee
class SignUpWithRandomPasswordView(APIView):
    def post(self, request):
        # Only accept username and email from the request
        data = {
            "username": request.data.get("username"),
            "email": request.data.get("email"),
        }
        if not data["username"] or not data["email"]:
            return Response(
                {"error": "Username and email are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        random_password = get_random_string(length=12)
        print(f"Generated Random Password: {random_password}")

        data["password"] = random_password

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()

            self.send_confirmation_email(request, user, random_password)
            return Response(
                {
                    "message": "User created successfully. Please check your email for confirmation."
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_confirmation_email(self, request, user, password):
        current_site = get_current_site(request).domain
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = custom_token_generator.make_token(user)

        confirmation_link = f"http://{current_site}{reverse('verify-email', kwargs={'uidb64': uid, 'token': token})}"
        subject = "Confirm your email address"
        message = (
            f"Hi {user.username},\n\n"
            f"Your account has been created successfully. Your temporary password is:\n\n"
            f"{password}\n\n"
            f"Please confirm your email address by clicking the link below:\n\n"
            f"{confirmation_link}\n\n"
            f"Thank you!"
        )

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )


# endregion

class MembershipCreateView(generics.CreateAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [permissions.AllowAny]

class MembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [permissions.AllowAny]
# region authentication
class SignUpView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            self.send_confirmation_email(request, user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_confirmation_email(self, request, user):
        current_site = get_current_site(request).domain
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = custom_token_generator.make_token(user)

        confirmation_link = f"http://{current_site}{reverse('verify-email', kwargs={'uidb64': uid, 'token': token})}"
        subject = "Confirm your email address"
        message = f"Hi {user.username},\n\nPlease confirm your email address by clicking the link below:\n\n{confirmation_link}\n\nThank you!"

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

class SignInView(APIView):
    def post(self, request):
        # Get credentials from the request
        identifier = request.data.get("username")  # Accept either username or email
        password = request.data.get("password")

        # Validate input
        if not identifier or not password:
            return Response(
                {"error": "Both identifier and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the identifier is an email
        is_email = re.match(r"[^@]+@[^@]+\.[^@]+", identifier)

        # Query the user by email or username
        try:
            if is_email:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check if the provided password matches the hashed password
        if check_password(password, user.password):
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Add custom claims to the token
            access_token = refresh.access_token
            access_token["role"] = user.role  # Assuming the `User` model has a `role` field

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(access_token),
                    "role": user.role,  # Explicitly include role in the response
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )
# endregion


# region users and profiles
class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email"]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class CompanyProfileViewSet(generics.ListCreateAPIView):
    queryset = CompanyProfile.objects.all()
    serializer_class = CompanyProfileSerializer


class EmployeeProfileViewSet(generics.ListCreateAPIView):
    queryset = EmployeeProfile.objects.all()
    serializer_class = EmployeeProfileSerializer


# endregion


# region helper methods
class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Exclude the `last_login` field
        return f"{user.pk}{user.is_active}{timestamp}"


custom_token_generator = CustomTokenGenerator()


class EmailVerificationView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and custom_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            return Response(
                {"message": "Email verified successfully."}, status=status.HTTP_200_OK
            )
        return Response(
            {"error": "Invalid token or user ID."}, status=status.HTTP_400_BAD_REQUEST
        )


# endregion
