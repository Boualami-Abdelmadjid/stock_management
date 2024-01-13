from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.admin.models import LogEntry
from django.dispatch import receiver


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
    
    def __str__(self):
        return self.name

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


    def __str__(self):
        return self.name
    
    def count_routers(self):
        results = self.router_set.filter(deleted=False).count()
        return results
    
    class Meta:
        verbose_name_plural = "categories"


class Router(models.Model):
    store = models.ForeignKey(Store,on_delete=models.SET_NULL,null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True)
    serial_number = models.CharField(max_length = 150, blank=True, null=True)
    emei =  models.CharField(max_length = 150, blank=True, null=True)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return self.emei
    

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
    emei = models.CharField(max_length=150,null=True,blank=True)
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
        emei = router.emei
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
        Log.objects.create(store=store,user = instance.user,action=action,instance=instance_type,emei = emei,category_name=category_name,instance_id=instance_id)

    #action_flags:
    #add = 1 -- edit = 2 -- delete = 3




