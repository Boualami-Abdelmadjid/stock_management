from django import template
from main.models import User, Router
register = template.Library()


@register.simple_tag
def get_correct_role(value):
    roles = User.Roles
    correct_role = value
    for role in roles:
        if role[0] == correct_role:
            correct_role = role[1]
            break
    return correct_role

@register.simple_tag
def get_correct_status(value):
    statuses = Router.STATUSES
    correct_status = value
    for status in statuses:
        if status[0] == correct_status:
            correct_status = status[1]
            break
    return correct_status
    
