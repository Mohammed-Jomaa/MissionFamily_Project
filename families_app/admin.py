from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(Family)
admin.site.register(FamilyMember)
admin.site.register(Task)
admin.site.register(TaskSubmission)
admin.site.register(Reward)
admin.site.register(PointsTransaction)
admin.site.register(ClaimedReward)
admin.site.register(SubmissionFile)
