import os
import json
import re
from pathlib import PurePath
from rest_framework import generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import Advisor, Country
from .serializers import AdvisorSerializer, CountrySerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

BASE_DOCUMENTS_FOLDER = os.path.join(settings.BASE_DIR, "ai_core", "documents")

# Allowed characters for path segments (alphanumeric, underscore and hyphen)
_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_segment(segment: str) -> str:
    """Return a cleaned path segment or raise ValueError."""
    if ".." in segment:
        raise ValueError("Invalid path segment")
    # PurePath will normalize any path separators
    if PurePath(segment).name != segment:
        raise ValueError("Invalid path segment")
    if not _SEGMENT_RE.fullmatch(segment):
        raise ValueError("Invalid path segment")
    return segment

class DocumentListAPIView(APIView):
    def get(self, request, niche, country):
        documents = []

        try:
            country_folder = os.path.join(BASE_DOCUMENTS_FOLDER, f"{niche}_docs", country.lower())

            if not os.path.exists(country_folder):
                return Response({"error": "Niche or country not found."}, status=status.HTTP_404_NOT_FOUND)

            for folder_name in os.listdir(country_folder):
                folder_path = os.path.join(country_folder, folder_name)
                metadata_path = os.path.join(folder_path, "metadata.json")

                if os.path.isdir(folder_path) and os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        documents.append(metadata)

            return Response(documents, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentDetailAPIView(APIView):
    def get(self, request, niche, country, form_number):
        try:
            try:
                niche = _validate_segment(niche).lower()
                country = _validate_segment(country).lower()
                form_number = _validate_segment(form_number).lower()
            except ValueError:
                return Response({"error": "Invalid path."}, status=status.HTTP_400_BAD_REQUEST)

            form_folder = os.path.join(BASE_DOCUMENTS_FOLDER, f"{niche}_docs", country, form_number)
            metadata_path = os.path.join(form_folder, "metadata.json")

            if not os.path.exists(metadata_path):
                return Response({"error": "Form not found."}, status=status.HTTP_404_NOT_FOUND)

            pdf_files = [f for f in os.listdir(form_folder) if f.endswith('.pdf')]

            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            if pdf_files:
                metadata["download_url"] = f"/media/documents/{niche}_docs/{country}/{form_number}/{pdf_files[0]}"
            else:
                metadata["download_url"] = None

            return Response(metadata, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class AdvisorListCreateView(generics.ListCreateAPIView):
    queryset = Advisor.objects.all()
    serializer_class = AdvisorSerializer
    permission_classes = [IsAuthenticated]  

class CountryListCreateView(generics.ListCreateAPIView):
    queryset = Country.objects.filter(is_active=True).prefetch_related("advisors")
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]
