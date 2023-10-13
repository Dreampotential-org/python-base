import os
import uuid
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.dispatch import receiver
from sfapp2.utils import email_utils
from django.core.mail import send_mail
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django_rest_passwordreset.signals import reset_password_token_created
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    # Link to password reset page
    SERVER_URL = "https://teacher-v2.dreampotential.org"
    # SERVER_URL = "http://localhost:8084"

    reset_url = "{}/CreatePassword?token={}".format(SERVER_URL, reset_password_token.key)


    email_plaintext_message = f'''To reset your password, visit the following link: 

{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
'''

    email_utils.send_email(
        reset_password_token.user.email,
        "Password Reset for {title}".format(title="Website title"),
        email_plaintext_message)

    return
    send_mail(
        # title:
        "Password Reset for {title}".format(title="Website title"),
        # message:
        email_plaintext_message,
        # from:
        settings.DEFAULT_FROM_EMAIL,
        # to:
        [reset_password_token.user.email]
    )

# class UserManager(BaseUserManager):
#     def create_user(self, email, password=None, username=None, phone=None, bio=None, photo=None):
#         """
#         Creates and saves a User with the given email and password.
#         """
#         if not email:
#             raise ValueError('Users must have an email address')

#         user = self.model(
#             email=self.normalize_email(email),
#             username=email,
#             phone=phone,
#             bio=bio,
#             photo=photo,
#         )

#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, password, username=None, phone=None, bio=None, photo=None):
#         """
#         Creates and saves a superuser with the given email and password.
#         """
#         if not email:
#             raise ValueError('Users must have an email address')

#         user = self.model(
#             email=self.normalize_email(email),
#             username=email,
#             phone=phone,
#             bio=bio,
#             photo=photo,
#         )
#         user.set_password(password)

#         user.is_admin = True
#         user.save(using=self._db)
#         return user


# class UserCoustom(AbstractBaseUser):
#     email = models.EmailField(unique=True, blank=True, null=True)
#     username = models.EmailField(
#         unique=True, max_length=255, null=True, blank=True)
#     is_verified = models.BooleanField(default=False)
#     is_active = models.BooleanField(default=True)
#     is_admin = models.BooleanField(default=False)
#     phone = models.CharField(max_length=20, unique=True)
#     bio = models.CharField(max_length=255, blank=True, null=True)
#     photo = models.CharField(max_length=255, blank=True, null=True)
#     code_2fa = models.CharField(max_length=20, blank=True, null=True)
#     has_verified_phone = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now=True)

#     REQUIRED_FIELDS = ["email", "phone"]
#     USERNAME_FIELD = 'email'
#     objects = UserManager()

#     @property
#     def is_staff(self):
#         "Is the user a member of staff?"
#         # Simplest possible answer: All admins are staff
#         return self.is_admin

#     def has_module_perms(self, app_label):
#         "Does the user have permissions to view the app `app_label`?"
#         # Simplest possible answer: Yes, always
#         return True

#     def has_perm(self, perm, obj=None):
#         "Does the user have a specific permission?"
#         # Simplest possible answer: Yes, always
#         return True

#     def get_short_name(self):
#         # The user is identified by their email address
#         return self.email

class UserProfile(models.Model):
    image = models.CharField(max_length=500,null = True, blank = True,
                        default='https://cdn.icon-icons.com/icons2/2643/PNG/512/male_boy_person_people_avatar_icon_159358.png')

    modified_at = models.DateTimeField(auto_now= True)
    phone_number = models.CharField(max_length=13,null = True, blank = True, default='+910000000000')
    about = models.CharField(max_length=1000, blank=True, default='Available') 
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True, blank=True,
                            related_name='user_profile')

    class Meta:
        unique_together = ('user', 'phone_number')
    def __str__(self) -> str:
        return f"-{self.user}-{self.id}-"
