# chats/views.py

import uuid, logging
from datetime import date
from django.utils.text import slugify
from django.utils import timezone
from rest_framework import status, permissions, viewsets, mixins, decorators, response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from django.http import StreamingHttpResponse
from .models import ChatSession, ChatMessage, Reaction, AccessRequest
from .serializers import ChatMessageSerializer, ChatSessionSerializer, MessageFeedbackSerializer
from ai_core.models import Advisor, Country
from membership.models import MonthlyUsage
from rest_framework.decorators import action
from ai_core.langgraph.workflows.workflow_free import get_free_immigration_graph
from ai_core.llm.llm_client_free import ask_openai


from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.http import FileResponse
from .utils.markdown_renderer import render_markdown_to_html
from django.template.loader import render_to_string
import pdfkit
from io import BytesIO
from docx import Document as DocxDocument
from bs4 import BeautifulSoup
from docx.shared import Pt, Inches


from django.contrib.staticfiles import finders


logo_path = finders.find("logo-dark.png")
font_path = finders.find("fonts/Cormorant-Regular.ttf")

logger = logging.getLogger(__name__)

graph = get_free_immigration_graph()




class ChatSessionCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        question = request.data.get("question", "").strip()
        if not question:
            logger.warning("No question provided")
            return Response(
                {"error": "Question required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) Country lookup by name (default to "USA")
        country_name = request.data.get("country", "").strip() or "USA"
        country = Country.objects.filter(name__iexact=country_name).first()
        if not country:
            logger.warning("Country '%s' not found, defaulting to USA", country_name)
            country = Country.objects.filter(name__iexact="USA").first()

        # 2) Advisor lookup by id OR name (default to "Immigration")
        advisor_id   = request.data.get("advisor")
        advisor = None
        if advisor_id:
            advisor = Advisor.objects.filter(pk=advisor_id).first()
        if not advisor:
            advisor_name = request.data.get("advisor_name", "").strip() or "Immigration"
            advisor = Advisor.objects.filter(name__iexact=advisor_name).first()
            if not advisor:
                logger.warning("Advisor '%s' not found, defaulting to Immigration", advisor_name)
                advisor = Advisor.objects.filter(name__iexact="Immigration").first()

        # 3) Generate a reasonably unique slug
        base = slugify(question)[:30]
        slug = f"{base}-{uuid.uuid4().hex[:85]}"

        # 4) Create the session
        session = ChatSession.objects.create(
            user=request.user,
            slug=slug,
            country=country,
            advisor=advisor,
            completed=False,
            memory_data=[]
        )
        logger.info("Created ChatSession slug=%s", slug)

        return Response(
            {
                "session_id": str(session.session_id),
                "slug":        slug
            },
            status=status.HTTP_201_CREATED
        )


from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
class ChatSessionStreamView(APIView):
    """Stream a markdown answer to the client in real-time."""
    permission_classes = [permissions.IsAuthenticated]

    # ───────────────────────── helpers ──────────────────────────
    def _get_this_month_usage(self, user):
        first_of_month = date.today().replace(day=1)
        usage, _ = MonthlyUsage.objects.get_or_create(
            user=user,
            period=first_of_month,
            defaults={"count": 0},
        )
        return usage

    def _record_usage(self, user):
        usage = self._get_this_month_usage(user)
        usage.increment()
        usage.save()

        logger.info("[Usage] %s ⇒ %s in %s", user.email, usage.count, usage.period)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"usage_{user.id}",
            {"type": "usage.update", "count": usage.count},
        )

    def _append_memory(self, session: ChatSession, role: str, content: str):
        data = session.memory_data or []
        data.append({"role": role, "content": content})
        session.memory_data = data
        session.save(update_fields=["memory_data", "updated"])
        logger.debug("[Memory] appended %s turn to session=%s", role, session.slug)

    # ───────────────────────── HEAD / POST ──────────────────────
    def head(self, request, slug, *args, **kwargs):
        get_object_or_404(ChatSession, slug=slug, user=request.user)
        return Response(status=status.HTTP_200_OK)

    def post(self, request, slug, *args, **kwargs):
        session = get_object_or_404(ChatSession, slug=slug, user=request.user)
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"error": "Question required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # store the user turn
        ChatMessage.objects.create(session=session, role="user", content=question)
        self._append_memory(session, "user", question)
        logger.info("[StreamView] Stored user message for %s: %s", slug, question)

        # ────────── streaming generator ──────────
        def stream_response():
            # tiny ping so the FE shows a spinner instantly
            yield "..."

            try:
                # call LangGraph synchronously
                result = graph.invoke({
                    "session_id": session.session_id,
                    "question":   question,
                    "niche":      getattr(session, "niche", "immigration"),
                    "country":    str(getattr(session, "country", "usa")).lower(),
                    "used_retrieval": False,
                })

                answer_md = (result.get("answer") or "").strip()
                docs      = result.get("docs") or []
                logger.info("[StreamView] docs=%s • answer_len=%s",
                            len(docs), len(answer_md))

                if docs and answer_md:
                    buffer: list[str] = []
                    CHUNK = 12                         # words/flush

                    words = answer_md.split(" ")
                    for i in range(0, len(words), CHUNK):
                        chunk = " ".join(words[i:i + CHUNK]) + " "
                        buffer.append(chunk)
                        yield chunk
                        yield ""                        # explicit flush

                    full = "".join(buffer)

                    ChatMessage.objects.create(
                        session=session,
                        role="assistant",
                        content=full,
                        html_content=render_markdown_to_html(full),
                    )
                    self._append_memory(session, "assistant", full)

                    session.completed = True
                    session.updated   = timezone.now()
                    session.save(update_fields=["completed", "updated"])

                    self._record_usage(request.user)

                else:  # fallback: no docs / empty answer
                    yield answer_md or "Sorry, no relevant information found."
                    ChatMessage.objects.create(
                        session=session,
                        role="assistant",
                        content=answer_md,
                        html_content=render_markdown_to_html(answer_md),
                    )
                    self._append_memory(session, "assistant", answer_md)

                    session.completed = True
                    session.updated   = timezone.now()
                    session.save(update_fields=["completed", "updated"])

            except Exception as exc:
                logger.exception("[StreamView] Error: %s", exc)
                err = ("I’m sorry — something went wrong while processing your "
                       "request. Please try again in a moment.")
                yield err
                ChatMessage.objects.create(
                    session=session,
                    role="assistant",
                    content=err,
                    html_content=render_markdown_to_html(err),
                )
                self._append_memory(session, "assistant", err)

        return StreamingHttpResponse(stream_response(),
                                     content_type="text/plain; charset=utf-8")

                                     
class ChatSessionRunView(ChatSessionStreamView):
    """Synchronous endpoint that runs generation without streaming"""

    def post(self, request, slug, *args, **kwargs):
        session = get_object_or_404(ChatSession, slug=slug, user=request.user)
        question = request.data.get("question", "").strip()
        if not question:
            return Response({"error": "Question required."}, status=status.HTTP_400_BAD_REQUEST)

        ChatMessage.objects.create(session=session, role="user", content=question)
        logger.info(f"[RunView] Stored user message for session={slug}: {question!r}")
        self._append_memory(session, "user", question)

        try:
            result = graph.invoke({
                "session_id": session.session_id,
                "question": question,
                "niche": getattr(session, "niche", "immigration"),
                "country": str(getattr(session, "country", "usa")).lower(),
                "used_retrieval": False,
            })
            answer_markdown = result.get("answer", "").strip()
            docs = result.get("docs") or []

            if docs and answer_markdown:
                full_response = ask_openai(answer_markdown, stream=False)
                self._record_usage(request.user)
            else:
                full_response = answer_markdown

            ChatMessage.objects.create(
                session=session,
                role="assistant",
                content=full_response,
                html_content=render_markdown_to_html(full_response),
            )
            self._append_memory(session, "assistant", full_response)

            session.completed = True
            session.updated = timezone.now()
            session.save(update_fields=["completed", "updated"])
            logger.info(f"[RunView] Completed answer ({len(full_response)} chars)")

        except Exception as e:
            logger.exception(f"[RunView] Error processing request: {e}")
            error_msg = "I apologize, but I encountered an error while processing your request. Please try again."
            ChatMessage.objects.create(
                session=session,
                role="assistant",
                content=error_msg,
                html_content=render_markdown_to_html(error_msg),
            )
            self._append_memory(session, "assistant", error_msg)

        return Response({"detail": "completed"}, status=status.HTTP_200_OK)

class ChatSessionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    list      GET   /api/sessions/
    retrieve  GET   /api/sessions/{slug}/
    destroy   DELETE/api/sessions/{slug}/
    """
    serializer_class = ChatSessionSerializer
    lookup_field = "slug"
    permission_classes = [permissions.IsAuthenticated]

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"messages/(?P<message_id>\d+)"
    )
    def delete_message(self, request, *args, **kwargs):
        # 1) get the Session instance via slug
        session = self.get_object()

        # 2) grab the message_id from the URL
        message_id = kwargs["message_id"]

        # 3) delete only if that ChatMessage belongs to this session
        msg = get_object_or_404(
            ChatMessage,
            pk=message_id,
            session_id=session.id   # <-- filter on the FK, not slug
        )
        msg.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        user = self.request.user
        logger.info("get_queryset called (action=%s) by user_id=%s", self.action, user.pk)

        if self.action == "list":
            qs = ChatSession.objects.filter(user=user).order_by("-updated")
            logger.debug("Returning %d sessions owned by user %s", qs.count(), user.pk)
            return qs

        # detail lookup: return all so get_object() can find private sessions
        qs = ChatSession.objects.all().order_by("-updated")
        logger.debug("Returning full queryset for detail lookup")
        return qs
    def retrieve(self, request, *args, **kwargs):
        session = self.get_object()

        # 1) Public‐link
        if session.share_option == "link":
            return super().retrieve(request, *args, **kwargs)

        # 2) Owner or allowed
        if session.user == request.user or session.allowed_users.filter(pk=request.user.pk).exists():
            return super().retrieve(request, *args, **kwargs)

        # 3) Private + unauthorized → just forbid, no auto‐email
        return Response(
            {"detail": "This session is private. Click Request Access to notify the owner."},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=True, methods=["post"], url_path="request_access")
    def request_access(self, request, slug=None):
        session = self.get_object()

        # If owner or public link, no need
        if session.user == request.user or session.share_option == "link":
            return Response({"detail": "Already accessible."}, status=status.HTTP_400_BAD_REQUEST)

        ar, created = AccessRequest.objects.get_or_create(
            session=session,
            requester=request.user
        )
        # Only on first creation do we send the e-mail
        if created and ar.status == "pending":
            approval_url = request.build_absolute_uri(
                reverse("chats:access_request_approve", args=[str(ar.token)])
            )
            ctx = {"owner": session.user, "requester": request.user,
                   "session": session, "approval_url": approval_url}
            text_body = render_to_string("emails/access_request.txt", ctx)
            html_body = render_to_string("emails/access_request.html", ctx)
            msg = EmailMultiAlternatives(
                f'[ExpertAIHub] Access request for "{session.title}"',
                text_body, "no-reply@expertaihub.com", [session.user.email]
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()

        return Response({"detail": "Access requested. An email has been sent to the owner."},
                        status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["patch"], url_path="update_metadata")
    def update_metadata(self, request, slug=None):
        session = self.get_object()
        serializer = ChatSessionSerializer(
            session, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["patch"], url_path="share_option")
    def update_share_option(self, request, slug=None):
        session = self.get_object()
        if session.user != request.user:
            return response.Response(status=status.HTTP_403_FORBIDDEN)

        opt = request.data.get("share_option")
        if opt not in ("private", "link"):
            return response.Response(
                {"detail": "share_option must be 'private' or 'link'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session.share_option = opt
        session.save(update_fields=["share_option", "updated"])
        return response.Response({"share_option": session.share_option})

    @decorators.action(
        detail=True,
        methods=["post"],
        url_path=r"approve_access/(?P<user_id>[^/.]+)"
    )
    def approve_access(self, request, slug=None, user_id=None):
        session = self.get_object()
        if session.user != request.user:
            return response.Response(status=status.HTTP_403_FORBIDDEN)

        try:
            ar = session.access_requests.get(
                requester_id=user_id,
                status="pending"
            )
        except AccessRequest.DoesNotExist:
            return response.Response(status=status.HTTP_404_NOT_FOUND)

        ar.status = "approved"
        ar.save(update_fields=["status"])
        session.allowed_users.add(ar.requester)
        return response.Response({"detail": "Access granted."})

    @decorators.action(detail=True, methods=["post"])
    def pin(self, request, slug=None):
        session = self.get_object()
        session.pinned = True
        session.save(update_fields=["pinned", "updated"])
        return response.Response({"pinned": True})

    @decorators.action(detail=True, methods=["post"])
    def unpin(self, request, slug=None):
        session = self.get_object()
        session.pinned = False
        session.save(update_fields=["pinned", "updated"])
        return response.Response({"pinned": False})

    @decorators.action(detail=True, methods=["post"])
    def archive(self, request, slug=None):
        session = self.get_object()
        session.archived = True
        session.save(update_fields=["archived", "updated"])
        return response.Response({"archived": True})

    @decorators.action(detail=True, methods=["post"])
    def unarchive(self, request, slug=None):
        session = self.get_object()
        session.archived = False
        session.save(update_fields=["archived", "updated"])
        return response.Response({"archived": False})

    @decorators.action(detail=True, methods=["get"])
    def messages(self, request, slug=None):
        session = self.get_object()
        msgs = ChatMessage.objects.filter(session=session).order_by("timestamp")
        serializer = ChatMessageSerializer(msgs, many=True, context={"request": request})
        return response.Response(serializer.data)
    
    @decorators.action(detail=True, methods=["get"], url_path="export/pdf")
    def export_pdf(self, request, slug=None):
        session = self.get_object()
        raw_msgs = session.messages.order_by("timestamp")

        # Annotate messages: give users a 'number' and 'content'; assistants keep html
        annotated = []
        qnum = 1
        for m in raw_msgs:
            if m.role == "user":
                annotated.append({
                    "role": "user",
                    "number": qnum,
                    "content": m.content,
                })
                qnum += 1
            else:
                annotated.append({
                    "role": "assistant",
                    "html_content": m.html_content or f"<p>{m.content}</p>",
                })

        html = render_to_string("chats/session_export.html", {
            "session": session,
            "messages": annotated,
        })

        config = pdfkit.configuration(
            wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        )
        options = {
            "enable-local-file-access": None,
            "load-error-handling": "ignore",
            "load-media-error-handling": "ignore",
        }
        pdf_bytes = pdfkit.from_string(html, False, configuration=config, options=options)

        bio = BytesIO(pdf_bytes)
        bio.seek(0)
        return FileResponse(
            bio,
            as_attachment=True,
            filename=f"{session.slug}.pdf",
            content_type="application/pdf"
        )
    

    @decorators.action(detail=True, methods=["get"], url_path="export/docx")
    def export_docx(self, request, slug=None):
        session = self.get_object()
        msgs = session.messages.order_by("timestamp")

        # 1) Create the Document
        doc = DocxDocument()

        # 2) Header: a two-cell table for logo + title
        table = doc.add_table(rows=1, cols=2)
        table.autofit = False
        cell_logo, cell_title = table.rows[0].cells

        # 2a) Insert logo
        cell_logo.width = Inches(0.8)
        logo_run = cell_logo.paragraphs[0].add_run()
        logo_run.add_picture(
            r"C:\Users\vamsh\OneDrive\Desktop\ExpertAiHub\Expertaihub\expertaihub_backend\static\logo-dark.png",
            width=Inches(0.6)
        )

        # 2b) Insert title
        cell_title.width = Inches(3.5)
        title_p = cell_title.paragraphs[0]
        title_run = title_p.add_run("Expertaihub")
        title_run.font.name = "Space Grotesk"
        title_run.font.size = Pt(16)
        title_run.font.bold = True

        # Blank line
        doc.add_paragraph()

        # 3) Walk through messages
        qnum = 1
        for m in msgs:
            if m.role == "user":
                # Numbered question
                p = doc.add_paragraph()
                num_run = p.add_run(f"{qnum}. ")
                num_run.font.name = "Cormorant"
                num_run.font.size = Pt(12)
                num_run.font.bold = True

                text_run = p.add_run(m.content)
                text_run.font.name = "Cormorant"
                text_run.font.size = Pt(12)

                qnum += 1

            else:
                # Assistant: parse HTML structure
                html = m.html_content or f"<p>{m.content}</p>"
                soup = BeautifulSoup(html, "html.parser")

                # Headings, paragraphs, lists, bold
                for elem in soup.recursiveChildGenerator():
                    if getattr(elem, "name", None) in ("h2", "h3"):
                        level = 1 if elem.name == "h2" else 2
                        doc.add_heading(elem.get_text(strip=True), level=level)

                    elif getattr(elem, "name", None) == "p":
                        p = doc.add_paragraph()
                        for child in elem.contents:
                            if getattr(child, "name", None) == "strong":
                                run = p.add_run(child.get_text())
                                run.bold = True
                                run.font.name = "Cormorant"
                                run.font.size = Pt(10)
                            else:
                                run = p.add_run(str(child))
                                run.font.name = "Cormorant"
                                run.font.size = Pt(10)

                    elif getattr(elem, "name", None) == "ul":
                        for li in elem.find_all("li"):
                            p = doc.add_paragraph(style="List Bullet")
                            run = p.add_run(li.get_text())
                            run.font.name = "Cormorant"
                            run.font.size = Pt(10)

                    elif getattr(elem, "name", None) == "ol":
                        for li in elem.find_all("li"):
                            p = doc.add_paragraph(style="List Number")
                            run = p.add_run(li.get_text())
                            run.font.name = "Cormorant"
                            run.font.size = Pt(10)

            # Spacer after each message
            doc.add_paragraph()

        # 4) Stream back as .docx
        bio = BytesIO()
        doc.save(bio)
        bio.seek(0)
        return FileResponse(
            bio,
            as_attachment=True,
            filename=f"{session.slug}.docx",
            content_type=(
                "application/vnd.openxmlformats-"
                "officedocument.wordprocessingml.document"
            )
        )
    

    @decorators.action(
        detail=True,
        methods=["get"],
        url_path=r"messages/(?P<message_id>\d+)/export/pdf"
    )
    def export_message_pdf(self, request, slug=None, message_id=None):
        session = self.get_object()
        # 1) Load the assistant message
        msg = get_object_or_404(
            ChatMessage,
            pk=message_id,
            session=session,
            role="assistant"
        )
        # 2) Find the immediately preceding user question
        question = (
            ChatMessage.objects
            .filter(session=session, role="user", timestamp__lt=msg.timestamp)
            .order_by("-timestamp")
            .first()
        )

        # 3) Build annotated list: question then answer
        annotated = []
        if question:
            annotated.append({
                "role": "user",
                "number": 1,
                "content": question.content,
            })
        annotated.append({
            "role": "assistant",
            "html_content": msg.html_content or f"<p>{msg.content}</p>",
        })

        # 4) Render with your existing template
        html = render_to_string("chats/session_export.html", {
            "session": session,
            "messages": annotated,
        })

        # 5) PDF generation (pdfkit config unchanged)
        config = pdfkit.configuration(
            wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        )
        options = {
            "enable-local-file-access": None,
            "load-error-handling": "ignore",
            "load-media-error-handling": "ignore",
        }
        pdf_bytes = pdfkit.from_string(html, False, configuration=config, options=options)

        bio = BytesIO(pdf_bytes)
        bio.seek(0)
        return FileResponse(
            bio,
            as_attachment=True,
            filename=f"{session.slug}-msg{message_id}.pdf",
            content_type="application/pdf"
        )


    @decorators.action(
        detail=True,
        methods=["get"],
        url_path=r"messages/(?P<message_id>\d+)/export/docx"
    )
    def export_message_docx(self, request, slug=None, message_id=None):
        session = self.get_object()
        msg = get_object_or_404(
            ChatMessage,
            pk=message_id,
            session=session,
            role="assistant"
        )
        question = (
            ChatMessage.objects
            .filter(session=session, role="user", timestamp__lt=msg.timestamp)
            .order_by("-timestamp")
            .first()
        )

        # 1) Create the Document and header (same as full-session)
        doc = DocxDocument()
        table = doc.add_table(rows=1, cols=2)
        table.autofit = False
        cell_logo, cell_title = table.rows[0].cells
        cell_logo.width = Inches(0.8)
        logo_run = cell_logo.paragraphs[0].add_run()
        logo_run.add_picture(r"C:\Users\vamsh\OneDrive\Desktop\ExpertAiHub\Expertaihub\expertaihub_backend\static\logo-dark.png", width=Inches(0.6))
        cell_title.width = Inches(3.5)
        run = cell_title.paragraphs[0].add_run("Expertaihub")
        run.font.name = "Space Grotesk"
        run.font.size = Pt(16)
        run.bold = True
        doc.add_paragraph()

        # 2) Insert the question (numbered)
        if question:
            p = doc.add_paragraph()
            num = p.add_run("1. ")
            num.font.name = "Cormorant"
            num.font.size = Pt(12)
            num.bold = True
            txt = p.add_run(question.content)
            txt.font.name = "Cormorant"
            txt.font.size = Pt(12)
            doc.add_paragraph()

        # 3) Parse and insert the assistant's HTML content
        html = msg.html_content or f"<p>{msg.content}</p>"
        soup = BeautifulSoup(html, "html.parser")
        for elem in soup.recursiveChildGenerator():
            tag = getattr(elem, "name", None)
            if tag in ("h2", "h3"):
                lvl = 1 if tag == "h2" else 2
                doc.add_heading(elem.get_text(strip=True), level=lvl)
            elif tag == "p":
                p = doc.add_paragraph()
                for child in elem.contents:
                    if getattr(child, "name", None) == "strong":
                        r = p.add_run(child.get_text())
                        r.bold = True
                        r.font.name = "Cormorant"
                        r.font.size = Pt(10)
                    else:
                        r = p.add_run(str(child))
                        r.font.name = "Cormorant"
                        r.font.size = Pt(10)
            elif tag == "ul":
                for li in elem.find_all("li"):
                    p = doc.add_paragraph(style="List Bullet")
                    r = p.add_run(li.get_text())
                    r.font.name = "Cormorant"
                    r.font.size = Pt(10)
            elif tag == "ol":
                for li in elem.find_all("li"):
                    p = doc.add_paragraph(style="List Number")
                    r = p.add_run(li.get_text())
                    r.font.name = "Cormorant"
                    r.font.size = Pt(10)
        doc.add_paragraph()

        # 4) Stream back
        bio = BytesIO()
        doc.save(bio)
        bio.seek(0)
        return FileResponse(
            bio,
            as_attachment=True,
            filename=f"{session.slug}-msg{message_id}.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseForbidden
from django.conf import settings
from .models import AccessRequest

def access_request_approve(request, token):
    """
    URL: GET /api/access-request/approve/<uuid:token>/
    - If not logged in → bounce to frontend /signin
    - If logged in but not owner → 403
    - If owner → approve + redirect to frontend chat
    """
    ar = get_object_or_404(AccessRequest, token=token, status="pending")
    session = ar.session

    # 1) Not logged in? → frontend signin
    if not request.user.is_authenticated:
        return redirect("http://localhost:3000/signin")

    # 2) Only the session owner can approve
    if session.user != request.user:
        return HttpResponseForbidden("Only the session owner can approve.")

    # 3) Mark the request approved
    ar.status = "approved"
    ar.save(update_fields=["status"])
    session.allowed_users.add(ar.requester)

    # 4) Back to your Next.js chat page with approved flag
    return redirect(f"http://localhost:3000/library/{session.slug}/?approved=true")

class ReactionUpsertView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug, message_id, *args, **kwargs):
        msg = get_object_or_404(
            ChatMessage,
            pk=message_id,
            session__slug=slug,
            session__user=request.user
        )

        # 2) Validate input
        reaction = request.data.get("reaction")
        if reaction not in (Reaction.LIKE, Reaction.DISLIKE):
            return Response({"error":"Invalid reaction"}, status=status.HTTP_400_BAD_REQUEST)

        # 3) Create or update
        obj, created = Reaction.objects.update_or_create(
            user=request.user,
            message=msg,
            defaults={"reaction": reaction}
        )

        # 4) Return updated counts & my_reaction
        likes    = msg.reactions.filter(reaction=Reaction.LIKE).count()
        dislikes = msg.reactions.filter(reaction=Reaction.DISLIKE).count()
        return Response({
            "my_reaction": obj.reaction,
            "likes_count": likes,
            "dislikes_count": dislikes
        })
    

class MessageFeedbackCreateView(CreateAPIView):
    """
    POST /api/sessions/{slug}/messages/{msg_id}/feedback/
    """
    serializer_class = MessageFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        slug   = self.kwargs["slug"]
        msg_id = self.kwargs["msg_id"]
        msg = get_object_or_404(ChatMessage, id=msg_id, session__slug=slug)
        serializer.save(user=self.request.user, message=msg)