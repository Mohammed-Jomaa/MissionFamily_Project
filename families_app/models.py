from django.db import models
import re
import bcrypt
from datetime import date

class UserManager(models.Manager):
    def user_validator(self, postdata):
        errors = {}
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

        first_name = postdata.get('registerFirstName', '').strip()
        last_name = postdata.get('registerLastName', '').strip()
        email = postdata.get('registerEmail', '').strip()
        password = postdata.get('registerPassword', '')
        repeat_password = postdata.get('registerRepeatPassword', '')
        birth_day = postdata.get('registerBirthDay', '')

        if len(first_name) < 2:
            errors['registerFirstName'] = "الاسم الأول يجب أن لا يقل عن حرفين"
        elif not first_name.isalpha():
            errors['registerFirstName'] = "الاسم الأول يجب أن يحتوي على أحرف فقط"

        if len(last_name) < 2:
            errors['registerLastName'] = "الاسم الأخير يجب أن لا يقل عن حرفين"
        elif not last_name.isalpha():
            errors['registerLastName'] = "الاسم الأخير يجب أن يحتوي على أحرف فقط"

        if not EMAIL_REGEX.match(email):
            errors['registerEmail'] = "بريد إلكتروني غير صالح"
        elif User.objects.filter(email=email).exists():
            errors['registerEmail'] = "هذا البريد الإلكتروني مسجل مسبقًا"

        if len(password) < 8:
            errors['registerPassword'] = "كلمة المرور يجب أن لا تقل عن 8 أحرف"

        if repeat_password != password:
            errors['registerRepeatPassword'] = "كلمتا المرور غير متطابقتين"

        if birth_day:
            try:
                birth_date = date.fromisoformat(birth_day)
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                if age < 18:
                    errors['registerBirthDay'] = "يجب أن يكون عمرك 18 سنة على الأقل"
            except ValueError:
                errors['registerBirthDay'] = "صيغة تاريخ الميلاد غير صحيحة"
        else:
            errors['registerBirthDay'] = "يرجى إدخال تاريخ الميلاد"

        return errors

    def login_validator(self, postdata):
        errors = {}
        email = postdata.get('loginEmail')
        password = postdata.get('loginPassword')
        if not email or not password:
            errors['login'] = "البريد الإلكتروني وكلمة المرور مطلوبة"
            return errors

        user = User.objects.filter(email=email).first()
        if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
            errors['login'] = "البريد الإلكتروني أو كلمة المرور غير صحيحة"
            return errors
        return errors

    def validate_admin_email(self, postdata):
        errors = {}
        email = postdata.get('email')
        if not email:
            errors['email'] = "البريد الإلكتروني مطلوب"
            return errors
        user = User.objects.filter(email=email).first()
        if not user:
            errors['email'] = "البريد الإلكتروني غير صحيح"
        return errors

    def child_validator(self, postdata):
        errors = {}
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        first_name = postdata.get('first_name', '').strip()
        last_name = postdata.get('last_name', '').strip()

        if len(first_name) < 2:
            errors['first_name'] = "الاسم الأول يجب أن لا يقل عن حرفين"
        elif not first_name.isalpha():
            errors['first_name'] = "الاسم الأول يجب أن يحتوي على أحرف فقط"

        if len(last_name) < 2:
            errors['last_name'] = "الاسم الأخير يجب أن لا يقل عن حرفين"
        elif not last_name.isalpha():
            errors['last_name'] = "الاسم الأخير يجب أن يحتوي على أحرف فقط"

        if not EMAIL_REGEX.match(postdata.get('email', '')):
            errors['email'] = "بريد إلكتروني غير صالح"
        elif User.objects.filter(email=postdata.get('email', '')).exists():
            errors['email'] = "هذا البريد الإلكتروني مسجل مسبقًا"

        if len(postdata.get('password', '')) < 8:
            errors['password'] = "كلمة المرور يجب أن لا تقل عن 8 أحرف"

        if postdata.get('repeatPassword') != postdata.get('password'):
            errors['repeatPassword'] = "كلمتا المرور غير متطابقتين"

        return errors


class TaskManager(models.Manager):
    def validate_task(self, postdata):
        errors = {}

        title = postdata.get('title', '').strip()
        due_date = postdata.get('due_date', '').strip()
        points_str = str(postdata.get('points', '')).strip()

        if len(title) < 2:
            errors['title'] = "عنوان المهمة يجب أن لا يقل عن حرفين"

        if due_date:
            try:
                from datetime import date
                due = date.fromisoformat(due_date)
                if due < date.today():
                    errors['due_date'] = "تاريخ الانتهاء لا يمكن أن يكون في الماضي"
            except ValueError:
                errors['due_date'] = "صيغة التاريخ غير صحيحة"

        if not points_str.isdigit():
            errors['points'] = "النقاط يجب أن تكون رقمًا صحيحًا"
        else:
            if int(points_str) <= 0:
                errors['points'] = "النقاط يجب أن تكون أكبر من صفر"

        return errors


class FamilyManager(models.Manager):
    def validate_family(self, postdata):
        errors = {}
        if len(postdata.get('familyName', '')) < 2:
            errors['familyName'] = "اسم العائلة يجب أن لا يقل عن حرفين"
        return errors


class RewardManager(models.Manager):
    def validate_rewards(self, postdata):
        errors = {}
        name = postdata.get('name', '').strip()
        points_str = postdata.get('points', '').strip()
        quantity_str = postdata.get('quantity', '').strip()

        if len(name) < 2:
            errors['name'] = "اسم الجائزة يجب أن لا يقل عن حرفين"

        if not points_str.isdigit():
            errors['points'] = "النقاط يجب أن تكون رقمًا صحيحًا"
        else:
            if int(points_str) <= 0:
                errors['points'] = "النقاط يجب أن تكون أكبر من صفر"

        if not quantity_str.isdigit():
            errors['quantity'] = "الكمية يجب أن تكون رقمًا صحيحًا"
        else:
            if int(quantity_str) <= 0:
                errors['quantity'] = "الكمية يجب أن تكون أكبر من صفر"

        return errors


# ====== MODELS ======

class User(models.Model):
    ROLE_CHOICES = (
        ('parent', 'Parent'),
        ('child', 'Child'),
    )
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    email = models.EmailField(unique=True)
    birth_day = models.DateField()
    password = models.CharField(max_length=60)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='child')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()


class Family(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_families')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = FamilyManager()


class FamilyMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    points = models.IntegerField(default=10)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = TaskManager()

    @property
    def is_closed(self):
        """يرجع True إذا انتهى موعد المهمة (مقفلة عن التسليم)."""
        if not self.due_date:
            return False
        return self.due_date < date.today()


class TaskSubmission(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    child = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'child'})
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(null=True, default=None)

    @property
    def is_late(self):
        """يرجع True إذا تم التسليم بعد موعد المهمة."""
        if not self.task.due_date:
            return False
        return self.submitted_at.date() > self.task.due_date


class SubmissionFile(models.Model):
    submission = models.ForeignKey(TaskSubmission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='task_proofs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Reward(models.Model):
    title = models.CharField(max_length=100)
    points_cost = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)  # عدد مرات الاستبدال المتاحة
    image = models.ImageField(upload_to='rewards/', null=True, blank=True)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = RewardManager()


class PointsTransaction(models.Model):
    child = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'child'})
    points = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class ClaimedReward(models.Model):
    child = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'child'})
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True)
    claimed_at = models.DateTimeField(auto_now_add=True)