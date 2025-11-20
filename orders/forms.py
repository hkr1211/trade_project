from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Company, Contact, Inquiry, InquiryItem, Order, OrderItem, Message


# ==================== Buyer 注册表单 ====================
class BuyerRegistrationForm(forms.Form):
    """Buyer 注册表单"""
    company_name = forms.CharField(
        label=_('公司名称'),
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    country = forms.CharField(
        label=_('国家'),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    name = forms.CharField(
        label=_('您的姓名'),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    position = forms.CharField(
        label=_('职位'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('例如：采购经理')})
    )
    email = forms.EmailField(
        label=_('邮箱'),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label=_('电话'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_confirm = forms.CharField(
        label=_('确认密码'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def clean_email(self):
        """验证邮箱是否已被使用"""
        email = self.cleaned_data['email']
        if Contact.objects.filter(email=email).exists():
            raise ValidationError(_('该邮箱已被注册。'))
        return email
    
    def clean(self):
        """验证两次密码是否一致"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError(_('两次输入的密码不一致。'))
        
        return cleaned_data


# ==================== Supplier 注册表单 ====================
class SupplierRegistrationForm(forms.Form):
    """Supplier 注册表单"""
    name = forms.CharField(
        label=_('姓名'),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    position = forms.CharField(
        label=_('职位'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('例如：销售经理')})
    )
    email = forms.EmailField(
        label=_('邮箱'),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label=_('电话'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_confirm = forms.CharField(
        label=_('确认密码'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def clean_email(self):
        """验证邮箱是否已被使用"""
        email = self.cleaned_data['email']
        if Contact.objects.filter(email=email).exists():
            raise ValidationError(_('该邮箱已被注册。'))
        return email
    
    def clean(self):
        """验证两次密码是否一致"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError(_('两次输入的密码不一致。'))
        
        return cleaned_data


# ==================== 询单表单 ====================
class InquiryForm(forms.ModelForm):
    # 将交货期调整为整数输入（天）
    delivery_requirement = forms.IntegerField(
        label=_('交货期（天）'),
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入天数，例如 7'),
            'inputmode': 'numeric'
        })
    )
    class Meta:
        model = Inquiry
        fields = ['delivery_requirement', 'customer_notes']
        widgets = {
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InquiryItemForm(forms.ModelForm):
    class Meta:
        model = InquiryItem
        fields = ['product_name', 'material_name', 'material_grade', 'quantity', 'unit', 'specifications', 'drawing_file']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'material_name': forms.TextInput(attrs={'class': 'form-control'}),
            'material_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'value': 'PCS'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'drawing_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


InquiryItemFormSet = inlineformset_factory(
    Inquiry,
    InquiryItem,
    form=InquiryItemForm,
    extra=1,
    can_delete=False
)


# ==================== 订单表单 ====================
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['inquiry', 'customer_order_number', 'customer_notes']
        widgets = {
            'inquiry': forms.Select(attrs={'class': 'form-select'}),
            'customer_order_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product_name', 'material_name', 'material_grade', 'quantity', 'unit', 'unit_price', 'specifications', 'drawing_file']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'material_name': forms.TextInput(attrs={'class': 'form-control'}),
            'material_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'value': 'PCS'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'drawing_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=False
)


# ==================== 沟通消息表单 ====================
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('输入消息...')})
        }