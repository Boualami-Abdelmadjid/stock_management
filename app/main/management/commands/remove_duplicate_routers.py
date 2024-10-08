from django.core.management.base import BaseCommand
from django.db.models import Count

from main.models import Router

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        duplicate_serial_numbers = Router.objects.values('serial_number').annotate(count=Count('id')).filter(count__gt=1)
        
        for duplicate_sn in duplicate_serial_numbers:
            routers = Router.objects.filter(serial_number=duplicate_sn['serial_number'])
            if routers.count() > 1:
                #Get the last router with that serial number, and remove the first ones
                first_router = routers.last()
                other_routers = routers.exclude(id=first_router.id)
                other_routers.delete()
