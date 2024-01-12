from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    Roles = (
        ('store_manager','Store manager'),
        ('senior_management','Senior management'),
        ('Stock_handler','Stock handler')
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

    def __str__(self):
        return self.name
    
    def count_routers(self):
        results = self.router_set.all().count()
        print(results)
        return results
    
    class Meta:
        verbose_name_plural = "categories"


class Router(models.Model):
    store = models.ForeignKey(Store,on_delete=models.SET_NULL,null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True)
    serial_number = models.CharField(max_length = 150, blank=True, null=True)
    emei =  models.CharField(max_length = 150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return self.emei

