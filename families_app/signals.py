import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import SubmissionFile, Reward


@receiver(post_delete, sender=SubmissionFile)
def delete_submission_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)


@receiver(post_delete, sender=Reward)
def delete_reward_image(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)
