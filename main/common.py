from main.models import User
from django.db.models import Q

def username_or_email_exists(username,email):
    return User.objects.filter(Q(username = username) | Q(email = email)).exists()