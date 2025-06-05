# membership/views.py
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from .models import Membership, MonthlyUsage
from rest_framework.response import Response
from .serializers import MembershipSerializer
from rest_framework.permissions import IsAuthenticated
from datetime import date


class MembershipDetailView(APIView):
    """
    GET  /api/membership/      → returns the current user's membership
    PATCH /api/membership/      → allows user to upgrade/downgrade plan
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = request.user.membership
        serializer = MembershipSerializer(membership)
        return Response(serializer.data)
    

    def patch(self, request):
        membership = request.user.membership
        serializer = MembershipSerializer(
            membership, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)


        end_date = serializer.validated_data.get("end_date")
        if end_date and end_date < timezone.now():
            serializer.validated_data["is_active"] = False

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)



class MembershipListAPIView(APIView):
    """
    [Admin only] List all user memberships or create new ones.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Membership.objects.select_related("user").all()
        serializer = MembershipSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Admin can create a membership for any user by passing a “user” field:
        serializer = MembershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    



class MonthlyUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        first_of_month = date.today().replace(day=1)
        usage, _ = MonthlyUsage.objects.get_or_create(
            user=request.user,
            period=first_of_month,
            defaults={'count': 0}
        )
        return Response({'count': usage.count})


