from django.contrib import admin
from .models import (
    Profile,
    Employee,
    SalaryAdvanceRequest,
    LoanRequest,
    ChatMessage,
    SupportChatMessage,
)

# ================================================================
# Employee & Profile Models
# ================================================================
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "full_name", "department", "job_title", "role", "date_joined")
    search_fields = ("staff_id", "full_name", "email")
    list_filter = ("department", "job_title", "role", "date_joined")
    ordering = ("staff_id",)

    list_display_links = ("staff_id", "full_name")

    #  Make role editable in the list view
    list_editable = ("role",)

    #  Make staff_id and age read-only but visible
    readonly_fields = ("staff_id", "age")

    #  Organize fields nicely
    fieldsets = (
        ("Personal Info", {
            "fields": ("full_name", "national_id", "dob", "age")
        }),
        ("Employment Info", {
            "fields": ("staff_id", "date_joined", "department", "job_title", "employment_type", "salary", "role")
        }),
        ("Contact Info", {
            "fields": ("email", "phone", "address")
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", 
        "get_staff_id", 
        "get_full_name", 
        "get_department", 
        "get_job_title",
        "get_role", 
        "profile_picture_preview"
    )
    search_fields = (
        "user__username", 
        "employee__staff_id", 
        "employee__full_name", 
        "employee__department", 
        "employee__job_title"
    )
    
    list_filter = ("employee__department", "employee__job_title")
    ordering = ("user",)

    fieldsets = (
        ("User Link", {
            "fields": ("user", "employee")
        }),
        ("Profile Picture", {
            "fields": ("profile_picture",)
        }),
    )

    # === Custom Columns ===
    def get_staff_id(self, obj):
        return obj.employee.staff_id if obj.employee else "-"
    get_staff_id.short_description = "Staff ID"

    def get_full_name(self, obj):
        return obj.employee.full_name if obj.employee else "-"
    get_full_name.short_description = "Full Name"

    def get_department(self, obj):
        return obj.employee.department if obj.employee else "-"
    get_department.short_description = "Department"

    def get_job_title(self, obj):
        return obj.employee.job_title if obj.employee else "-"
    get_job_title.short_description = "Job Title"

    def get_role(self, obj):
        # If you moved role into Employee
        return obj.employee.role if obj.employee else "-"
    get_role.short_description = "Role"

    # Show profile picture as thumbnail
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return f'<img src="{obj.profile_picture.url}" style="height:40px;width:40px;border-radius:50%;" />'
        return "—"
    profile_picture_preview.short_description = "Profile Picture"
    profile_picture_preview.allow_tags = True



# ================================================================
# Finance Models
# ================================================================
@admin.register(SalaryAdvanceRequest)
class SalaryAdvanceRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "date_requested")
    search_fields = ("user__username", "user__email")
    list_filter = ("status", "date_requested")
    ordering = ("-date_requested",)


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "amount", "status", "created_at")
    search_fields = ("employee__staff_id", "employee__full_name")
    list_filter = ("status", "created_at")
    ordering = ("-created_at",)


# ================================================================
# Chat Models
# ================================================================
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "message", "timestamp", "is_read")
    search_fields = ("sender__username", "receiver__username", "message")
    list_filter = ("is_read", "timestamp")
    ordering = ("-timestamp",)


@admin.register(SupportChatMessage)
class SupportChatMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "message", "timestamp", "is_read")
    search_fields = ("sender__username", "receiver__username", "message")
    list_filter = ("is_read", "timestamp")
    ordering = ("-timestamp",)
