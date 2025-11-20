from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os


# ==================== 文件验证函数 ====================
def validate_file_extension(value):
    """验证上传文件的扩展名"""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.dwg', '.dxf', '.ppt', '.pptx', '.doc', '.docx']
    if ext not in valid_extensions:
        raise ValidationError(
            _('不支持的文件格式。允许的格式：%(exts)s') % {
                'exts': ", ".join(valid_extensions)
            }
        )


def validate_file_size(value):
    """验证文件大小（限制为20MB）"""
    filesize = value.size
    if filesize > 20 * 1024 * 1024:  # 20MB
        raise ValidationError(_('文件大小不能超过 20MB'))


# ==================== 公司表 ====================
class Company(models.Model):
    """客户公司表"""
    company_name = models.CharField(_('公司名称'), max_length=200, unique=True)
    country = models.CharField(_('国家'), max_length=100)
    address = models.TextField(_('地址'), blank=True)
    website = models.URLField(_('网站'), blank=True)
    
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    is_active = models.BooleanField(_('是否有效'), default=True)
    notes = models.TextField(_('备注'), blank=True)
    
    class Meta:
        verbose_name = _('客户公司')
        verbose_name_plural = _('客户公司')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company_name} ({self.country})"


# ==================== 联系人表（Buyer 和 Supplier） ====================
class Contact(models.Model):
    """联系人表 - 支持 Buyer 和 Supplier 两种角色"""
    APPROVAL_STATUS_CHOICES = [
        ('pending', _('待审批')),
        ('approved', _('已批准')),
        ('rejected', _('已拒绝')),
    ]

    ROLE_CHOICES = [
        ('buyer', _('买家')),
        ('supplier', _('供应商')),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contacts', verbose_name=_('所属公司'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('登录账号'))
    
    # 新增：角色字段
    role = models.CharField(_('角色'), max_length=20, choices=ROLE_CHOICES, default='buyer')
    
    name = models.CharField(_('姓名'), max_length=100)
    position = models.CharField(_('职位'), max_length=100, blank=True)
    email = models.EmailField(_('邮箱'), unique=True)
    phone = models.CharField(_('电话'), max_length=50, blank=True)
    wechat = models.CharField(_('微信'), max_length=100, blank=True)
    
    is_primary = models.BooleanField(_('是否主要联系人'), default=False)
    is_active = models.BooleanField(_('是否有效'), default=True)
    
    # 审批状态
    approval_status = models.CharField(_('审批状态'), max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approved_at = models.DateTimeField(_('批准时间'), null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='approved_contacts', verbose_name=_('批准人'))
    rejection_reason = models.TextField(_('拒绝原因'), blank=True)
    
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    notes = models.TextField(_('备注'), blank=True)
    
    class Meta:
        verbose_name = _('联系人')
        verbose_name_plural = _('联系人')
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_role_display()} - {self.company.company_name})"
    
    def is_buyer(self):
        """是否是买家"""
        return self.role == 'buyer'
    
    def is_supplier(self):
        """是否是供应商"""
        return self.role == 'supplier'


# ==================== 询单表 ====================
class Inquiry(models.Model):
    """询单表 - 由客户创建，供应商报价"""
    STATUS_CHOICES = [
        ('pending', _('待报价')),
        ('quoted', _('已报价')),
        ('accepted', _('客户已接受')),
        ('rejected', _('客户已拒绝')),
        ('cancelled', _('已取消')),
    ]
    
    inquiry_number = models.CharField(_('询单号'), max_length=50, unique=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, verbose_name=_('询价联系人'))
    status = models.CharField(_('状态'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 客户填写的信息
    delivery_requirement = models.CharField(_('客户交货期要求'), max_length=200, blank=True)
    customer_notes = models.TextField(_('客户备注'), blank=True)
    
    # 供应商填写的报价信息
    quoted_lead_time = models.CharField(_('报工期'), max_length=200, blank=True)
    quoted_at = models.DateTimeField(_('报价时间'), null=True, blank=True)
    quoted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='quoted_inquiries', verbose_name=_('报价人'))
    supplier_notes = models.TextField(_('供应商备注'), blank=True)
    
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('询单')
        verbose_name_plural = _('询单')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.inquiry_number} - {self.contact.company.company_name}"
    
    def total_amount(self):
        """计算询单总金额（报价后）"""
        return sum(item.quoted_price * item.quantity for item in self.items.all() if item.quoted_price)


# ==================== 询单明细表 ====================
class InquiryItem(models.Model):
    """询单明细表"""
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='items', verbose_name=_('询单'))
    
    # 客户填写的需求信息
    product_name = models.CharField(_('产品名称'), max_length=200)
    material_name = models.CharField(_('材料名称'), max_length=200)
    material_grade = models.CharField(_('材料牌号'), max_length=100, blank=True)
    quantity = models.DecimalField(_('数量'), max_digits=10, decimal_places=2)
    unit = models.CharField(_('单位'), max_length=50, default='件')
    specifications = models.TextField(_('技术规格'), blank=True)
    
    # 单个图纸（可选，简单工件用这个）
    drawing_file = models.FileField(
        _('图纸文件'), 
        upload_to='drawings/inquiries/%Y/%m/', 
        blank=True, 
        null=True,
        validators=[validate_file_extension, validate_file_size],
        help_text=_('可选：单个图纸快速上传。复杂工件请使用下方"询单附件"上传多个文件')
    )
    
    # 供应商填写的报价
    quoted_price = models.DecimalField(_('报价单价(USD)'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(_('备注'), blank=True)
    
    class Meta:
        verbose_name = _('询单明细')
        verbose_name_plural = _('询单明细')
    
    def __str__(self):
        return f"{self.inquiry.inquiry_number} - {self.product_name}"
    
    def subtotal(self):
        """计算小计"""
        if self.quoted_price:
            return self.quantity * self.quoted_price
        return 0


# ==================== 询单附件表（新增） ====================
class InquiryAttachment(models.Model):
    """询单附件表 - 支持多个文件上传"""
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='attachments', verbose_name=_('询单'))
    
    file = models.FileField(
        _('文件'),
        upload_to='attachments/inquiries/%Y/%m/',
        validators=[validate_file_extension, validate_file_size]
    )
    file_name = models.CharField(_('文件名称'), max_length=255, blank=True)
    description = models.CharField(_('文件描述'), max_length=200, blank=True)
    file_size = models.IntegerField(_('文件大小(字节)'), default=0)
    
    uploaded_at = models.DateTimeField(_('上传时间'), auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('上传人'))
    
    class Meta:
        verbose_name = _('询单附件')
        verbose_name_plural = _('询单附件')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.inquiry.inquiry_number} - {self.file_name or self.file.name}"
    
    def save(self, *args, **kwargs):
        # 自动保存文件名和大小
        if self.file:
            if not self.file_name:
                self.file_name = os.path.basename(self.file.name)
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_extension(self):
        """获取文件扩展名"""
        return os.path.splitext(self.file.name)[1].lower()
    
    def get_file_size_display(self):
        """友好显示文件大小"""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


# ==================== 订单表 ====================
class Order(models.Model):
    """订单表 - 由客户创建，供应商确认并更新状态"""
    STATUS_CHOICES = [
        ('pending', _('待确认')),
        ('confirmed', _('已确认（生产中）')),
        ('ready', _('待提货')),
        ('shipped', _('已发货')),
        ('completed', _('已完成')),
        ('cancelled', _('已取消')),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', _('未付款')),
        ('partial', _('部分付款')),
        ('paid', _('已付款')),
    ]
    
    order_number = models.CharField(_('订单号'), max_length=50, unique=True)
    customer_order_number = models.CharField(_('客户订单号'), max_length=100, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, verbose_name=_('下单联系人'))
    inquiry = models.ForeignKey(Inquiry, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('关联询单'))
    
    status = models.CharField(_('订单状态'), max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(_('付款状态'), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    
    # 时间节点
    confirmed_at = models.DateTimeField(_('确认时间'), null=True, blank=True)
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='confirmed_orders', verbose_name=_('确认人'))
    
    delivery_date = models.DateField(_('预计交货日期'), blank=True, null=True)
    shipping_date = models.DateField(_('实际发货日期'), blank=True, null=True)
    completion_date = models.DateField(_('完成日期'), blank=True, null=True)
    
    # 备注
    customer_notes = models.TextField(_('客户备注'), blank=True)
    supplier_notes = models.TextField(_('供应商备注'), blank=True)
    
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('订单')
        verbose_name_plural = _('订单')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.contact.company.company_name}"
    
    def total_amount(self):
        """计算订单总金额"""
        return sum(item.subtotal() for item in self.items.all())


# ==================== 订单明细表 ====================
class OrderItem(models.Model):
    """订单明细表"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('订单'))
    
    product_name = models.CharField(_('产品名称'), max_length=200)
    material_name = models.CharField(_('材料名称'), max_length=200)
    material_grade = models.CharField(_('材料牌号'), max_length=100, blank=True)
    quantity = models.DecimalField(_('数量'), max_digits=10, decimal_places=2)
    unit = models.CharField(_('单位'), max_length=50, default='件')
    specifications = models.TextField(_('技术规格'), blank=True)
    
    unit_price = models.DecimalField(_('单价(USD)'), max_digits=10, decimal_places=2)
    
    # 单个图纸（可选，简单工件用这个）
    drawing_file = models.FileField(
        _('图纸文件'), 
        upload_to='drawings/orders/%Y/%m/', 
        blank=True, 
        null=True,
        validators=[validate_file_extension, validate_file_size],
        help_text=_('可选：单个图纸快速上传。复杂工件请使用下方"订单附件"上传多个文件')
    )
    
    notes = models.TextField(_('备注'), blank=True)
    
    class Meta:
        verbose_name = _('订单明细')
        verbose_name_plural = _('订单明细')
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product_name}"
    
    def subtotal(self):
        """计算小计"""
        return self.quantity * self.unit_price


# ==================== 订单附件表（新增） ====================
class OrderAttachment(models.Model):
    """订单附件表 - 支持多个文件上传"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='attachments', verbose_name=_('订单'))
    
    file = models.FileField(
        _('文件'),
        upload_to='attachments/orders/%Y/%m/',
        validators=[validate_file_extension, validate_file_size]
    )
    file_name = models.CharField(_('文件名称'), max_length=255, blank=True)
    description = models.CharField(_('文件描述'), max_length=200, blank=True)
    file_size = models.IntegerField(_('文件大小(字节)'), default=0)
    
    uploaded_at = models.DateTimeField(_('上传时间'), auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('上传人'))
    
    class Meta:
        verbose_name = _('订单附件')
        verbose_name_plural = _('订单附件')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.file_name or self.file.name}"
    
    def save(self, *args, **kwargs):
        # 自动保存文件名和大小
        if self.file:
            if not self.file_name:
                self.file_name = os.path.basename(self.file.name)
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_extension(self):
        """获取文件扩展名"""
        return os.path.splitext(self.file.name)[1].lower()
    
    def get_file_size_display(self):
        """友好显示文件大小"""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


# ==================== 沟通消息 ====================
class Message(models.Model):
    inquiry = models.ForeignKey('Inquiry', on_delete=models.CASCADE, related_name='messages', null=True, blank=True, verbose_name=_('关联询单'))
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='messages', null=True, blank=True, verbose_name=_('关联订单'))
    sender = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('发送人'))
    content = models.TextField(_('内容'), blank=True)
    created_at = models.DateTimeField(_('发送时间'), auto_now_add=True)

    class Meta:
        verbose_name = _('沟通消息')
        verbose_name_plural = _('沟通消息')
        ordering = ['-created_at']

    def __str__(self):
        target = self.inquiry and f"INQ:{self.inquiry.inquiry_number}" or (self.order and f"ORD:{self.order.order_number}" or '')
        return f"{target} - {self.sender.username}"


class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments', verbose_name=_('消息'))
    file = models.FileField(_('文件'), upload_to='attachments/messages/%Y/%m/', validators=[validate_file_extension, validate_file_size])
    file_name = models.CharField(_('文件名称'), max_length=255, blank=True)
    file_size = models.IntegerField(_('文件大小(字节)'), default=0)
    uploaded_at = models.DateTimeField(_('上传时间'), auto_now_add=True)

    class Meta:
        verbose_name = _('消息附件')
        verbose_name_plural = _('消息附件')
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if self.file:
            if not self.file_name:
                self.file_name = os.path.basename(self.file.name)
            self.file_size = self.file.size
        super().save(*args, **kwargs)