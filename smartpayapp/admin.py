from django.contrib import admin
from .models import (
    Profile,
    Employee,
    SalaryAdvanceRequest,
    LoanRequest,
    ChatMessage,
    SupportChatMessage,
    EmployeeLeaveBalance, 
    LeaveRequest,
    LeaveType,
    Role,
    Department,
    OpenPosition,
    Project,
    ProjectStage,
    ProjectTask,
    AssignmentAcknowledgment,
    ProjectLog,
    DepartmentDocument,
    SuccessionPlan,
    EmployeeContract,

    EmployeePayrollProfile,
    EmployeePayslip,
    PayrollPeriod,
    OvertimeRate,
    EmployeeOvertimeAssignment

)
from django.utils.html import format_html
from django import forms
from django.core.exceptions import PermissionDenied








# ================================================================
# Role Admin
# ================================================================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


# ================================================================
# Department Admin
# ================================================================

class DepartmentAdminForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Only allow selecting employees in this department
            self.fields['head'].queryset = Employee.objects.filter(department=self.instance)
        else:
            self.fields['head'].queryset = Employee.objects.none()

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    form = DepartmentAdminForm
    list_display = ('name', 'head')
    search_fields = ('name',)
    ordering = ('name',)



# ================================================================
# Employee Admin
# ================================================================
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'staff_id', 'email', 'phone', 'department', 
        'job_title', 'role', 'employment_type', 'salary', 'date_joined', 
        'last_updated_by', 'last_updated_at'
    )
    list_filter = ('department', 'role', 'employment_type', 'date_joined')
    search_fields = ('full_name', 'staff_id', 'email', 'phone', 'job_title')
    ordering = ('staff_id',)
    readonly_fields = ('staff_id', 'age', 'last_updated_by', 'last_updated_at')  # make auto fields readonly

    fieldsets = (
        ('Personal Info', {
            'fields': ('full_name', 'national_id', 'dob', 'age', 'email', 'phone', 'address')
        }),
        ('Employment Info', {
            'fields': ('staff_id', 'department', 'job_title', 'employment_type', 'salary', 'date_joined', 'last_updated_by', 'last_updated_at')
        }),
        ('Role Info', {
            'fields': ('role',)
        }),
    )



# ================================================================
# Profile Admin
# ================================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_name', 'role', 'profile_picture_preview')
    search_fields = ('user__username', 'employee__full_name', 'employee__email')
    readonly_fields = ('profile_picture_preview',)

    # Display employee full name in list
    def employee_name(self, obj):
        return obj.employee.full_name if obj.employee else '-'
    employee_name.short_description = 'Employee Name'

    # Display role dynamically
    def role(self, obj):
        return obj.employee.role.name if obj.employee and obj.employee.role else 'employee'
    
    # Preview profile picture
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;" />', obj.profile_picture.url)
        return "-"
    profile_picture_preview.short_description = 'Profile Picture'





@admin.register(OpenPosition)
class OpenPositionAdmin(admin.ModelAdmin):
    list_display = (
        "job_title",
        "department",
        "status",
        "number_of_positions",
        "created_by",
        "created_by_id_no",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "department", "reason")
    search_fields = ("job_title", "department__name", "created_by__full_name")
    readonly_fields = ("created_by", "created_by_id_no", "created_at", "updated_at")
    ordering = ("-created_at",)


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


# ================================================================
# Attendance Model
# ================================================================
from .models import Attendance  # make sure this import is added

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "date",
        "clock_in",
        "clock_out",
        "hours_worked",
        "status",
        "late_minutes",
        "needs_explanation",
    )
    search_fields = (
        "employee__staff_id",
        "employee__full_name",
        "employee__department",
        "employee__job_title",
    )
    list_filter = ("status", "needs_explanation", "date", "employee__department")
    ordering = ("-date",)
    list_display_links = ("employee", "date")
    readonly_fields = ("hours_worked", "late_minutes", "status", "needs_explanation")

    fieldsets = (
        ("Employee & Date", {
            "fields": ("employee", "date")
        }),
        ("Times", {
            "fields": ("clock_in", "clock_out")
        }),
        ("Calculated Info", {
            "fields": ("hours_worked", "status", "late_minutes", "needs_explanation")
        }),
    )



# ================================================================
# Leave Management
# ================================================================
@admin.register(EmployeeLeaveBalance)
class EmployeeLeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "regular_leave", "off_days", "sick_leave_taken")
    search_fields = ("employee__staff_id", "employee__full_name", "employee__department")
    list_filter = ("employee__department",)
    ordering = ("employee__staff_id",)
    readonly_fields = ("sick_leave_taken",)  # only admin can adjust regular/off if needed

    fieldsets = (
        ("Employee", {
            "fields": ("employee",)
        }),
        ("Leave Balances", {
            "fields": ("regular_leave", "off_days", "sick_leave_taken")
        }),
    )



@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "leave_type",
        "start_date",
        "end_date",
        "total_days",
        "status",
        "approved_at",
        "rejected_at",
        "doctor_letter",
    )

    readonly_fields = ("approved_at", "rejected_at", "total_days", "resumption_date")
    list_filter = ("status", "leave_type", "start_date")
    search_fields = ("employee__full_name", "employee__staff_id")
    ordering = ("-created_at",)




# ====================================================
# Project Admin
# ====================================================
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'order_id', 'overall_status', 'created_by', 'created_at', 'updated_at')
    search_fields = ('name', 'order_id', 'description')
    list_filter = ('overall_status', 'created_at', 'departments')
    readonly_fields = ('order_id', 'created_by', 'created_at', 'updated_at')
    filter_horizontal = ('departments',)

admin.site.register(Project, ProjectAdmin)


# ====================================================
# ProjectStage Admin
# ====================================================
class ProjectStageAdmin(admin.ModelAdmin):
    list_display = ('project', 'department', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'department', 'project')
    search_fields = ('project__name', 'department__name', 'notes')
    filter_horizontal = ('employees',)

admin.site.register(ProjectStage, ProjectStageAdmin)


# ====================================================
# ProjectTask Admin
# ====================================================
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ('description', 'stage', 'assigned_to', 'assigned_by', 'status', 'start_date', 'due_date', 'completion_date')
    list_filter = ('status', 'stage__project', 'assigned_to')
    search_fields = ('description', 'assigned_to__username', 'assigned_by__username')
    readonly_fields = ('completion_date',)

admin.site.register(ProjectTask, ProjectTaskAdmin)


# ====================================================
# AssignmentAcknowledgment Admin
# ====================================================
class AssignmentAcknowledgmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'from_user', 'to_user', 'ack_type', 'timestamp')
    list_filter = ('ack_type', 'timestamp', 'from_user', 'to_user')
    search_fields = ('task__description', 'from_user__username', 'to_user__username', 'notes')
    readonly_fields = ('timestamp',)

admin.site.register(AssignmentAcknowledgment, AssignmentAcknowledgmentAdmin)


# ====================================================
# ProjectLog Admin
# ====================================================
class ProjectLogAdmin(admin.ModelAdmin):
    list_display = ('project', 'task', 'action_by', 'action_type', 'timestamp')
    list_filter = ('action_type', 'timestamp', 'action_by')
    search_fields = ('project__name', 'task__description', 'action_by__username', 'notes')
    readonly_fields = ('timestamp',)

admin.site.register(ProjectLog, ProjectLogAdmin)

# -------------------------
# Department Documents Admin
# -------------------------
@admin.register(DepartmentDocument)
class DepartmentDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'uploaded_at', 'file_link')
    search_fields = ('title', 'department__name')
    list_filter = ('department', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

    def file_link(self, obj):
        if obj.document_file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.document_file.url)
        return "No file"
    file_link.short_description = 'File'

# -------------------------
# Succession Plans Admin
# -------------------------
@admin.register(SuccessionPlan)
class SuccessionPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'uploaded_at', 'file_link')
    search_fields = ('title', 'department__name')
    list_filter = ('department', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

    def file_link(self, obj):
        if obj.plan_file:
            return format_html('<a href="{}" target="_blank">View Plan</a>', obj.plan_file.url)
        return "No file"
    file_link.short_description = 'File'



@admin.register(EmployeeContract)
class EmployeeContractAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 
        'contract_status', 
        'contract_expiry_date', 
        'created_by', 
        'created_at'
    )
    readonly_fields = ('created_by', 'created_at')
    search_fields = ('employee__full_name', 'employee__staff_id', 'created_by__full_name')
    list_filter = ('employee__employment_type',)

    def contract_status(self, obj):
        return "Permanent" if obj.employee.employment_type == "Permanent" else "Contract/Internship"
    contract_status.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        # Identify the Employee object linked to the current user (if exists)
        try:
            employee_user = Employee.objects.get(email=request.user.email)
        except Employee.DoesNotExist:
            employee_user = None

        # Permission check: only HR role or superuser
        if not request.user.is_superuser:
            if not employee_user or not (employee_user.role and employee_user.role.name.lower() == 'hr'):
                raise PermissionDenied("Only HR or Admin can create employee contracts.")

        # Set created_by on first creation
        if not obj.pk:
            obj.created_by = request.user  # Always set to the Django user creating the contract

        super().save_model(request, obj, form, change)


# ----------------------------
# Payroll Period Admin
# ----------------------------
@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ('month', 'year', 'start_date', 'end_date')
    list_filter = ('year', 'month')
    ordering = ('-year', '-month')


# ----------------------------
# Employee Payroll Profile Admin
# ----------------------------
@admin.register(EmployeePayrollProfile)
class EmployeePayrollProfileAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'payroll_employee_id',  # renamed from employee_id
        'department',
        'base_salary',
        'house_allowance_rate',
        'loan_repayment',
        'bonus',
        'hse_levy'
    )
    search_fields = ('employee__username', 'employee__email', 'payroll_employee_id')
    list_filter = ('department',)


# ----------------------------
# Employee Payslip Admin
# ----------------------------
@admin.register(EmployeePayslip)
class EmployeePayslipAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'period',
        'gross_salary',
        'house_allowance',
        'overtime_amount',
        'total_deductions',
        'net_pay',
        'status',
        'generated_at'
    )
    search_fields = ('employee__username',)
    list_filter = ('period', 'status')
    readonly_fields = (
        'gross_salary',
        'house_allowance',
        'overtime_hours',
        'overtime_rate',
        'overtime_amount',
        'paye',
        'nhif',
        'nssf',
        'loan_deduction',
        'hse_levy',
        'total_deductions',
        'net_pay',
        'generated_at'
    )

    # Optional: allow generating payslip from admin
    actions = ['generate_selected_payslips']

    def generate_selected_payslips(self, request, queryset):
        for payslip in queryset:
            payslip.generate_payslip()
        self.message_user(request, "Selected payslips have been generated.")
    generate_selected_payslips.short_description = "Generate selected payslips"



# ----------------------------
# Overtime Rate Admin
# ----------------------------
@admin.register(OvertimeRate)
class OvertimeRateAdmin(admin.ModelAdmin):
    list_display = ('rate_per_hour', 'effective_from', 'notes')
    ordering = ('-effective_from',)
    search_fields = ('rate_per_hour', 'notes')


# ----------------------------
# Overtime Assignment Admin
# ----------------------------
@admin.register(EmployeeOvertimeAssignment)
class EmployeeOvertimeAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'hours', 'status', 'approved_by', 'approved_at')
    list_filter = ('status', 'month', 'year')
    search_fields = ('employee__username', 'notes')
    ordering = ('-year', '-month')