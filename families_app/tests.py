from django.test import TestCase

# Create your tests here.
"""
اختبارات مشروع بُناة المستقبل.
للتشغيل:  python manage.py test
ملاحظة: الاختبارات تنشئ قاعدة بيانات مؤقتة ولا تمسّ بياناتك الحقيقية.
"""
import json
import bcrypt
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from .models import (
    User, Family, FamilyMember, Task, TaskSubmission,
    SubmissionFile, Reward, PointsTransaction, ClaimedReward
)


# ============ أدوات مساعدة ============

def make_parent(email='parent@test.com'):
    pw = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()
    return User.objects.create(
        first_name='Abu', last_name='Test', email=email,
        birth_day='1985-01-01', password=pw, role='parent'
    )


def make_child(email='child@test.com'):
    pw = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()
    return User.objects.create(
        first_name='Walad', last_name='Test', email=email,
        birth_day='2012-01-01', password=pw, role='child'
    )


def add_points(child, pts):
    PointsTransaction.objects.create(child=child, points=pts)


# ============ 1) اختبارات الموديلات والـ properties ============

class ModelLogicTests(TestCase):

    def setUp(self):
        self.parent = make_parent()
        self.child = make_child()
        self.family = Family.objects.create(name='Test Fam', owner=self.parent)
        FamilyMember.objects.create(user=self.parent, family=self.family)
        FamilyMember.objects.create(user=self.child, family=self.family)

    def test_task_is_closed_future_date(self):
        """مهمة موعدها بالمستقبل = غير مقفلة"""
        t = Task.objects.create(title='Open', family=self.family,
                                created_by=self.parent, points=10,
                                due_date=date.today() + timedelta(days=3))
        self.assertFalse(t.is_closed)

    def test_task_is_closed_past_date(self):
        """مهمة فات موعدها = مقفلة"""
        t = Task.objects.create(title='Closed', family=self.family,
                                created_by=self.parent, points=10,
                                due_date=date.today() - timedelta(days=2))
        self.assertTrue(t.is_closed)

    def test_task_no_date_never_closed(self):
        """مهمة بدون موعد = لا تُقفل أبداً"""
        t = Task.objects.create(title='NoDate', family=self.family,
                                created_by=self.parent, points=5)
        self.assertFalse(t.is_closed)

    def test_submission_is_late(self):
        """تسليم بعد الموعد = متأخر"""
        t = Task.objects.create(title='X', family=self.family,
                                created_by=self.parent, points=10,
                                due_date=date.today() - timedelta(days=1))
        sub = TaskSubmission.objects.create(task=t, child=self.child, is_approved=None)
        self.assertTrue(sub.is_late)

    def test_submission_not_late(self):
        """تسليم قبل الموعد = في الوقت"""
        t = Task.objects.create(title='Y', family=self.family,
                                created_by=self.parent, points=10,
                                due_date=date.today() + timedelta(days=5))
        sub = TaskSubmission.objects.create(task=t, child=self.child, is_approved=None)
        self.assertFalse(sub.is_late)

    def test_points_aggregation(self):
        """مجموع النقاط يُحسب صح"""
        add_points(self.child, 30)
        add_points(self.child, 20)
        add_points(self.child, -10)
        total = sum(p.points for p in PointsTransaction.objects.filter(child=self.child))
        self.assertEqual(total, 40)

    def test_submission_files_relation(self):
        """عدة ملفات تُربط بتسليم واحد"""
        t = Task.objects.create(title='Z', family=self.family,
                                created_by=self.parent, points=10)
        sub = TaskSubmission.objects.create(task=t, child=self.child, is_approved=None)
        SubmissionFile.objects.create(submission=sub, file='task_proofs/a.mp4')
        SubmissionFile.objects.create(submission=sub, file='task_proofs/b.jpg')
        self.assertEqual(sub.files.count(), 2)


# ============ 2) اختبارات الـ Validators ============

class ValidatorTests(TestCase):

    def test_valid_user_passes(self):
        data = {
            'registerFirstName': 'Mohammed', 'registerLastName': 'Jomaa',
            'registerEmail': 'new@test.com', 'registerPassword': 'password123',
            'registerRepeatPassword': 'password123', 'registerBirthDay': '1990-01-01'
        }
        errors = User.objects.user_validator(data)
        self.assertEqual(errors, {})

    def test_short_password_fails(self):
        data = {
            'registerFirstName': 'Mohammed', 'registerLastName': 'Jomaa',
            'registerEmail': 'new@test.com', 'registerPassword': '123',
            'registerRepeatPassword': '123', 'registerBirthDay': '1990-01-01'
        }
        errors = User.objects.user_validator(data)
        self.assertIn('registerPassword', errors)

    def test_password_mismatch_fails(self):
        data = {
            'registerFirstName': 'Mohammed', 'registerLastName': 'Jomaa',
            'registerEmail': 'new@test.com', 'registerPassword': 'password123',
            'registerRepeatPassword': 'different', 'registerBirthDay': '1990-01-01'
        }
        errors = User.objects.user_validator(data)
        self.assertIn('registerRepeatPassword', errors)

    def test_underage_fails(self):
        data = {
            'registerFirstName': 'Mohammed', 'registerLastName': 'Jomaa',
            'registerEmail': 'new@test.com', 'registerPassword': 'password123',
            'registerRepeatPassword': 'password123', 'registerBirthDay': '2015-01-01'
        }
        errors = User.objects.user_validator(data)
        self.assertIn('registerBirthDay', errors)

    def test_task_validator_negative_points(self):
        errors = Task.objects.validate_task({'title': 'Task', 'points': '-5', 'due_date': ''})
        self.assertIn('points', errors)

    def test_task_validator_past_date(self):
        past = (date.today() - timedelta(days=3)).isoformat()
        errors = Task.objects.validate_task({'title': 'Task', 'points': '10', 'due_date': past})
        self.assertIn('due_date', errors)

    def test_reward_validator_quantity(self):
        errors = Reward.objects.validate_rewards({'name': 'Gift', 'points': '50', 'quantity': '0'})
        self.assertIn('quantity', errors)

    def test_reward_validator_valid(self):
        errors = Reward.objects.validate_rewards({'name': 'Gift', 'points': '50', 'quantity': '5'})
        self.assertEqual(errors, {})


# ============ 3) اختبارات الـ Views والتدفّق الكامل ============

class ViewFlowTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.parent = make_parent()
        self.child = make_child()
        self.family = Family.objects.create(name='Fam', owner=self.parent)
        FamilyMember.objects.create(user=self.parent, family=self.family)
        FamilyMember.objects.create(user=self.child, family=self.family)

    def login_as(self, user):
        session = self.client.session
        session['user_id'] = user.id
        session['name'] = f'{user.first_name} {user.last_name}'
        session.save()

    def test_dashboard_requires_login(self):
        """لوحة التحكم تتطلب تسجيل دخول"""
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)  # تحويل لـ index

    def test_parent_can_see_dashboard(self):
        self.login_as(self.parent)
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_child_cannot_access_parent_dashboard(self):
        """الطفل لا يدخل لوحة ولي الأمر"""
        self.login_as(self.child)
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_add_task(self):
        self.login_as(self.parent)
        resp = self.client.post(
            reverse('add_task', args=[self.family.id]),
            data=json.dumps({'title': 'Clean room', 'description': 'x',
                             'points': '20', 'due_date': ''}),
            content_type='application/json'
        )
        self.assertTrue(json.loads(resp.content)['success'])
        self.assertEqual(Task.objects.filter(family=self.family).count(), 1)

    def test_approve_gives_points(self):
        """الموافقة على مهمة تضيف نقاط للطفل"""
        task = Task.objects.create(title='T', family=self.family,
                                   created_by=self.parent, points=25)
        sub = TaskSubmission.objects.create(task=task, child=self.child, is_approved=None)
        self.login_as(self.parent)
        self.client.post(reverse('approve_submission', args=[sub.id]))
        total = sum(p.points for p in PointsTransaction.objects.filter(child=self.child))
        self.assertEqual(total, 25)

    def test_claim_reward_deducts_points(self):
        """استبدال جائزة يخصم النقاط"""
        add_points(self.child, 100)
        reward = Reward.objects.create(title='Toy', points_cost=60, quantity=5,
                                       family=self.family, created_by=self.parent)
        self.login_as(self.child)
        self.client.get(reverse('claim_reward', args=[reward.id]))
        total = sum(p.points for p in PointsTransaction.objects.filter(child=self.child))
        self.assertEqual(total, 40)  # 100 - 60
        self.assertEqual(ClaimedReward.objects.filter(child=self.child).count(), 1)

    def test_claim_reward_insufficient_points(self):
        """لا يمكن الاستبدال بنقاط غير كافية"""
        add_points(self.child, 10)
        reward = Reward.objects.create(title='Big', points_cost=100, quantity=5,
                                       family=self.family, created_by=self.parent)
        self.login_as(self.child)
        self.client.get(reverse('claim_reward', args=[reward.id]))
        self.assertEqual(ClaimedReward.objects.filter(child=self.child).count(), 0)

    def test_claim_reward_quantity_limit(self):
        """لا يمكن استبدال جائزة نفدت كميتها"""
        reward = Reward.objects.create(title='Limited', points_cost=10, quantity=1,
                                       family=self.family, created_by=self.parent)
        # طفل أول يستهلك الكمية
        other_child = make_child(email='other@test.com')
        FamilyMember.objects.create(user=other_child, family=self.family)
        ClaimedReward.objects.create(child=other_child, reward=reward, family=self.family)
        # الطفل الثاني يحاول
        add_points(self.child, 100)
        self.login_as(self.child)
        self.client.get(reverse('claim_reward', args=[reward.id]))
        self.assertEqual(ClaimedReward.objects.filter(child=self.child, reward=reward).count(), 0)

    def test_cannot_claim_twice(self):
        """لا يمكن استبدال نفس الجائزة مرتين"""
        add_points(self.child, 200)
        reward = Reward.objects.create(title='Once', points_cost=20, quantity=10,
                                       family=self.family, created_by=self.parent)
        self.login_as(self.child)
        self.client.get(reverse('claim_reward', args=[reward.id]))
        self.client.get(reverse('claim_reward', args=[reward.id]))  # محاولة ثانية
        self.assertEqual(ClaimedReward.objects.filter(child=self.child, reward=reward).count(), 1)