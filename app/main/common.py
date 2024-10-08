import json
import logging
from datetime import date, datetime, time


from django.db.models import Q


from main.models import Router, Store, User, Category, Monitoring


logger = logging.getLogger(__name__)


def username_or_email_exists(username, email):
    return User.objects.filter(Q(username=username) | Q(email=email)).exists()


def create_monitoring():
    try:
        stores = Store.objects.all()
        today = date.today()
        min_today_time = datetime.combine(today, time.min)
        for store in stores:
            try:
                # calculate number of routers per category
                categories = Category.objects.filter(store=store)
                for category in categories:
                    try:
                        routers = category.count_routers()
                        monitor, _ = Monitoring.objects.get_or_create(
                            store=store, category=category, day__gte=min_today_time
                        )
                        monitor.routers = routers
                        monitor.save()
                    except Exception as e:
                        logger.exception(e)
            except Exception as e:
                logger.exception(e)
    except Exception as e:
        logger.exception(e)


def create_alerts():
    categories = Category.objects.filter(alerted=False)
    for category in categories:
        count = category.count_routers()
        if count < category.alert_on:
            # TODO: Impelment Real alerts
            print("low stock")
            category.alerted = True
            category.save()


def today_midnight():
    return datetime.combine(date.today(), time.min)


def check_routers(request, response):
    routers = json.loads(request.body)
    new_routers = []
    wrong_status = []
    wrong_stores = []
    fails = []

    for router in routers:
        router_res = {}
        try:
            db_router = Router.objects.filter(
                serial_number=router.get("serial_number")
            ).first()
            router_res["serial_number"] = router.get("serial_number")

            if db_router:
                check_existing_router(
                    request, router, router_res, db_router, wrong_status, wrong_stores
                )
            else:
                check_unexisting_router(router_res, router, new_routers)

            if not router_res["success"]:
                fails.append(router.get("serial_number"))
            response["results"].append(router_res)

        except Exception as e:
            logger.exception(e)

    response["fails"] = fails
    response["wrong_stores"] = wrong_stores
    response["new_routers"] = new_routers
    response["wrong_status"] = wrong_status


def check_existing_router(
    request, router, router_res, db_router, wrong_status, wrong_stores
):
    router_res["exists"] = True
    router_res["in_stock"] = db_router.status == "in_stock"
    router_res["correct_store"] = db_router.store == request.user.store
    router_res["status"] = db_router.status
    router_res["belong_to"] = db_router.store.name
    router_res["success"] = router_res["in_stock"] and router_res["correct_store"]
    if not router_res["in_stock"]:
        wrong_status.append(
            {
                "serial_number": router.get("serial_number"),
                "status": router_res["status"],
            }
        )
    if not router_res["correct_store"]:
        wrong_stores.append(
            {
                "serial_number": router.get("serial_number"),
                "belong_to": router_res["belong_to"],
            }
        )


def check_unexisting_router(router_res, router, new_routers):
    router_res["exists"] = False
    router_res["in_stock"] = False
    router_res["correct_store"] = False
    router_res["status"] = None
    router_res["belong_to"] = None
    router_res["success"] = False
    new_routers.append(router.get("serial_number"))


def check_missing_routers(request, response):
    routers = json.loads(request.body)
    serial_numbers = [router.get("serial_number") for router in routers]
    store_routers = list(
        Router.objects.filter(
            store=request.user.store, status=Router.STATUSES[0][0]
        ).values_list("serial_number", flat=True)
    )
    missing_routers = [
        serial_number
        for serial_number in store_routers
        if serial_number not in serial_numbers
    ]
    response["missing_routers"] = missing_routers
