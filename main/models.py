from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.admin.models import LogEntry
from django.dispatch import receiver
from django.conf import settings

import boto3, logging
from datetime import date, datetime, time

logger = logging.getLogger(__file__)

# Create your models here.

class User(AbstractUser):
    Roles = (
        ('store_manager','Store manager'),
        ('senior_management','Senior management'),
        ('stock_handler','Stock handler')
    )
    email = models.CharField(max_length=50)
    role = models.CharField(choices=Roles,max_length=150,blank=True,null=True)
    store = models.ForeignKey('Store',null=True, on_delete=models.SET_NULL)

class Store(models.Model):
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    alert_on = models.IntegerField(default=50)
    
    def __str__(self):
        return self.name
    
    def count_routers(self):
        results = self.router_set.filter(deleted=False,status="in_stock").count()
        return results
    

class Category(models.Model):
    Types = (
        ('indoor','Indoor'),
        ('outdoor','Outdoor'),
    )

    name = models.CharField(max_length=150)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    type = models.CharField(choices = Types, max_length=150)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    deleted = models.BooleanField(default=False)
    alerted = models.BooleanField(default=False)
    alert_on = models.IntegerField(default=50)


    def __str__(self):
        return self.name
    
    def count_routers(self):
        results = self.router_set.filter(deleted=False,status="in_stock").count()
        return results
    
    class Meta:
        verbose_name_plural = "categories"


class Router(models.Model):
    STATUSES = (
        ('in_stock','In stock'),
        ('new_sale','New sale'),
        ('collected','Collected'),
        ('return','Return'),
        ('swap','Device swap')
    )
    store = models.ForeignKey(Store,on_delete=models.SET_NULL,null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True)
    serial_number = models.CharField(max_length = 150, blank=True, null=True)
    emei =  models.CharField(max_length = 150, blank=True, null=True)
    status = models.CharField(max_length=50,default=STATUSES[0][0], choices=STATUSES)
    reason = models.CharField(max_length=150, null=True,blank=True)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    shipped = models.BooleanField(default=False)


    def __str__(self):
        return self.serial_number
    

class Log(models.Model):
    INSTANCES_CHOICES = (
        ('router','Router'),
        ('category','Category')
    )
    ACTIONS_CHOICES = (
        ('add','Add'),
        ('edit','Edit'),
        ('delete','Delete'),
    )
    
    store = models.ForeignKey(Store,on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User,on_delete=models.SET_NULL, null=True)
    action = models.CharField(choices=ACTIONS_CHOICES, max_length=20)
    instance = models.CharField(choices=INSTANCES_CHOICES,max_length=20)
    serial_number = models.CharField(max_length=150,null=True,blank=True)
    category_name = models.CharField(max_length=150, null=True)
    instance_id = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + ' ' + self.action
    
class Monitoring(models.Model):
    store = models.ForeignKey(Store,on_delete=models.CASCADE)
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
    store = models.ForeignKey(Store,on_delete=models.SET_NULL,null=True)
    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    action = models.CharField(max_length=50,choices = ACTIONS)
    order_number = models.CharField(max_length=50,null=True,blank=True)
    shipped = models.BooleanField(default=False)
    router = models.ForeignKey(Router,on_delete=models.SET_NULL,null=True)
    router2 = models.ForeignKey(Router,on_delete=models.SET_NULL,null=True,related_name='imei2')
    reason = models.CharField(max_length=50,null=True,blank=True)
    comment = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

class Notification(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    date_sent = models.DateField(auto_now_add=True)
    
#This to receive a signal when the super user changes something from the admin console
@receiver(models.signals.post_save, sender = LogEntry)
def action_created(sender, instance, created, **kwargs):
    instance_type = None
    store = None
    action = None
    emei = None
    category_name = None
    instance_id = instance.object_id
    if 'router' in str(instance.content_type):
        instance_type = 'router'
        router = Router.objects.filter(id=instance_id).first()
        serial_number = router.serial_number
        store = router.store
    elif 'category' in str(instance.content_type):
        instance_type = 'category'
        category = Category.objects.filter(id=instance_id).first()
        category_name = category.name
        store = category.store
    if instance.action_flag == 1:
        action = 'add'
    elif instance.action_flag == 2:
        action = 'edit'
    elif instance.action_flag == 3:
        action = 'delete'
    if instance_type:
        Log.objects.create(store=store,user = instance.user,action=action,instance=instance_type,serial_number = serial_number,category_name=category_name,instance_id=instance_id)

    #action_flags:
    #add = 1 -- edit = 2 -- delete = 3


def send_email(emails,subject,body):
    try:
        #Change the region
        client = boto3.client('ses',region_name = 'eu-north-1',aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY,  aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY)
        source = 'Nduduzo.khawula32@gmail.com' 
        message = {"Subject":{"Data":subject},"Body":{"Text":{"Data":body }}}
        response = client.send_email(Source = source, Destination={"ToAddresses":emails}, Message=message)
        logger.debug(response)
    except Exception as e:
        logger.exception(e)

def today_midnight():
    return datetime.combine(date.today(), time.min) 

@receiver(models.signals.post_save, sender = Router)
def router_changed(sender, instance, created, **kwargs):
    store = instance.store
    emails = list(store.user_set.all().values_list('email',flat=True))
    #Stock level email
    if store.count_routers() < store.alert_on and not Notification.objects.filter(store=store,date_sent__gte=today_midnight()).exists():
        send_email(emails,'LOW STOCK LEVEL',f"You have {store.count_routers()} routers on your store")
        Notification.objects.create(store=store)    