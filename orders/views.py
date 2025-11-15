from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.db.utils import OperationalError
from django.db import connection
import logging
import traceback

logger = logging.getLogger(__name__)

from .models import Company, Contact, Inquiry, InquiryItem, InquiryAttachment, Order, OrderItem, OrderAttachment
from .forms import (
    BuyerRegistrationForm, 
    InquiryForm, 
    InquiryItemFormSet, 
    OrderForm, 
    OrderItemFormSet,
    SupplierRegistrationForm
)

# ==================== 获取或创建供应商公司 ====================
def get_supplier_company():
    """获取或创建供应商公司（宝鸡蕴杰金属制品有限公司）"""
    company, created = Company.objects.get_or_create(
        company_name='宝鸡蕴杰金属制品有限公司',
        defaults={
            'country': '中国',
            'address': '陕西省宝鸡市',
            'is_active': True
        }
    )
    return company


# ==================== Supplier 注册 ====================
def supplier_register(request):
    """Supplier 注册页面"""
    if request.method == 'POST':
        form = SupplierRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 创建用户账号（设为不活跃，等待审批）
                    user = User.objects.create_user(
                        username=form.cleaned_data['email'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['name'],
                        is_active=False
                    )
                    
                    # 获取供应商公司
                    supplier_company = get_supplier_company()
                    
                    # 创建供应商联系人记录
                    contact = Contact.objects.create(
                        company=supplier_company,
                        user=user,
                        role='supplier',  # 设置为供应商角色
                        name=form.cleaned_data['name'],
                        position=form.cleaned_data.get('position', ''),
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data.get('phone', ''),
                        approval_status='pending'
                    )
                    
                    messages.success(request, '注册成功！您的账号正在等待管理员审批，审批通过后您将收到通知。')
                    return redirect('supplier_login')
            except Exception as e:
                messages.error(request, f'注册失败：{str(e)}')
    else:
        form = SupplierRegistrationForm()
    
    return render(request, 'orders/supplier_register.html', {'form': form})


# ==================== Supplier 登录 ====================
def supplier_login(request):
    """Supplier 登录页面"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            try:
                contact = Contact.objects.get(user=user, role='supplier')
                if contact.approval_status != 'approved':
                    if contact.approval_status == 'pending':
                        messages.warning(request, '您的账号正在等待管理员审批，请耐心等待。')
                    else:
                        messages.error(request, f'您的账号已被拒绝。原因：{contact.rejection_reason}')
                    return redirect('supplier_login')
            except Contact.DoesNotExist:
                messages.error(request, '该账号不是有效的供应商账号。')
                return redirect('supplier_login')
            
            login(request, user)
            messages.success(request, f'欢迎回来，{contact.name}！')
            return redirect('supplier_dashboard')
        else:
            messages.error(request, '邮箱或密码错误。')
    
    return render(request, 'orders/supplier_login.html')


# ==================== Supplier 仪表板 ====================
@login_required
def supplier_dashboard(request):
    """Supplier 仪表板 - 显示所有询单和订单"""
    try:
        contact = Contact.objects.get(user=request.user, role='supplier')
    except Contact.DoesNotExist:
        messages.error(request, _('您不是供应商账号。'))
        return redirect('home')
    
    # 供应商可以看到所有询单和订单
    inquiries = Inquiry.objects.all()
    orders = Order.objects.all()
    
    context = {
        'contact': contact,
        'inquiry_count': inquiries.count(),
        'order_count': orders.count(),
        'pending_inquiries': inquiries.filter(status='pending').count(),
        'pending_orders': orders.filter(status='pending').count(),
        'recent_inquiries': inquiries[:10],
        'recent_orders': orders[:10],
    }
    
    return render(request, 'orders/supplier_dashboard.html', context)

# =====================获取询单详细信息=========================================
@login_required
def get_inquiry_details(request, inquiry_id):
    """获取询单详细信息的API端点"""
    try:
        inquiry = get_object_or_404(Inquiry, id=inquiry_id, contact__user=request.user)
        
        # 获取询单明细项
        items = []
        for item in inquiry.items.all():
            items.append({
                'product_name': item.product_name,
                'material_name': item.material_name,
                'material_grade': item.material_grade or '',
                'quantity': str(item.quantity),
                'unit': item.unit,
                'specifications': item.specifications or '',
                # 如果有报价，也包含价格信息
                'unit_price': str(item.unit_price) if hasattr(item, 'unit_price') else ''
            })
        
        data = {
            'success': True,
            'inquiry': {
                'inquiry_number': inquiry.inquiry_number,
                'delivery_requirement': inquiry.delivery_requirement or '',
                'customer_notes': inquiry.customer_notes or '',
            },
            'items': items
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
# ==================== Supplier 查看所有询单 ====================
@login_required
def supplier_inquiry_list(request):
    """供应商查看所有询单列表"""
    try:
        contact = Contact.objects.get(user=request.user, role='supplier')
    except Contact.DoesNotExist:
        messages.error(request, _('您不是供应商账号。'))
        return redirect('home')
    
    inquiries = Inquiry.objects.all().prefetch_related('items', 'attachments').order_by('-created_at')
    
    # 筛选功能
    status = request.GET.get('status')
    if status:
        inquiries = inquiries.filter(status=status)

    # 检索：询单号、产品名称
    q = (request.GET.get('q') or '').strip()
    if q:
        inquiries = inquiries.filter(
            Q(inquiry_number__icontains=q) |
            Q(items__product_name__icontains=q)
        ).distinct()
    
    return render(request, 'orders/supplier_inquiry_list.html', {
        'contact': contact,
        'inquiries': inquiries,
        'q': q,
        'status': status or ''
    })


# ==================== Supplier 查看询单详情并报价 ====================
@login_required
def supplier_inquiry_detail(request, inquiry_id):
    """供应商查看询单详情并进行报价"""
    try:
        contact = Contact.objects.get(user=request.user, role='supplier')
    except Contact.DoesNotExist:
        messages.error(request, _('您不是供应商账号。'))
        return redirect('home')
    
    inquiry = get_object_or_404(Inquiry, id=inquiry_id)
    
    # POST 请求：提交报价
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 销售锁定规则：一旦已有 quoted_by，则仅允许该销售继续操作
                if inquiry.quoted_by and inquiry.quoted_by != request.user:
                    messages.error(request, f'该询单已由销售 {inquiry.quoted_by.get_full_name() or inquiry.quoted_by.username} 负责，请联系其处理。')
                    return redirect('supplier_inquiry_detail', inquiry_id=inquiry.id)

                # 更新询单状态和报价信息
                inquiry.quoted_lead_time = request.POST.get('quoted_lead_time', '')
                inquiry.supplier_notes = request.POST.get('supplier_notes', '')
                inquiry.status = 'quoted'
                inquiry.quoted_at = timezone.now()
                # 初次报价时锁定负责销售；若已锁定则不覆盖
                if not inquiry.quoted_by:
                    inquiry.quoted_by = request.user
                inquiry.save()
                
                # 更新每个产品的报价
                for item in inquiry.items.all():
                    quoted_price = request.POST.get(f'item_{item.id}_price')
                    if quoted_price:
                        item.quoted_price = quoted_price
                        item.save()
                
            messages.success(request, _('询单 %(inquiry_number)s 报价成功！') % {'inquiry_number': inquiry.inquiry_number})
            return redirect('supplier_inquiry_detail', inquiry_id=inquiry.id)
        except Exception as e:
            messages.error(request, _('报价失败：%(error)s') % {'error': str(e)})
    
    return render(request, 'orders/supplier_inquiry_detail.html', {
        'contact': contact,
        'inquiry': inquiry
    })


# ==================== Supplier 查看所有订单 ====================
@login_required
def supplier_order_list(request):
    """供应商查看所有订单列表"""
    try:
        contact = Contact.objects.get(user=request.user, role='supplier')
    except Contact.DoesNotExist:
        messages.error(request, _('您不是供应商账号。'))
        return redirect('home')
    
    orders = Order.objects.all().prefetch_related('items', 'attachments').order_by('-created_at')
    
    # 筛选功能
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    # 检索：订单号、产品名称、客户订单号
    q = (request.GET.get('q') or '').strip()
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(items__product_name__icontains=q) |
            Q(customer_order_number__icontains=q)
        ).distinct()
    
    return render(request, 'orders/supplier_order_list.html', {
        'contact': contact,
        'orders': orders,
        'q': q,
        'status': status or ''
    })


# ==================== Supplier 查看订单详情并更新状态 ====================
@login_required
def supplier_order_detail(request, order_id):
    """供应商查看订单详情并更新状态"""
    try:
        contact = Contact.objects.get(user=request.user, role='supplier')
    except Contact.DoesNotExist:
        messages.error(request, _('您不是供应商账号。'))
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    
    # POST 请求：更新订单状态
    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            # 负责销售判定：已确认人优先；否则取询单报价人
            responsible_user = order.confirmed_by or (getattr(order, 'inquiry', None) and order.inquiry.quoted_by)

            if action == 'confirm':
                # 若已有询单报价人且与当前人不一致，则不允许确认
                if getattr(order, 'inquiry', None) and order.inquiry.quoted_by and order.inquiry.quoted_by != request.user:
                    messages.error(request, _('该订单关联询单已由销售 %(sales)s 负责，请联系其进行确认。') % {'sales': (order.inquiry.quoted_by.get_full_name() or order.inquiry.quoted_by.username)})
                    return redirect('supplier_order_detail', order_id=order.id)
                # 若已存在确认人且与当前人不一致，也不允许重复确认
                if order.confirmed_by and order.confirmed_by != request.user:
                    messages.error(request, _('该订单已由销售 %(sales)s 确认，不可由其他人再次确认。') % {'sales': (order.confirmed_by.get_full_name() or order.confirmed_by.username)})
                    return redirect('supplier_order_detail', order_id=order.id)
                order.status = 'confirmed'
                order.confirmed_at = timezone.now()
                order.confirmed_by = request.user
                order.delivery_date = request.POST.get('delivery_date')
                messages.success(request, _('订单已确认！'))
            elif action == 'ship':
                # 发货必须由负责销售执行
                if not responsible_user or responsible_user != request.user:
                    messages.error(request, _('仅负责销售可执行发货操作。'))
                    return redirect('supplier_order_detail', order_id=order.id)
                order.status = 'shipped'
                order.shipping_date = timezone.now().date()
                messages.success(request, _('订单已发货！'))
            elif action == 'confirm_payment':
                # 供应商确认收款
                if not responsible_user or responsible_user != request.user:
                    messages.error(request, _('仅负责销售可确认收款。'))
                    return redirect('supplier_order_detail', order_id=order.id)
                order.payment_status = 'paid'
                messages.success(request, _('收款已确认，付款状态更新为已付款。'))
            elif action == 'complete':
                # 未确认收款，不得确认订单完成
                if order.payment_status != 'paid':
                    messages.error(request, _('未确认收款，不能完成订单。请先确认收款。'))
                    return redirect('supplier_order_detail', order_id=order.id)
                if not responsible_user or responsible_user != request.user:
                    messages.error(request, _('仅负责销售可确认订单完成。'))
                    return redirect('supplier_order_detail', order_id=order.id)
                order.status = 'completed'
                order.completion_date = timezone.now().date()
                messages.success(request, _('订单已完成！'))
            elif action == 'update_notes':
                order.supplier_notes = request.POST.get('supplier_notes', '')
                messages.success(request, _('备注已更新！'))
            
            order.save()
            return redirect('supplier_order_detail', order_id=order.id)
        except Exception as e:
            messages.error(request, _('操作失败：%(error)s') % {'error': str(e)})
    
    return render(request, 'orders/supplier_order_detail.html', {
        'contact': contact,
        'order': order
    })

# ==================== 首页 ====================
# 修改原有的 home 视图，支持供应商跳转
def home(request):
    """首页 - 显示欢迎页面"""
    contact = None
    if request.user.is_authenticated:
        try:
            contact = Contact.objects.get(user=request.user)
            if contact.approval_status == 'approved':
                if contact.role == 'buyer':
                    return redirect('buyer_dashboard')
                elif contact.role == 'supplier':
                    return redirect('supplier_dashboard')
        except Contact.DoesNotExist:
            pass
    
    return render(request, 'orders/home.html', {'contact': contact})


# ==================== Buyer 注册 ====================
def buyer_register(request):
    """Buyer 注册页面"""
    if request.method == 'POST':
        form = BuyerRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 检查用户是否已存在
                    email = form.cleaned_data['email']
                    if User.objects.filter(username=email).exists():
                        messages.error(request, _('该邮箱已被注册。'))
                        return render(request, 'orders/buyer_register.html', {'form': form})

                    # 创建用户账号（设为不活跃，等待审批）
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['name'],
                        is_active=False  # 设为不活跃，等待审批
                    )
                    
                    # 获取或创建公司记录
                    company, _ = Company.objects.get_or_create(
                        company_name=form.cleaned_data['company_name'],
                        defaults={
                            'country': form.cleaned_data.get('country', ''),
                            'is_active': True
                        }
                    )

                    # 创建联系人记录
                    contact = Contact.objects.create(
                        company=company,
                        user=user,
                        role='buyer',  # 明确设置为买家角色
                        name=form.cleaned_data['name'],
                        position=form.cleaned_data.get('position', ''),
                        email=form.cleaned_data['email'],
                        phone=form.cleaned_data.get('phone', ''),
                        approval_status='pending'
                    )
                    
                    messages.success(request, _('注册成功！您的账号正在等待管理员审批，审批通过后您将收到邮件通知。'))
                    return redirect('buyer_login')
            except Exception as e:
                # 记录详细错误信息
                logger.error(f'Buyer registration failed: {str(e)}')
                logger.error(traceback.format_exc())
                messages.error(request, _('注册失败：%(error)s') % {'error': str(e)})
    else:
        form = BuyerRegistrationForm()
    
    return render(request, 'orders/buyer_register.html', {'form': form})


# ==================== Buyer 登录 ====================
def buyer_login(request):
    """Buyer 登录页面"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                try:
                    contact = Contact.objects.get(user=user)
                    if contact.approval_status != 'approved':
                        if contact.approval_status == 'pending':
                            messages.warning(request, '您的账号正在等待管理员审批，请耐心等待。')
                        else:
                            messages.error(request, f'您的账号已被拒绝。原因：{contact.rejection_reason}')
                        return redirect('buyer_login')
                except Contact.DoesNotExist:
                    messages.error(request, _('该账号不是有效的买家账号。'))
                    return redirect('buyer_login')
                login(request, user)
                messages.success(request, _('欢迎回来，%(name)s！') % {'name': contact.name})
                return redirect('buyer_dashboard')
            else:
                messages.error(request, _('邮箱或密码错误。'))
        except OperationalError:
            messages.error(request, _('数据库连接失败，请稍后再试。'))
            return render(request, 'orders/buyer_login.html')
    
    return render(request, 'orders/buyer_login.html')


# ==================== Buyer 登出 ====================
def buyer_logout(request):
    """Buyer 登出"""
    logout(request)
    messages.success(request, _('您已成功登出。'))
    return redirect('home')


# ==================== Buyer 仪表板 ====================
@login_required
def buyer_dashboard(request):
    """Buyer 仪表板 - 显示概览信息"""
    try:
        contact = Contact.objects.get(user=request.user)
    except Contact.DoesNotExist:
        messages.error(request, _('未找到联系人信息。'))
        return redirect('home')
    
    # 统计数据
    inquiries = Inquiry.objects.filter(contact=contact)
    orders = Order.objects.filter(contact=contact)
    
    context = {
        'contact': contact,
        'inquiry_count': inquiries.count(),
        'order_count': orders.count(),
        'pending_inquiries': inquiries.filter(status='pending').count(),
        'pending_orders': orders.filter(status='pending').count(),
        'recent_inquiries': inquiries[:5],
        'recent_orders': orders[:5],
    }
    
    return render(request, 'orders/buyer_dashboard.html', context)

def health_db(request):
    try:
        connection.ensure_connection()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


# ==================== 我的询单列表 ====================
@login_required
def inquiry_list(request):
    """我的询单列表"""
    try:
        contact = Contact.objects.get(user=request.user)
    except Contact.DoesNotExist:
        messages.error(request, _('未找到联系人信息。'))
        return redirect('home')
    # 买家可见范围：同公司内的所有询单
    inquiries = Inquiry.objects.filter(contact__company=contact.company).prefetch_related('items', 'attachments').order_by('-created_at')

    # 检索：询单号、产品名称
    q = (request.GET.get('q') or '').strip()
    if q:
        inquiries = inquiries.filter(
            Q(inquiry_number__icontains=q) |
            Q(items__product_name__icontains=q)
        ).distinct()

    return render(request, 'orders/inquiry_list.html', {
        'contact': contact,
        'inquiries': inquiries,
        'q': q
    })


# ==================== 询单详情 ====================
@login_required
def inquiry_detail(request, inquiry_id):
    """询单详情页面"""
    try:
        contact = Contact.objects.get(user=request.user)
    except Contact.DoesNotExist:
        messages.error(request, _('未找到联系人信息。'))
        return redirect('home')
    
    inquiry = get_object_or_404(Inquiry, id=inquiry_id, contact=contact)
    
    return render(request, 'orders/inquiry_detail.html', {
        'contact': contact,
        'inquiry': inquiry
    })


# ==================== 创建询单 ====================
@login_required
def inquiry_create(request):
    """创建询单页面"""
    try:
        contact = Contact.objects.get(user=request.user)
    except Contact.DoesNotExist:
        messages.error(request, _('未找到联系人信息。'))
        return redirect('home')
    
    if request.method == 'POST':
        form = InquiryForm(request.POST)
        formset = InquiryItemFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # 生成询单号
                    inquiry_number = f"INQ-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # 创建询单
                    inquiry = Inquiry.objects.create(
                        inquiry_number=inquiry_number,
                        contact=contact,
                        delivery_requirement=str(form.cleaned_data.get('delivery_requirement', '')),  # 存储为字符串，但输入为数字天数
                        customer_notes=form.cleaned_data.get('customer_notes', ''),
                        status='pending'
                    )
                    
                    # 保存询单明细
                    for item_form in formset:
                        if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                            InquiryItem.objects.create(
                                inquiry=inquiry,
                                product_name=item_form.cleaned_data['product_name'],
                                material_name=item_form.cleaned_data['material_name'],
                                material_grade=item_form.cleaned_data.get('material_grade', ''),
                                quantity=item_form.cleaned_data['quantity'],
                                unit=item_form.cleaned_data.get('unit', '件'),
                                specifications=item_form.cleaned_data.get('specifications', ''),
                                drawing_file=item_form.cleaned_data.get('drawing_file')
                            )
                    
                    # 第 604-611 行
                    # 处理附件上传
                    files = request.FILES.getlist('attachments')
                    for file in files:
                        InquiryAttachment.objects.create(
                            inquiry=inquiry,
                            file=file,
                            file_name=file.name,  # 添加 file_name
                            uploaded_by=request.user
                        )

                    messages.success(request, _('询单 %(inquiry_number)s 创建成功！') % {'inquiry_number': inquiry_number})
                    return redirect('inquiry_detail', inquiry_id=inquiry.id)
            except Exception as e:
                messages.error(request, _('创建询单失败：%(error)s') % {'error': str(e)})
    else:
        form = InquiryForm()
        formset = InquiryItemFormSet()
    
    return render(request, 'orders/inquiry_create.html', {
        'contact': contact,
        'form': form,
        'formset': formset
    })


# ==================== 我的订单列表 ====================
@login_required
def order_list(request):
    """我的订单列表"""
    try:
        contact = Contact.objects.get(user=request.user)
    except Contact.DoesNotExist:
        messages.error(request, _('未找到联系人信息。'))
        return redirect('home')
    # 买家可见范围：同公司内的所有订单
    orders = Order.objects.filter(contact__company=contact.company).prefetch_related('items', 'attachments').order_by('-created_at')

    # 检索：订单号、产品名称、客户订单号
    q = (request.GET.get('q') or '').strip()
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(items__product_name__icontains=q) |
            Q(customer_order_number__icontains=q)
        ).distinct()

    return render(request, 'orders/order_list.html', {
        'contact': contact,
        'orders': orders,
        'q': q
    })


# ==================== 订单详情 ====================
@login_required
def order_detail(request, order_id):
    """订单详情页面"""
    try:
        contact = Contact.objects.get(user=request.user)
    except Contact.DoesNotExist:
        messages.error(request, _('未找到联系人信息。'))
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id, contact=contact)
    
    # 买家上传付款凭证（可选）
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload_payment_proof':
            try:
                file = request.FILES.get('payment_proof')
                if file:
                    OrderAttachment.objects.create(
                        order=order,
                        file=file,
                        file_name=file.name,
                        description='付款凭证',
                        uploaded_by=request.user
                    )
                    messages.success(request, _('付款凭证已上传。'))
                else:
                    messages.info(request, _('未选择文件，未上传。'))
            except Exception as e:
                messages.error(request, _('上传失败：%(error)s') % {'error': str(e)})
            return redirect('order_detail', order_id=order.id)
    
    return render(request, 'orders/order_detail.html', {
        'contact': contact,
        'order': order
    })


# ==================== 创建订单 ====================
@login_required
def order_create(request):
    """创建订单"""
    try:
        contact = Contact.objects.get(user=request.user)
    except Contact.DoesNotExist:
        messages.error(request, _('未找到联系人信息。'))
        return redirect('home')
    
    # 获取可选的询单列表（已报价的询单）
    available_inquiries = Inquiry.objects.filter(
        contact=contact,
        status__in=['quoted', 'pending']  # 可以根据需要调整状态
    ).order_by('-created_at')
    
    if request.method == 'POST':
        inquiry_id = request.POST.get('inquiry_id')
        
        try:
            with transaction.atomic():
                # 生成订单号
                order_number = f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                
                # 创建订单
                # 合并备注：若提供了交货期（天），与客户备注合并保存
                delivery_days = (request.POST.get('delivery_requirement', '') or '').strip()
                customer_notes = request.POST.get('customer_notes', '')
                customer_order_number = (request.POST.get('customer_order_number', '') or '').strip()
                if delivery_days:
                    customer_notes = f"交货期（天）：{delivery_days}\n" + customer_notes
                
                order = Order.objects.create(
                    order_number=order_number,
                    customer_order_number=customer_order_number,
                    contact=contact,
                    inquiry_id=inquiry_id if inquiry_id else None,
                    customer_notes=customer_notes,
                    status='pending'
                )
                
                # 处理订单明细项
                items_data = {}
                for key, value in request.POST.items():
                    if key.startswith('items['):
                        # 解析 items[0][product_name] 格式的键
                        import re
                        match = re.match(r'items\[(\d+)\]\[(\w+)\]', key)
                        if match:
                            index, field = match.groups()
                            if index not in items_data:
                                items_data[index] = {}
                            items_data[index][field] = value
                
                # 创建订单明细项
                for index, item_data in items_data.items():
                    if item_data.get('product_name'):  # 确保有产品名称
                        OrderItem.objects.create(
                            order=order,
                            product_name=item_data.get('product_name', ''),
                            material_name=item_data.get('material_name', ''),
                            material_grade=item_data.get('material_grade', ''),
                            quantity=item_data.get('quantity', 0),
                            unit=item_data.get('unit', 'PCS'),
                            unit_price=item_data.get('unit_price', 0),
                            specifications=item_data.get('specifications', '')
                        )
                
                # 如果基于询单创建，更新询单状态
                if inquiry_id:
                    Inquiry.objects.filter(id=inquiry_id).update(status='ordered')
                
                messages.success(request, _('订单 %(order_number)s 创建成功！') % {'order_number': order_number})
                return redirect('order_detail', order_id=order.id)
                
        except Exception as e:
            messages.error(request, _('创建订单失败：%(error)s') % {'error': str(e)})
    
    return render(request, 'orders/order_create.html', {
        'contact': contact,
        'available_inquiries': available_inquiries
    })
