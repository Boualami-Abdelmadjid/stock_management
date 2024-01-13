from datetime import date, datetime, time

from django.db.models import Q

from main.models import *


import logging
logger = logging.getLogger(__name__)

def username_or_email_exists(username,email):
    return User.objects.filter(Q(username = username) | Q(email = email)).exists()

def create_monitoring():
    try:
        stores = Store.objects.all()
        today = date.today()
        min_today_time = datetime.combine(today, time.min) 
        for store in stores:
            try:
                #calculate number of routers per category
                categories = Category.objects.filter(store=store)
                for category in categories:
                    try:
                        routers = category.count_routers()
                        monitor,created = Monitoring.objects.get_or_create(store=store,category=category,day__gte=min_today_time)
                        monitor.routers=routers
                        monitor.save()
                    except Exception as e:
                        logger.exception(e)
            except Exception as e:
                logger.exception(e)
    except Exception as e:
        logger.exception(e)