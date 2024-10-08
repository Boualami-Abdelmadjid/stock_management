from django.contrib.admin.models import LogEntry
from django.db import models
from django.dispatch import receiver

from main.models import Router, Category, Log, Notification, today_midnight


# This to receive a signal when the super user changes something from the admin console
@receiver(models.signals.post_save, sender=LogEntry)
def action_created(sender, instance, created, **kwargs):
    instance_type = None
    store = None
    action = None
    category_name = None
    instance_id = instance.object_id
    serial_number = None
    if 'router' in str(instance.content_type):
        instance_type = 'router'
        router = Router.objects.filter(id=instance_id).first()
        serial_number = router.serial_number
        store = router.store
    elif 'category' in str(instance.content_type):
        instance_type = 'category'
        category = Category.objects.filter(id=instance_id).first()
        category_name = category.name
    if instance.action_flag == 1:
        action = 'add'
    elif instance.action_flag == 2:
        action = 'edit'
    elif instance.action_flag == 3:
        action = 'delete'
    if instance_type:
        Log.objects.create(store=store, user=instance.user, action=action,
                           instance=instance_type,
                           serial_number=serial_number,
                           category_name=category_name,
                           instance_id=instance_id)

    # action_flags:
    # add = 1 -- edit = 2 -- delete = 3


@receiver(models.signals.post_save, sender=Router)
def router_changed(sender, instance, created, **kwargs):
    store = instance.store
    if store:
        # emails = list(store.user_set.all().values_list('email', flat=True))
        # Stock level email
        if store.count_routers() < store.alert_on and not Notification.objects.filter(store=store,
                                                                                      date_sent__gte=today_midnight()).exists():
            # TODO add notification email functionality
            Notification.objects.create(store=store)
