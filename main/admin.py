from django.contrib import admin
from main.models import *
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email','store','role')

class StoreAdmin(admin.ModelAdmin):
    list_display=('name','created_at','count_routers')

class CategoryAdmin(admin.ModelAdmin):
    list_display=('name','type','store','count_routers','deleted','alerted','created_at')
    list_editable = ('deleted',)

class RouterAdmin(admin.ModelAdmin):
    list_display=('store','category','status','emei','serial_number','deleted','created_at')
    search_fields = ('store__name','email','serial_number')
    list_editable = ('deleted',)

class NotificationAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Notification._meta.get_fields()]


class LogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Log._meta.get_fields()]

class MonitoringAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Monitoring._meta.get_fields()]

class ActionAdmin(admin.ModelAdmin):
   list_display = [field.name for field in Action._meta.get_fields()] 

admin.site.register(User,UserAdmin)
admin.site.register(Store,StoreAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(Router,RouterAdmin)
admin.site.register(Log,LogAdmin)
admin.site.register(Monitoring,MonitoringAdmin)
admin.site.register(Action,ActionAdmin)
admin.site.register(Notification,NotificationAdmin)
