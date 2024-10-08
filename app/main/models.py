import logging
from datetime import date, datetime, time


from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


logger = logging.getLogger(__file__)
store_table = 'main.Store'

class User(AbstractUser):
    Roles = (
        ('store_manager', 'Store manager'),
        ('senior_management', 'Senior management'),
        ('store_assistant', 'Store Assistant'),
    )
    email = models.CharField(max_length=50)
    role = models.CharField(choices=Roles, max_length=150, blank=True, default=Roles[0][0])
    store = models.ForeignKey(store_table, null=True, on_delete=models.SET_NULL)


class Category(models.Model):
    Types = (
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
    )

    name = models.CharField(max_length=150)
    type = models.CharField(choices=Types, max_length=150)
    store = models.ForeignKey(store_table, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    deleted = models.BooleanField(default=False)
    alerted = models.BooleanField(default=False)
    alert_on = models.IntegerField(default=50)

    def __str__(self):
        return self.name

    def count_routers(self):
        results = self.router_set.filter(deleted=False, status="in_stock").count()
        return results

    class Meta:
        verbose_name_plural = "categories"


class Log(models.Model):
    INSTANCES_CHOICES = (
        ('router', 'Router'),
        ('category', 'Category'),
    )
    ACTIONS_CHOICES = (
        ('add', 'Add'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('transfer', 'Transfer'),
    )

    store = models.ForeignKey(store_table, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(choices=ACTIONS_CHOICES, max_length=20)
    instance = models.CharField(choices=INSTANCES_CHOICES, max_length=20)
    serial_number = models.CharField(max_length=150, blank=True, default="")
    category_name = models.CharField(max_length=150, blank=True, default="")
    instance_id = models.IntegerField(null=True)
    old_store = models.ForeignKey(store_table, on_delete=models.SET_NULL, null=True, related_name='old_store')
    new_store = models.ForeignKey(store_table, on_delete=models.SET_NULL, null=True, related_name='new_store')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + ' ' + self.action


class Store(models.Model):
    name = models.CharField(max_length=150, blank=True, default="")
    name_full = models.CharField(max_length=150, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    alert_on = models.IntegerField(default=50)

    def __str__(self):
        return self.name_full or self.name

    def count_routers(self):
        results = self.router_set.filter(deleted=False, status="in_stock").count()
        return results


class Router(models.Model):
    STATUSES = (
        ('in_stock', 'In-Stock'),
        ('new_sale', 'New sale'),
        ('collected', 'Collected'),
        ('onboarded', 'Onboarded'),
        ('swap', 'Device swap'),
        ('returned', 'Returned'),
        ('to_refurb', 'To-Refurb'),
        ('Internal use', 'Out-of-stock(Internal use)')
    )

    EVENT_TYPES = (
        ('received', 'Received'),
        ('new_sale', 'New Sale'),
        ('collection', 'Collection'),
        ('swop_out', 'Swop-Out'),
        ('return', 'Return'),
        ('transfer', 'Transfer'),
        ('returned_CCD', 'Returned CCD'),
        ('internal_dist', 'Internal Distribution'),
    )

    store = models.ForeignKey(store_table, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey('main.Category', on_delete=models.SET_NULL, null=True)
    serial_number = models.CharField(max_length=150, unique=True)
    emei = models.CharField(max_length=150, blank=True, default="")
    status = models.CharField(max_length=50, default=STATUSES[0][0], choices=STATUSES)
    reason = models.CharField(max_length=150, blank=True, default="")
    deleted = models.BooleanField(default=False)
    shipped = models.BooleanField(default=False)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, blank=True, default="")
    meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.serial_number


class Monitoring(models.Model):
    store = models.ForeignKey(store_table, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    routers = models.IntegerField(default=0)
    day = models.DateField(auto_now=True)

    def __str__(self):
        return str(self.day)+' '+self.category.name


class Action(models.Model):
    ACTIONS = (
        ('collect','Collect'),
        ('sale','Sale'),
        ('return','Return'),
        ('swap','Device swap')
    )
    store = models.ForeignKey(store_table, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=50,choices = ACTIONS)
    order_number = models.CharField(max_length=50, blank=True, default="")
    shipped = models.BooleanField(default=False)
    router = models.ForeignKey('main.Router', on_delete=models.SET_NULL, null=True)
    router2 = models.ForeignKey('main.Router', on_delete=models.SET_NULL, null=True, related_name='imei2')
    reason = models.CharField(max_length=50, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True,null=True)


class Notification(models.Model):
    store = models.ForeignKey(store_table, on_delete=models.CASCADE)
    date_sent = models.DateField(auto_now_add=True)


class FailedUploads(models.Model):
    STATUSES = (
        ('in_stock', 'In-Stock'),
        ('onboarded', 'Onboarded'),
        ('returned', 'Returned'),
        ('to_refurb', 'To-Refurb'),
    )

    EVENT_TYPES = (
        ('received', 'Received'),
        ('new_sale', 'New Sale'),
        ('collection', 'Collection'),
        ('swop_out', 'Swop-Out'),
        ('return', 'Return'),
        ('transfer', 'Transfer'),
        ('returned_CCD', 'Returned CCD'),
        ('internal_dist', 'Internal Distribution'),
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, blank=True, default="")
    serial_number = models.CharField(max_length=150, blank=True, default="")
    status_from = models.CharField(max_length=50, default=STATUSES[0][0],
                              choices=STATUSES)
    status_to = models.CharField(max_length=50, default=STATUSES[0][0],
                                 choices=STATUSES)
    message = models.CharField(max_length=150, blank=True, default="")

    def __str__(self):
        return str(self.event_type) + '_' + str(self.created_at)


def today_midnight():
    return datetime.combine(date.today(), time.min)

