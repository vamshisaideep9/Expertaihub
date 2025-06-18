from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from membership.models import Membership, MonthlyUsage
from ai_core.models import Advisor, Country, DocumentChunk, RawDocument
from chats.models import ChatMessage, ChatSession, Reaction, AccessRequest, MessageFeedback
from suggestions.models import FAQQuestion, ChatSuggestion


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'full_name', 'is_active', 'is_staff']
    ordering = ['email']
    search_fields = ['email', 'full_name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)

#Memberships
@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'membership_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('membership_type', 'is_active')
    search_fields = ('user__email',)

@admin.register(MonthlyUsage)
class MonthlyUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'period', 'count')




#ai_core
@admin.register(Advisor)
class AdvisorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description', 'is_active')

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name','is_active')


#Chats
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'advisor', 'country', 'title', 'pinned', 'notes', 'archived', 'created', 'updated', 'completed')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'content', 'timestamp')


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'reaction')



@admin.register(MessageFeedback)
class MessageFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'reasons', 'additional_comments', 'created_at')


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "requester", "status", "created")
    list_filter  = ("status", "created")
    search_fields = ("session__title", "requester__email")


@admin.register(ChatSuggestion)
class ChatSuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "text", "rank", "clicked", "created")






class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ("chunk_index", "text")  # show whatever fields you care about
    readonly_fields = ("chunk_index",)
    show_change_link = True
    ordering = ("chunk_index",)


@admin.register(RawDocument)
class RawDocumentAdmin(admin.ModelAdmin):
    list_display = ("filename", "category", "advisor", "country", "created_at")
    search_fields = ("filename", "category", "source_path")
    list_filter = ("category",)
    readonly_fields = ("created_at",)
    inlines = (DocumentChunkInline,)
    ordering = ("-created_at",)


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("__str__", "raw_document", "chunk_index")
    search_fields = ("text", "metadata")
    list_filter = ("raw_document__category",)
    readonly_fields = ("created_at",)
    ordering = ("raw_document", "chunk_index")