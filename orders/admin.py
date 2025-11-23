from django import forms
import os
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin import sites
from django.contrib.admin.actions import delete_selected
from .models import (Company, Contact, Inquiry, InquiryItem, InquiryAttachment,
                     Order, OrderItem, OrderAttachment)


# ==================== 联系人表单（用于管理后台） ====================
class ContactAdminForm(forms.ModelForm):
    """联系人管理表单，支持密码设置"""
    password = forms.CharField(
        label='登录密码',
        widget=forms.PasswordInput(attrs={'placeholder': '如果不修改密码请留空'}),
        required=False,
        help_text='为该联系人设置登录密码。如果是编辑已有联系人，留空表示不修改密码。'
    )
    
    class Meta:
        model = Contact
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是新建联系人，密码必填
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['password'].help_text = '为该联系人设置登录密码（必填）'
    
    def save(self, commit=True):
        contact = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        # 如果是新建联系人或者填写了密码
        if password:
            if contact.user:
                # 更新现有用户的密码
                contact.user.set_password(password)
                contact.user.save()
            else:
                # 检查是否已存在相同邮箱的用户
                try:
                    existing_user = User.objects.get(username=contact.email)
                    # 如果存在，重用该用户并更新密码
                    existing_user.set_password(password)
                    existing_user.first_name = contact.name
                    existing_user.email = contact.email
                    existing_user.is_active = True
                    existing_user.save()
                    contact.user = existing_user
                except User.DoesNotExist:
                    # 不存在，创建新用户
                    user = User.objects.create_user(
                        username=contact.email,
                        email=contact.email,
                        password=password,
                        first_name=contact.name,
                        is_active=True
                    )
                    contact.user = user
                
                # 管理员创建的联系人自动批准
                if not contact.pk:  # 新建时
                    contact.approval_status = 'approved'
                    contact.approved_at = timezone.now()
        
        if commit:
            contact.save()
        
        return contact



# ==================== 联系人内联（用于公司管理页面） ====================
class ContactInline(admin.StackedInline):  # 改为 StackedInline 以显示更多字段
    model = Contact
    form = ContactAdminForm
    extra = 0
    fields = [
        ('name', 'position'), 
        ('email', 'phone'), 
        'password',  # 新增：密码字段
        ('is_primary', 'is_active'),
        'approval_status',
        'notes'
    ]
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        # 编辑时，审批状态只读（通过批量操作修改）
        if obj:
            return ['approval_status']
        return []


# ==================== 公司管理 ====================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'country', 'contact_count', 'created_at']
    search_fields = ['company_name']
    list_filter = ['country', 'is_active']
    inlines = [ContactInline]
    
    def contact_count(self, obj):
        return obj.contacts.count()
    contact_count.short_description = '联系人数'


# ==================== 联系人管理（独立页面） ====================
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    form = ContactAdminForm
    list_display = ['name', 'company', 'get_role_display', 'email', 'phone', 
                    'approval_status_display', 'has_login_account', 'is_primary', 'created_at']
    search_fields = ['name', 'email', 'company__company_name']
    list_filter = ['company', 'role', 'approval_status', 'is_primary', 'is_active']  # 添加 role 筛选
    actions_on_top = True
    actions_on_bottom = True
    actions_selection_counter = True
    
    fieldsets = (
        ('基本信息', {
            'fields': ('company', 'name', 'position', 'email', 'phone', 'wechat')
        }),
        ('登录账号', {
            'fields': ('password',),
            'description': '为该联系人设置登录密码'
        }),
        ('审批信息', {
            'fields': ('approval_status', 'approved_at', 'approved_by', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('其他', {
            'fields': ('is_primary', 'is_active', 'notes'),
        }),
    )
    
    readonly_fields = ['approved_at', 'approved_by']
    
    actions = ['approve_contacts', 'reject_contacts', 'reset_password']
    
    def get_role_display(self, obj):
        """显示角色"""
        if obj.role == 'buyer':
            return format_html('<span style="color: blue;">👤 买家</span>')
        else:
            return format_html('<span style="color: green;">🏢 供应商</span>')
    get_role_display.short_description = '角色'
    
    def has_login_account(self, obj):
        """显示是否有登录账号"""
        if obj.user:
            return format_html('<span style="color: green;">✓ 已创建</span>')
        return format_html('<span style="color: red;">✗ 未创建</span>')
    has_login_account.short_description = '登录账号'
    
    def approval_status_display(self, obj):
        """彩色显示审批状态"""
        if obj.approval_status == 'approved':
            return format_html('<span style="color: green; font-weight: bold;">✓ 已批准</span>')
        elif obj.approval_status == 'rejected':
            return format_html('<span style="color: red; font-weight: bold;">✗ 已拒绝</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">⏳ 待审批</span>')
    approval_status_display.short_description = '审批状态'
    
    @admin.action(description='✓ 批量批准选中的联系人', permissions=['change', 'delete'])
    def approve_contacts(self, request, queryset):
        """批量批准"""
        count = 0
        for contact in queryset.filter(approval_status='pending'):
            contact.approval_status = 'approved'
            contact.approved_at = timezone.now()
            contact.approved_by = request.user
            contact.save()
            
            # 激活用户账号
            if contact.user:
                contact.user.is_active = True
                contact.user.save()
            
            count += 1
        
        self.message_user(request, f'成功批准 {count} 个买家账号。', messages.SUCCESS)
    approve_contacts.short_description = '✓ 批准选中的买家'
    
    @admin.action(description='✗ 批量拒绝选中的联系人', permissions=['change', 'delete'])
    def reject_contacts(self, request, queryset):
        """批量拒绝"""
        count = 0
        for contact in queryset.filter(approval_status='pending'):
            contact.approval_status = 'rejected'
            contact.rejection_reason = '管理员拒绝'
            contact.save()
            count += 1
        
        self.message_user(request, f'已拒绝 {count} 个买家账号。', messages.WARNING)
    reject_contacts.short_description = '✗ 拒绝选中的买家'
    
    @admin.action(description='🔑 重置选中用户的密码', permissions=['change', 'delete'])
    def reset_password(self, request, queryset):
        """重置密码（生成临时密码）"""
        import random
        import string
        
        for contact in queryset:
            if contact.user:
                # 生成随机密码
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                contact.user.set_password(temp_password)
                contact.user.save()
                
                # 在消息中显示临时密码（实际应用中应该发邮件）
                self.message_user(
                    request, 
                    f'{contact.name} ({contact.email}) 的临时密码：{temp_password}',
                    messages.WARNING
                )
        
        self.message_user(request, '已重置密码，请将临时密码发送给用户。', messages.SUCCESS)
    reset_password.short_description = '🔑 重置选中用户的密码'


# ==================== 询单明细内联 ====================
class InquiryItemInline(admin.TabularInline):
    model = InquiryItem
    extra = 0
    fields = ['product_name', 'material_name', 'material_grade', 'quantity', 'unit', 
              'specifications', 'drawing_file', 'quoted_price']
    readonly_fields = ['drawing_file']


# ==================== 询单附件内联 ====================
class InquiryAttachmentInline(admin.TabularInline):
    model = InquiryAttachment
    extra = 1
    fields = ['file', 'file_name', 'description', 'get_file_info', 'uploaded_at']
    readonly_fields = ['get_file_info', 'uploaded_at']
    
    def get_file_info(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">下载</a> | {} | {}',
                obj.file.url,
                obj.get_file_extension(),
                obj.get_file_size_display()
            )
        return '-'
    get_file_info.short_description = '文件信息'


# ==================== 询单管理 ====================
@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['inquiry_number', 'get_company', 'contact', 'status', 
                    'attachment_count', 'created_at']
    search_fields = ['inquiry_number', 'contact__company__company_name', 'contact__name']
    list_filter = ['status', 'created_at']
    inlines = [InquiryItemInline, InquiryAttachmentInline]
    
    fieldsets = (
        ('询单信息', {
            'fields': ('inquiry_number', 'contact', 'status')
        }),
        ('客户需求', {
            'fields': ('delivery_requirement', 'customer_notes'),
            'classes': ('collapse',)
        }),
        ('供应商报价', {
            'fields': ('quoted_lead_time', 'quoted_at', 'quoted_by', 'supplier_notes'),
            'description': '在此填写报价信息'
        }),
    )
    
    readonly_fields = ['inquiry_number', 'created_at']
    
    def get_company(self, obj):
        return obj.contact.company.company_name
    get_company.short_description = '公司'
    
    def attachment_count(self, obj):
        count = obj.attachments.count()
        if count > 0:
            return format_html('<span style="color: green;">{} 个附件</span>', count)
        return '-'
    attachment_count.short_description = '附件'
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'quoted' and not obj.quoted_at:
            obj.quoted_at = timezone.now()
            obj.quoted_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, InquiryAttachment) and not instance.uploaded_by:
                instance.uploaded_by = request.user
            instance.save()
        formset.save_m2m()


# ==================== 订单明细内联 ====================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product_name', 'material_name', 'material_grade', 'quantity', 'unit', 
              'specifications', 'unit_price', 'drawing_file']
    readonly_fields = ['drawing_file']


# ==================== 订单附件内联 ====================
class OrderAttachmentInline(admin.TabularInline):
    model = OrderAttachment
    extra = 1
    fields = ['file', 'file_name', 'description', 'get_file_info', 'uploaded_at']
    readonly_fields = ['get_file_info', 'uploaded_at']
    
    def get_file_info(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">下载</a> | {} | {}',
                obj.file.url,
                obj.get_file_extension(),
                obj.get_file_size_display()
            )
        return '-'
    get_file_info.short_description = '文件信息'


# ==================== 订单管理 ====================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'get_company', 'contact', 'status', 'payment_status', 
                    'attachment_count', 'delivery_date', 'created_at', 'total_amount']
    search_fields = ['order_number', 'contact__company__company_name', 'contact__name']
    list_filter = ['status', 'payment_status', 'created_at']
    inlines = [OrderItemInline, OrderAttachmentInline]
    
    fieldsets = (
        ('订单基本信息', {
            'fields': ('order_number', 'contact', 'inquiry', 'status', 'payment_status')
        }),
        ('时间节点', {
            'fields': ('confirmed_at', 'confirmed_by', 'delivery_date', 'shipping_date', 'completion_date'),
        }),
        ('备注信息', {
            'fields': ('customer_notes', 'supplier_notes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['order_number', 'created_at', 'confirmed_at', 'confirmed_by']
    
    def get_company(self, obj):
        return obj.contact.company.company_name
    get_company.short_description = '公司'
    
    def attachment_count(self, obj):
        count = obj.attachments.count()
        if count > 0:
            return format_html('<span style="color: green;">{} 个附件</span>', count)
        return '-'
    attachment_count.short_description = '附件'
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'confirmed' and not obj.confirmed_at:
            obj.confirmed_at = timezone.now()
            obj.confirmed_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, OrderAttachment) and not instance.uploaded_by:
                instance.uploaded_by = request.user
            instance.save()
        formset.save_m2m()


# ==================== 用户管理批量动作 ====================
# 将 permissions=['change', 'delete'] 修改为 permissions=['change']

@admin.action(description='✓ 批量激活选中用户')
def activate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    messages.success(request, f'已激活 {updated} 个用户')


@admin.action(description='✗ 批量禁用选中用户')
def deactivate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    messages.success(request, f'已禁用 {updated} 个用户')


@admin.action(description='👤 设为工作人员（is_staff=True）')
def grant_staff(modeladmin, request, queryset):
    updated = queryset.update(is_staff=True)
    messages.success(request, f'已设为工作人员 {updated} 个用户')


@admin.action(description='🚫 取消工作人员（is_staff=False）')
def revoke_staff(modeladmin, request, queryset):
    updated = queryset.update(is_staff=False)
    messages.success(request, f'已取消工作人员 {updated} 个用户')


@admin.action(description='⭐ 设为超级用户（is_superuser=True）')
def grant_superuser(modeladmin, request, queryset):
    updated = queryset.update(is_superuser=True)
    messages.success(request, f'已设为超级用户 {updated} 个')


@admin.action(description='⬇ 取消超级用户（is_superuser=False）')
def revoke_superuser(modeladmin, request, queryset):
    updated = queryset.update(is_superuser=False)
    messages.success(request, f'已取消超级用户 {updated} 个')



# ==================== User Admin Customization ====================
class UserAdmin(DjangoUserAdmin):
    actions = [
        activate_users,
        deactivate_users,
        grant_staff,
        revoke_staff,
        grant_superuser,
        revoke_superuser,
        delete_selected,
    ]
    actions_on_top = True
    actions_on_bottom = True
    actions_selection_counter = True

# Safely unregister and re-register User
try:
    admin.site.unregister(User)
except sites.NotRegistered:
    pass

admin.site.register(User, UserAdmin)

# ==================== Admin Site Configuration ====================
admin.site.site_header = f"外贸系统管理后台（{os.environ.get('APP_BUILD_ID', 'local')}）"
admin.site.site_title = "外贸系统管理后台"
admin.site.index_title = "管理功能"
