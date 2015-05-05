import datetime
import utils

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.conf import settings

from managers import EmailConfirmationManager, PasswordResetManager
from signal_receivers import * # Makes sure signal receivers are registered on startup

EMAIL_UNIQUE = getattr(settings,'EMAIL_UNIQUE',True)
EMAIL_EXPIRATION_DAYS = getattr(settings,'EMAIL_CONFIRMATION_DAYS_VALID')
PASSWORD_RESET_EXPIRATION_DAYS = getattr(settings,'PASSWORD_RESET_DAYS_VALID')
# Overrides basic User with whatever custom model is in use.


# Create your models here.
class EmailAddress(models.Model):
    """
    A users email address.
    """
    user = models.ForeignKey(User,related_name='email_address')
    email = models.EmailField(unique=EMAIL_UNIQUE)
    verified = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'EmailAddresses'
        if not EMAIL_UNIQUE:
            unique_together = [('user','email')]

    def change(self,new_email):
        """
        Allow the user to change their email and send a confirmation email to new address.
        Assumes the email address has been validated by calling code.
        """
        with transaction.atomic():
            self.user.email = new_email
            self.user.save()
            self.email = new_email
            self.verified = False
            self.save()
            self.send_confirmation()

    def send_confirmation(self):
        confirmation = EmailConfirmation.create(self)
        confirmation.send()
        return confirmation

class EmailConfirmation(models.Model):
    email_address = models.ForeignKey(EmailAddress)
    time_created = models.DateTimeField(default=timezone.now)
    time_sent = models.DateTimeField(null=True)
    key = models.CharField(max_length=64,unique=True)

    # Use custom manager
    objects = EmailConfirmationManager()

    class Meta:
        verbose_name_plural = 'EmailConfirmations'

    @classmethod
    def create(cls, email_address):
        key = get_random_string(64).lower()
        return cls._default_manager.create(email_address=email_address,
                                           key=key)

    def key_expired(self):
        """
        Returns True if the key for this EmailConfirmation has expired.
        False if it is still valid
        """
        expiration_date = self.time_sent + datetime.timedelta(days=EMAIL_EXPIRATION_DAYS)
        return expiration_date <= timezone.now()

    def confirm_email(self,key):
        """
        Confirm the email up receiving the correct key. Returns True if email verified.
        """
        if not self.key_expired() and not self.email_address.verified and key == self.key:
            self.email_address.verified = True
            self.email_address.save()
            return True
        return False

    def send(self):
        context =  {
            'user':self.email_address.user,
            'domain': getattr(settings,'DOMAIN'),
            'site_name': getattr(settings,'SITE_NAME'),
            'username': self.email_address.user.username,
            'token': self.key,
            'protocol': getattr(settings,'DEFAULT_PROTOCOL')
        }
        context['url'] = getattr(settings,'ACTIVATION_URL').format(**context)
        from_email = getattr(settings,'FROM_EMAIL')
        utils.send_email(self.email_address.email,from_email,context,'activation_email_subject.txt'
                         ,'activation_email_body.txt')
        self.time_sent = timezone.now()
        self.save()


class PasswordReset(models.Model):
    user = models.ForeignKey(User)
    used = models.BooleanField(default=False)
    time_created = models.DateTimeField(default=timezone.now)
    time_sent = models.DateTimeField(null=True)
    key = models.CharField(max_length=64,unique=True)

    # Use custom manager
    objects = PasswordResetManager()

    class Meta:
        verbose_name_plural = 'PasswordResets'

    @classmethod
    def create(cls, user):
        key = get_random_string(64).lower()
        return cls._default_manager.create(user=user,
                                           key=key)

    def confirm(self,key):
        """Confirm the password reset. At this stage, generate a new token for the user"""
        if not self.key_expired() and key ==self.key and not self.used:
            with transaction.atomic():
                self.used = True
                self.save()
                # Delete users current token and make a new one
                Token.objects.filter(user=self.user).all().delete()
                token = Token.objects.create(user=self.user)
                token.save()
            return True
        return False

    def key_expired(self):
        """
        Returns True if the key for this PasswordReset has expired.
        False if it is still valid
        """
        expiration_date = self.time_sent + datetime.timedelta(days=PASSWORD_RESET_EXPIRATION_DAYS)
        return expiration_date <= timezone.now()



    def send(self):
        context =  {
            'user':self.user,
            'domain': getattr(settings,'DOMAIN'),
            'site_name': getattr(settings,'SITE_NAME'),
            'username': self.user.username,
            'token': self.key,
            'protocol': getattr(settings,'DEFAULT_PROTOCOL')
        }
        context['url'] = getattr(settings,'PASSWORD_RESET_CONFIRM_URL').format(**context)
        from_email = getattr(settings,'FROM_EMAIL')
        utils.send_email(self.user.email,from_email,context,'password_reset_email_subject.txt'
                         ,'password_reset_email_body.txt')
        self.time_sent = timezone.now()
        self.save()