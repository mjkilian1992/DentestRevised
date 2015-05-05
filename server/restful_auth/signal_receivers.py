__author__ = 'mkilian'

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Creates an AuthToken for a User after they are created. Lifted straight from REST framework"""
    if created:
        Token.objects.create(user=instance)