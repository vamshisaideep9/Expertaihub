from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from membership.models import Membership, MonthlyUsage
from ai_core.models import Advisor, Country
from chats.models import ChatLibrary, ChatMessage, ChatSession

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
    list_filter = ('period', 'count')
    search_fields = ('user__email',)


#ai_core
@admin.register(Advisor)
class AdvisorAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description', 'is_active')

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')


#Chats
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'advisor', 'country', 'created_at', 'updated_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'content', 'timestamp')

@admin.register(ChatLibrary)
class ChatLibraryAdmin(admin.ModelAdmin):
    list_display = ('user', 'prompt', 'slug', 'advisor', 'country', 'created_at')



