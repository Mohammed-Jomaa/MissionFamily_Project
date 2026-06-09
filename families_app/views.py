from django.shortcuts import render, redirect
from .models import *
from django.contrib import messages
import bcrypt
from django.http import JsonResponse
import json
from django.urls import reverse
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
import random


# ====== HELPERS ======

def get_current_user(request):
    if 'user_id' not in request.session:
        return None
    return get_object_or_404(User, id=request.session['user_id'])


# ====== AUTH ======

def index(request):
    return render(request, 'index.html')

def register(request):
    return render(request, 'register.html')

def login(request):
    return render(request, 'login.html')

def about(request):
    return render(request, 'about.html')

def logout(request):
    request.session.flush()
    return redirect('/')


def create_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        errors = User.objects.user_validator(data)
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        hashed_pw = bcrypt.hashpw(
            data['registerPassword'].encode(),
            bcrypt.gensalt()
        ).decode()

        user = User.objects.create(
            first_name=data['registerFirstName'],
            last_name=data['registerLastName'],
            email=data['registerEmail'],
            birth_day=data['registerBirthDay'],
            password=hashed_pw,
            role='parent'
        )

        request.session.cycle_key()
        request.session['name'] = f"{user.first_name} {user.last_name}"
        request.session['user_id'] = user.id
        return JsonResponse({'success': True, 'message': 'تم إنشاء الحساب بنجاح!'})

    return JsonResponse({'success': False, 'errors': {'general': 'طلب غير صالح'}})


def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        errors = User.objects.login_validator(data)
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        user = User.objects.filter(email=data['loginEmail']).first()
        request.session.cycle_key()
        request.session['name'] = f"{user.first_name} {user.last_name}"
        request.session['user_id'] = user.id

        if user.role == 'child':
            return JsonResponse({'success': True, 'redirect_url': '/child_dashboard'})

        return JsonResponse({'success': True, 'redirect_url': '/dashboard'})

    return JsonResponse({'success': False, 'errors': {'general': 'طلب غير صالح'}})


# ====== PARENT DASHBOARD ======

def dashboard(request):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    families = FamilyMember.objects.filter(user=user)
    return render(request, 'dashboard.html', {'families': families})


def new_family(request):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')
    return render(request, 'new_family.html')


def create_family(request):
    if request.method == 'POST':
        user = get_current_user(request)
        if not user or user.role != 'parent':
            return redirect('index')

        errors = Family.objects.validate_family(request.POST)
        if errors:
            for key, value in errors.items():
                messages.error(request, value)
            return render(request, 'new_family.html')

        family = Family.objects.create(
            name=request.POST['familyName'],
            owner=user
        )
        FamilyMember.objects.create(family=family, user=user)
        return redirect('dashboard')

    return redirect('dashboard')


def manage_family(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    family = get_object_or_404(Family, id=id)
    return render(request, 'manage_family.html', {'family': family})


def add_admin(request):
    if request.method == 'POST':
        user = get_current_user(request)
        if not user or user.role != 'parent':
            return redirect('index')

        family_id = request.POST['family_id']
        errors = User.objects.validate_admin_email(request.POST)
        if errors:
            for key, value in errors.items():
                messages.error(request, value)
            return redirect(reverse('manage_family', args=[family_id]))

        admin_user = User.objects.filter(email=request.POST['email']).first()
        family = get_object_or_404(Family, id=family_id)

        if FamilyMember.objects.filter(family=family, user=admin_user).exists():
            messages.warning(request, 'هذا المستخدم عضو بالفعل في العائلة')
        else:
            FamilyMember.objects.create(family=family, user=admin_user)
            messages.success(request, 'تمت إضافة المشرف بنجاح')

        return redirect(reverse('manage_family', args=[family_id]))

    return redirect('dashboard')


def delete_family(request):
    if request.method == 'POST':
        user = get_current_user(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'يجب تسجيل الدخول'})
        if user.role != 'parent':
            return JsonResponse({'success': False, 'error': 'غير مصرح'})

        family_id = request.POST.get('family_id')
        family = get_object_or_404(Family, id=family_id)

        if family.owner.id != user.id:
            return JsonResponse({'success': False, 'error': 'فقط صاحب العائلة يمكنه الحذف'})

        family.delete()
        return JsonResponse({'success': True, 'redirect_url': '/dashboard'})

    return JsonResponse({'success': False, 'error': 'طلب غير صالح'})


# ====== TASKS ======

def task_list(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    family = get_object_or_404(Family, id=id)
    tasks = Task.objects.filter(family=family)
    return render(request, 'tasks/task_list.html', {'family': family, 'tasks': tasks})


def add_task(request, id):
    user = get_current_user(request)
    if not user:
        return JsonResponse({'success': False, 'errors': {'general': 'غير مسموح'}})
    if user.role != 'parent':
        return redirect('index')

    family = get_object_or_404(Family, id=id)

    if request.method == 'POST':
        data = json.loads(request.body)
        errors = Task.objects.validate_task(data)
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        Task.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            due_date=data.get('due_date') or None,
            points=data.get('points'),
            family=family,
            created_by=user
        )
        return JsonResponse({'success': True, 'message': 'تمت إضافة المهمة بنجاح!'})

    return render(request, 'tasks/add_task.html', {'family': family})


def delete_task(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    if request.method == 'POST':
        task = get_object_or_404(Task, id=id)
        family_id = task.family.id
        task.delete()
        return redirect('task_list', id=family_id)

    return redirect('dashboard')


def review_tasks(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    family = get_object_or_404(Family, id=id)
    submissions = TaskSubmission.objects.filter(task__family=family).order_by('-submitted_at')
    return render(request, 'tasks/review_tasks.html', {'family': family, 'submissions': submissions})


def approve_submission(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    submission = get_object_or_404(TaskSubmission, id=id)
    submission.is_approved = True
    submission.save()

    task_points = submission.task.points or 0
    if task_points > 0:
        PointsTransaction.objects.create(
            child=submission.child,
            points=task_points
        )

    return redirect('review_tasks', id=submission.task.family.id)


def reject_submission(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    submission = get_object_or_404(TaskSubmission, id=id)
    submission.is_approved = False
    submission.save()
    return redirect('review_tasks', id=submission.task.family.id)


# ====== CHILDREN ======

def children(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    family = get_object_or_404(Family, id=id)
    children_members = FamilyMember.objects.filter(family=family, user__role='child')

    children_with_points = []
    for member in children_members:
        child = member.user
        total_points = PointsTransaction.objects.filter(child=child).aggregate(
            total=Sum('points')
        )['total'] or 0
        children_with_points.append({
            'child': child,
            'points': total_points
        })

    return render(request, 'children/children.html', {
        'family': family,
        'children_with_points': children_with_points
    })


def create_child(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    family = get_object_or_404(Family, id=id)
    return render(request, 'children/add_child.html', {'family': family})


def add_child(request, id):
    user = get_current_user(request)
    if not user:
        return JsonResponse({'success': False, 'errors': {'general': 'غير مصرح'}})
    if user.role != 'parent':
        return JsonResponse({'success': False, 'errors': {'general': 'غير مصرح'}})

    if request.method == 'POST':
        data = json.loads(request.body)
        errors = User.objects.child_validator(data)
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        hashed_pw = bcrypt.hashpw(
            data['password'].encode(),
            bcrypt.gensalt()
        ).decode()

        child = User.objects.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            birth_day=data['birth_day'],
            password=hashed_pw,
            role='child'
        )

        family = get_object_or_404(Family, id=id)
        FamilyMember.objects.create(user=child, family=family)
        return JsonResponse({'success': True, 'message': 'تم إضافة الطفل بنجاح!'})

    return JsonResponse({'success': False, 'errors': {'general': 'طلب غير صالح'}})


# ====== REWARDS ======

def rewards(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    family = get_object_or_404(Family, id=id)

    rewards_list = Reward.objects.filter(family=family).annotate(
        claimed_count=Count('claimedreward')
    )
    for reward in rewards_list:
        reward.remaining = reward.quantity - reward.claimed_count

    redemptions = ClaimedReward.objects.filter(
        reward__family=family
    ).select_related('child', 'reward').order_by('-claimed_at')

    return render(request, 'rewards/rewards.html', {
        'family': family,
        'rewards': rewards_list,
        'redemptions': redemptions,
    })


def create_reward(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    family = get_object_or_404(Family, id=id)
    return render(request, 'rewards/create_reward.html', {'family': family})


def add_reward(request, id):
    user = get_current_user(request)
    if not user:
        return JsonResponse({'success': False, 'errors': {'general': 'غير مصرح'}})
    if user.role != 'parent':
        return redirect('index')

    if request.method == 'POST':
        data = request.POST
        image = request.FILES.get('image')

        errors = Reward.objects.validate_rewards(data)
        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        Reward.objects.create(
            title=data['name'],
            points_cost=data['points'],
            quantity=data['quantity'],
            image=image,
            family=get_object_or_404(Family, id=id),
            created_by=user
        )
        return JsonResponse({'success': True, 'message': 'تمت إضافة الجائزة بنجاح!'})

    return JsonResponse({'success': False, 'errors': {'general': 'طلب غير صالح'}})


def delete_reward(request, id):
    user = get_current_user(request)
    if not user or user.role != 'parent':
        return redirect('index')

    if request.method == 'POST':
        reward = get_object_or_404(Reward, id=id)
        family_id = reward.family.id
        reward.delete()
        return redirect('rewards', id=family_id)

    return redirect('dashboard')


# ====== CHILD DASHBOARD ======

def child_dashboard(request):
    user = get_current_user(request)
    if not user or user.role != 'child':
        return redirect('index')

    family_member = FamilyMember.objects.filter(user=user).first()
    family = family_member.family
    tasks = Task.objects.filter(family=family)
    total_points = PointsTransaction.objects.filter(child=user).aggregate(
        total=Sum('points')
    )['total'] or 0

    # جلب الجوائز مع عدد مرات الاستبدال الفعلية
    rewards_list = Reward.objects.filter(family=family).annotate(
        claimed_count=Count('claimedreward')
    )
    for reward in rewards_list:
        reward.remaining = reward.quantity - reward.claimed_count

    # الجوائز التي استبدلها هذا الطفل تحديداً
    my_claimed_ids = ClaimedReward.objects.filter(child=user).values_list('reward_id', flat=True)

    return render(request, 'child_dashboard.html', {
        'user': user,
        'family': family,
        'tasks': tasks,
        'rewards': rewards_list,
        'points': {'points': total_points},
        'claimed_reward_ids': my_claimed_ids,
    })


def submit_task(request, id):
    user = get_current_user(request)
    if not user or user.role != 'child':
        return redirect('index')

    task = get_object_or_404(Task, id=id)

    # التحقق أن المهمة تخص عائلة الطفل
    family_member = FamilyMember.objects.filter(user=user).first()
    if not family_member or task.family != family_member.family:
        return redirect('child_dashboard')

    my_submission = TaskSubmission.objects.filter(task=task, child=user).first()
    return render(request, 'tasks/submit_proof.html', {
        'task': task,
        'my_submission': my_submission
    })


def submit_proof(request, task_id):
    user = get_current_user(request)
    if not user:
        return redirect('index')

    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)

        # منع الرفع بعد انتهاء الموعد (قفل صارم)
        if task.is_closed:
            messages.error(request, 'انتهى وقت هذه المهمة، لا يمكن إرسال إثبات.')
            return redirect('submit_task', id=task_id)

        files = request.FILES.getlist('proof')
        if not files:
            messages.error(request, 'يجب إرفاق ملف واحد على الأقل.')
            return redirect('submit_task', id=task_id)

        # فحص حجم كل ملف (الحد الأقصى 100 ميجا)
        MAX_SIZE = 100 * 1024 * 1024
        for f in files:
            if f.size > MAX_SIZE:
                messages.error(
                    request,
                    'الملف "%s" حجمه كبير جداً (%d ميجا). الحد الأقصى 100 ميجا.' % (f.name, f.size // (1024 * 1024))
                )
                return redirect('submit_task', id=task_id)

        # حذف أي تسليم مرفوض سابق (تُحذف ملفاته تلقائياً عبر CASCADE)
        TaskSubmission.objects.filter(task=task, child=user, is_approved=False).delete()

        submission = TaskSubmission.objects.create(
            task=task,
            child=user,
            is_approved=None
        )
        for f in files:
            SubmissionFile.objects.create(submission=submission, file=f)

        messages.warning(request, 'تم إرسال المهمة! بانتظار الموافقة.')
        return redirect('submit_task', id=task_id)

    return redirect('child_dashboard')


def claim_reward(request, id):
    user = get_current_user(request)
    if not user or user.role != 'child':
        return redirect('index')

    reward = get_object_or_404(Reward, id=id)

    # التحقق أن الجائزة تخص عائلة الطفل
    family_member = FamilyMember.objects.filter(user=user).first()
    if not family_member or reward.family != family_member.family:
        messages.error(request, "غير مصرح باستبدال هذه الجائزة.")
        return redirect('child_dashboard')

    # التحقق أن الطفل لم يستبدل هذه الجائزة من قبل
    if ClaimedReward.objects.filter(child=user, reward=reward).exists():
        messages.error(request, "لقد استبدلت هذه الجائزة مسبقاً.")
        return redirect('child_dashboard')

    # التحقق من الكمية المتبقية
    claimed_count = ClaimedReward.objects.filter(reward=reward).count()
    if claimed_count >= reward.quantity:
        messages.error(request, "عذراً، نفدت كمية هذه الجائزة.")
        return redirect('child_dashboard')

    # التحقق من النقاط
    total_points = PointsTransaction.objects.filter(child=user).aggregate(
        total=Sum('points')
    )['total'] or 0

    if total_points < reward.points_cost:
        messages.error(request, "ليس لديك نقاط كافية لاستبدال هذه المكافأة.")
        return redirect('child_dashboard')

    # خصم النقاط وتسجيل الاستبدال
    PointsTransaction.objects.create(child=user, points=-reward.points_cost)
    ClaimedReward.objects.create(child=user, reward=reward, family=family_member.family)

    messages.success(request, f"تم استبدال المكافأة: {reward.title} بنجاح!")
    return redirect('child_dashboard')


# ====== API ======

def motivation_api(request):
    quotes = [
        "أنت قادر على إنجاز أي شيء!",
        "كل مهمة تنجزها تُقرّبك من حلمك.",
        "أنت نجم المهام اليوم!",
        "القليل من الجهد يصنع فرقًا كبيرًا.",
        "هدفك واضح، وخطواتك ثابتة.",
        "لا تستسلم، أنت أقوى مما تظن.",
        "استخدامك للوقت صح = نجاح كبير!",
        "الإنجاز يبدأ بخطوة... وأنت بدأت!",
        "عملك مميز ويستحق التقدير.",
        "العبقرية تبدأ بالالتزام اليومي.",
        "كل مهمة تعلمك شيئًا جديدًا.",
        "أنت القائد في عائلتك اليوم!",
        "مهمة جديدة = فرصة جديدة للنجاح!",
        "السر في الاستمرار وليس الكمال.",
        "أنت تبني مستقبلًا مشرقًا الآن.",
        "كل نقطة تحصّلها، تُقرّبك من الجائزة!",
        "اجعل من كل يوم خطوة للنجاح.",
        "اغتنم وقتك… فأنت تصنع فرقًا!",
        "أنت تصمم قصة إنجازك بنفسك.",
        "المثابرة هي مفتاح كل إنجاز عظيم.",
    ]
    return JsonResponse({'quote': random.choice(quotes)})