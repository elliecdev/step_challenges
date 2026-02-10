from django.contrib import admin
from .models import StepChallenge, Team, Participant, StepEntry
from .forms import TeamAdminForm

@admin.register(StepChallenge)
class StepChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "start_date",
        "end_date",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active",)
    search_fields = ("name",)

    list_editable = ("is_active",)

    ordering = ("-start_date",)

    fieldsets = (
        (None, {
            "fields": ("name", "is_active")
        }),
        ("Challenge Dates", {
            "fields": ("start_date", "end_date")
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("created_at",)


class TeamInline(admin.TabularInline):
    model = Team
    form = TeamAdminForm
    extra = 1


StepChallengeAdmin.inlines = [TeamInline]

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "team",
        "challenge",
        "joined_at",
    )

    list_filter = (
        "team__challenge",
        "team",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
    )

    ordering = ("team", "user")

    readonly_fields = ("joined_at",)

    def challenge(self, obj):
        return obj.team.challenge

@admin.register(StepEntry)
class StepEntryAdmin(admin.ModelAdmin):
    list_display = (
        "participant",
        "challenge",
        "date",
        "daily_steps",
        "created_at",
    )

    list_filter = (
        "challenge",
        "participant__team",
    )

    search_fields = (
        "participant__user__username",
        "participant__user__first_name",
        "participant__user__last_name",
    )

    ordering = ("-date",)

    date_hierarchy = "date"

    readonly_fields = ("created_at",)

    def get_readonly_fields(self, request, obj=None):
        """
        Optional safety: prevent edits if challenge is closed,
        but still allow superusers to fix mistakes.
        """
        if obj and not obj.challenge.is_active and not request.user.is_superuser:
            return self.readonly_fields + ("participant", "challenge", "date", "daily_steps")
        return self.readonly_fields

