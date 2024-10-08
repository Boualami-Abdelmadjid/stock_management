# Best practice is to divide the imports
# First import Built-in methods
# Then import Django methods
# Last import custom method written by you

import logging
from datetime import timedelta

from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Sum, Case, When, IntegerField, Window, F
from django.db.models.functions import RowNumber
from django.shortcuts import render
from django.utils.timezone import make_aware
from django.views.generic import View

from main.common import *
from utilities import *

logger = logging.getLogger(__name__)


# Create your views here.

class HomePage(View):
    """
    A view to display the homepage, showing a limited number of categories and routers.
    """

    def get(self, req):
        """
        Handles GET requests to render the homepage with categories and routers.
        """
        context = {}
        user = req.user
        # Get up to 6 categories and routers from the user's store that are not marked as deleted 
        categories = Category.objects.filter()[:6]

        routers = RouterMaster.objects.filter(
            store_id=user.store
        ).annotate(
            rank=Window(
                expression=RowNumber(),
                partition_by=[F('serial_number')],
                order_by=F('created_at').desc()
            )
        ).filter(rank=1).filter(status='in_stock')[:6]
        # Determine if more than 5 categories or routers exist to control the display of a 'show more' button
        context['more_categories'] = len(categories) > 5
        context['more_routers'] = len(routers) > 5
        # Limit the displayed categories and routers to 5
        context['categories'] = categories[:5]
        context['routers'] = routers[:5]

        return render(req, 'main/other/homepage.html', context=context)


class SignupView(View):
    """
    A view to handle user sign-ups.
    """

    def get(self, req):
        """
        Handles GET requests to show the signup form.
        """
        return render(req, 'main/account/signup.html')

    def post(self, req):
        """
        Handles POST requests to register a new user.
        """
        res = {'status': 500, 'message': 'Something wrong hapenned'}
        try:
            body = json.loads(req.body)
            username = body.get('username')
            email = body.get('email')
            password1 = body.get('password1')
            password2 = body.get('password2')
            # Validate required fields
            if not all([username, email, password1, password2]):
                res['message'] = 'All fields are required'
            else:
                if password1 != password2:
                    res['message'] = 'Passwords do not match'
                elif len(password1) < 8:
                    res['message'] = 'The password is too short'
                elif username_or_email_exists(username, email):
                    res['message'] = 'Username or email already exists'
                else:
                    # Create and save the new user
                    user = User.objects.create(username=username, email=email)
                    # Later use set_password method, this method will hash the password of the user instead of leaving it in plain text (For security)
                    user.set_password(password1)
                    user.save()
                    res['status'] = 200
                    del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class LoginView(View):
    """
    A view to handle user login.
    """

    def get(self, req):
        """
        Handles GET requests to show the login form.
        """
        return render(req, 'main/account/login.html')

    def post(self, req):
        """
        Handles POST requests to authenticate and log in a user.
        """
        res = {'status': 500, 'message': 'Something wrong hapenned'}
        try:
            body = json.loads(req.body)
            username = body.get('username')
            password = body.get('password')
            if username and password:
                # Check if a user with the username or email provided exists
                user = authenticate(req, username=username, password=password)
                if not user:
                    # In case the user tried to login using his email, find the user and authenticate using the username of the found user
                    email_user = User.objects.filter(email=username).first()
                    if email_user:
                        user = authenticate(req, username=email_user.username, password=password)
                if user:
                    # When authenticated log the user in and we will redirect him to the homepage from the frontend
                    login(req, user)
                    res['status'] = 200
                    del res['message']
                else:
                    matched_user = User.objects.filter(Q(username=username) | Q(email=username))
                    if not matched_user:
                        res['message'] = ('Invalid username or email')
                    elif not matched_user[0].check_password(password):
                        res['message'] = ('Invalid password')
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class ProfileView(View):
    """
    A view to display and manage user profiles.
    """

    def get(self, req):
        """
        Handles GET requests to display the profile page.
        """
        context = {}
        user = req.user
        # Exclude the current user from the list of store users.
        store_users = list(req.user.store.user_set.all().exclude(id=user.id).values())
        context['store_users'] = store_users
        return render(req, 'main/account/profile.html', context=context)

    def post(self, req):
        """
        Handles POST requests to update user information.
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            # Check if the logged-in user has store_manager role
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res, status=res['status'])

            store = req.user.store
            body = json.loads(req.body)
            username = body.get('username')
            role = body.get('role')

            # Try fo find the user by username or email
            added_user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            if added_user:
                # Update the user's store and role accordingly.
                if added_user.store == store:
                    added_user.role = role
                    message = 'edited'
                else:
                    added_user.store = store
                    added_user.role = role
                    message = 'added'
                added_user.save()
                res['status'] = 200
                res['message'] = f'User {message} successfully'
            else:
                res['message'] = 'User not found'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])

    def put(self, req):
        """
        Handles PUT requests to update the alert threshold setting for a store.
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            body = json.loads(req.body)
            value = body.get('value')
            if value:
                store = req.user.store
                # Update the store's alert_on value with the new threshold
                store.alert_on = value
                store.save()
                res['status'] = 200
                res['message'] = 'Alert threshold edited successfully'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])

    def delete(self, req):
        """
        Handles DELETE requests to remove a user from a store.
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            # Ensure only users with store_manager role can perform this action
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res, status=res['status'])

            body = json.loads(req.body)
            user_id = body.get('id')

            # Attempt to find and delete the specified user.
            store_user = User.objects.filter(id=user_id).first()
            if store_user:
                # Remove the user from the store and clear their role
                store_user.role = None
                store_user.store = None
                store_user.save()
                res['status'] = 200
                res['message'] = 'User deleted successfully'
            else:
                res['message'] = "Can't find the user"
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class DashboardView(View):
    """
    Dashboard view to display various statistics and listings for the user's store, including routers,
    categories, employee actions, and monitoring stats.
    """

    def get(self, req):
        """
        Handles GET request to render the dashboard page with contextual data.
        """
        user = req.user
        check_other_stores = user.is_superuser and req.GET.get('store')
        store_exists = StoreMaster.objects.filter(id=req.GET.get('store')).exists()
        store = StoreMaster.objects.filter(
            id=req.GET.get('store')).first() if check_other_stores and store_exists else user.store
        query = req.GET
        context = {}
        # Define color scheme for graphical elements
        colors = ["#e58989", "#edcb8d", "#6868e5"]
        # Calculate the last 5 days for trend analysis
        days = list(reversed([today_midnight() - timedelta(days=x) for x in range(5)]))

        # Routers part
        # Process routers with optional filtering
        router_page = query.get('router_page') if query.get('router_page') else 1
        routers = Router.objects.filter(store=store, deleted=False).order_by('-id')
        # Apply filters based on query 
        emei = query.get('emei')
        serial = query.get('serial')
        category = query.get('router_category')
        router_type = query.get('router_type')
        status = query.get('status')
        if emei:
            routers = routers.filter(emei__icontains=emei)
        if serial:
            routers = routers.filter(serial_number__icontains=serial)
        if router_type:
            routers = routers.filter(category__type=router_type)
        if category:
            category_instance = Category.objects.filter(id=category).first()
            if category_instance:
                routers = routers.filter(category=category_instance)
        if status:
            routers = routers.filter(status=status)

        # Paginate routers listing
        router_paginator = Paginator(routers, 10)
        routers = router_paginator.page(router_page)
        context['statuses'] = Router.STATUSES
        context['routers_count'] = router_paginator.count
        context['routers_paginator'] = router_paginator.get_elided_page_range(number=router_page,
                                                                              on_each_side=1,
                                                                              on_ends=1)

        # Category page
        # Similar processing for categories with pagination.
        categories_page = query.get('categories_page') if query.get('categories_page') else 1
        categories = Category.objects.filter(store=store, deleted=False).order_by('-id')
        category_name = query.get('category_name')
        category_type = query.get('category_type')
        if category_name:
            categories = categories.filter(name__icontains=category_name)
        if category_type:
            categories = categories.filter(type=category_type)

        category_paginator = Paginator(categories, 10)
        categories = category_paginator.page(categories_page)
        context['categories_paginator'] = category_paginator.get_elided_page_range(number=categories_page,
                                                                                   on_each_side=1,
                                                                                   on_ends=1)

        # Employees part
        # Employee action logs processing.
        # This loop compiles actions taken by employees on routers over the last 5 days.
        employees = User.objects.filter(store=store)
        actions = ['add', 'edit', 'delete']
        for action in actions:
            context[action] = {}
            for emp_index, employee in enumerate(employees):
                obj = []
                for day_index, day in enumerate(days):
                    date_start = make_aware(day)
                    date_end = make_aware(day + timedelta(days=1))
                    logs = Log.objects.filter(store=store, user=employee, action=action, instance="router",
                                              created_at__gte=date_start, created_at__lt=date_end).count()
                    if logs:
                        obj.append(logs)
                    else:
                        obj.append(0)
                color = colors[emp_index % len(colors)]
                context[action][employee.username] = {'obj': obj, 'color': color + '33', 'border': color}

        # Monitors part
        # Monitor and display routers by category and overall store performance.
        context['monitors'] = []
        store_monitors = []

        # Routers per category section
        routers_categories = Category.objects.filter(store=store, deleted=False)

        # Iterate over each category in the routers_categories list with its index
        for index, category in enumerate(routers_categories):
            # Initialize an empty list to hold the data for the current category
            obj = []

            # Iterate over each day in the days list with its index
            for day_index, day in enumerate(days):
                # Special case for the fifth day (index 4, since indexing starts at 0)
                if day_index == 4:
                    obj.append(category.count_routers())
                else:
                    date_start = day
                    date_end = day + timedelta(days=1)
                    monitoring = Monitoring.objects.filter(store=store, category=category, day__gte=date_start,
                                                           day__lt=date_end).first()
                    if monitoring:
                        obj.append(monitoring.routers)
                    else:
                        default = 0
                        if day_index > 0:
                            default = obj[day_index - 1]
                        obj.append(default)
            color = colors[index % len(colors)]
            monitor_obj = {'label': category.name, 'values': obj, 'color': color + '33', 'border': color}

            context['monitors'].append(monitor_obj)

        # Routers by store section
        for day_index, day in enumerate(days):
            if day_index == 4:
                store_monitors.append(store.count_routers())
            else:
                date_start = day
                date_end = day + timedelta(days=1)
                condition1 = Q(store=store)
                condition2 = Q(day__gte=date_start)
                condition3 = Q(day__lt=date_end)

                condition = Case(
                    When(condition1 & condition2 & condition3, then=F('routers')),
                    default=0,
                    output_field=IntegerField()
                )
                result = Monitoring.objects.aggregate(total=Sum(condition))
                total = result.get('total')
                # When there is no entry for this date, and index > 1, keep the same amount of routers of yesterday for today
                if not total and day_index > 0 and not Monitoring.objects.filter(store=store, day__gte=date_start,
                                                                                 day__lt=date_end):
                    total = store_monitors[day_index - 1]

                store_monitors.append(total)

        context['stores'] = StoreMaster.objects.all()
        context['store'] = store
        context['routers'] = routers
        context['categories_obj'] = categories
        context['categories'] = routers_categories
        context['action'] = actions
        context['store_monitors'] = store_monitors
        context['days'] = [day.strftime("%A") for day in days]
        return render(req, 'main/dashboard/index.html', context=context)


class CreateStoreView(View):
    """
    View for creating a new store.
    Handles GET requests to display the store creation form and POST requests to create a store.
    """

    def get(self, req):
        """
        Handle GET requests: Renders the store creation form.

        :param request: HttpRequest object
        :return: HttpResponse object with the rendered store creation form template
        """
        return render(req, 'main/store/create-store.html')

    def post(self, req):
        """
        Handle POST requests: Creates a new store with the provided name from the request.

        :param request: HttpRequest object containing the store name in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": "Something went wrong"}
        try:
            # We format the body of the request to a Python dictionary
            body = json.loads(req.body)

            # We retrieve the name from the body of the request
            name = body.get("name")
            full_name = body.get("full_name")
            print(full_name)
            # Create the store and save it to the database
            store = StoreMaster.objects.create(name=name, name_full=full_name)
            store.save()
            # Associate the created store to the user and assign him as the store manager
            user = req.user
            user.store = store
            user.role = 'store_manager'
            user.save()
            res['status'] = 200

            del res['message']  # Remove the error message on success
        except Exception as e:
            logger.exception(e)  # Log the exception for debugging purposes
        return JsonResponse(res, status=res['status'])


class CreateCategoryView(View):
    """
    View for creating a new category within a store.
    Handles GET requests to display the category creation form and POST requests to create a category.
    """

    def get(self, req):
        """
        Handle GET requests: Renders the category creation form.

        :param request: HttpRequest object
        :return: HttpResponse object with the rendered category creation form template
        """
        return render(req, 'main/category/create-category.html')

    def post(self, req):
        """
        Handle POST requests: Creates a new category for the store of the logged-in user.

        :param request: HttpRequest object containing the category name and type in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res, status=res['status'])
            user = req.user
            store = user.store
            # We format the body of the request to a Python dictionary
            body = json.loads(req.body)
            # We retrieve the name and type from the body of the request
            name = body.get("name")
            category_type = body.get('type')
            # Create the Category instance and save it to the database
            category = Category.objects.create(name=name, type=category_type, store=store)
            category.save()
            # Log the creation action
            Log.objects.create(user=user, store=store, instance='category', instance_id=category.id,
                               category_name=category.name, action='add')

            res['status'] = 200
            del res['message']  # Remove the error message on success
        except Exception as e:
            logger.exception(e)  # Log the exception for debugging purposes
        return JsonResponse(res, status=res['status'])


class CreateRouterView(View):
    """
    View for creating a new router within a store.
    Handles GET requests to display the router creation form and POST requests to create a router.
    """

    def __init__(self):
        self.action = 'received'
        self.status = 'in_stock'

    def get(self, req):
        """
        Handle GET requests: Renders the router creation form with available categories.

        :param request: HttpRequest object
        :return: HttpResponse object with the rendered router creation form template
        """
        context = {}
        store = req.user.store
        # Fetch categories that are not marked as deleted and belong to the user's store
        categories = list(Category.objects.filter(deleted=False).values())
        context['categories'] = categories
        return render(req, 'main/router/create-router.html', context=context)

    def post(self, req):
        """
        Handle POST requests: Creates a new router with the provided details from the request.

        :param request: HttpRequest object containing the router details in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": "Something went wrong."}
        try:
            if not valid_permissions(req.user):
                return JsonResponse({"status": 403, "message": "You don't have permissions."}, status=403)

            user = req.user
            store = user.store
            bodies = json.loads(req.body)
            failed_uploads = []

            for body in bodies:

                category = body.get('category')

                serial_number = body.get('serial_number')

                meta_json = {"agent": req.user.email, "action": self.action}

                category = Category.objects.filter(name=category).first()

                router_status_check = RouterMaster.objects.filter(store=store,
                                                                  serial_number=serial_number
                                                                  ).order_by('-updated_at').first()

                if (router_status_check is None or router_status_check.status == RouterMaster.STATUSES[3][0]):

                    message = ""

                    try:

                        # Create the router instance and save it to the database
                        router = RouterMaster.objects.create(store=store,
                                                             category=category,
                                                             serial_number=serial_number,
                                                             event_type=self.action,
                                                             status=self.status,
                                                             meta=meta_json)

                        router.save()

                    except:
                        body['message'] = "failed to write to database"
                        failed_upload = FailedUploads.objects.create(
                            event_type=self.action,
                            serial_number=serial_number,
                            status_from=router_status_check.status,
                            status_to=self.status,
                            message=message)

                        failed_uploads.append(body)

                else:

                    if router_status_check.status == RouterMaster.STATUSES[0][0]:
                        message = "Router already in-stock"
                    elif router_status_check.status == RouterMaster.STATUSES[1][0]:
                        message = "Router currently onboarded and assigned to customer"
                    elif router_status_check.status == RouterMaster.STATUSES[2][0]:
                        message = "Router returned by customer, bound for CCD"

                    failed_upload = FailedUploads.objects.create(event_type=self.action,
                                                                 serial_number=serial_number,
                                                                 status_from=router_status_check.status,
                                                                 status_to=self.status,
                                                                 message=message)
                    failed_upload.save()

                    failed_uploads.append(body)

            if len(failed_uploads) == 0:
                res['status'] = 200
                del res['message']

            else:
                res['status'] = 201
                res['message'] = 'Some router uploads failed'
                print(failed_uploads)

        except IntegrityError:
            res['message'] = 'Router already exists in the database'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class CreateRoutersView(View):
    """
    View for creating multiple routers routers within a store.
    """

    def get(self, req):
        """
        Handle GET requests: Renders the routers creation form with available categories.

        :param request: HttpRequest object
        :return: HttpResponse object with the rendered router creation form template
        """
        context = {}
        store = req.user.store
        # Fetch categories that are not marked as deleted and belong to the user's store
        categories = list(Category.objects.filter(store=store, deleted=False).values())
        context['categories'] = categories
        return render(req, 'main/router/bulk-create.html', context=context)

    def post(self, req):
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have permissions"
                return JsonResponse(res, status=res['status'])

            user = req.user
            store = user.store
            # We format the body of the request to a python object
            body = json.loads(req.body)
            # We retrieve the name from the body of the request
            serial_numbers = body.get('serial_numbers')
            logger.info(f'{len(serial_numbers)} serial numbers received')
            category = body.get('category')

            # Validate and fetch the category
            category = Category.objects.filter(id=category).first()
            for sn in serial_numbers:
                try:
                    router = Router.objects.create(store=store, category=category, serial_number=sn)
                    router.save()
                    Log.objects.create(user=user, store=store, instance='router', instance_id=router.id,
                                       serial_number=router.serial_number, action='add')
                except Exception as e:
                    logger.exception(e)

            # Reset the alerted flag for the category as a new router is adde
            category.alerted = False
            category.save()
            # Log the router addition

            res['status'] = 200
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class CategoryView(View):
    """
    View for editing and deleting categories within a store.
    Handles PUT requests to edit categories and DELETE requests to mark categories as deleted.
    """

    def put(self, req):
        """
        Handle PUT requests: Edits the details of an existing category.

        :param request: HttpRequest object containing the updated category details in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res, status=res['status'])

            body = json.loads(req.body)
            category_id = body.get('id')
            name = body.get('name')
            category_type = body.get('type')

            category = Category.objects.filter(id=category_id).first()
            if category:
                category.name = name
                category.type = category_type
                category.save()
                # Log the category edit action
                Log.objects.create(user=req.user,
                                   instance='category',
                                   instance_id=category.id,
                                   category_name=category.name,
                                   action='edit')
                res['status'] = 200
                res['message'] = 'Category edited successfully'

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])

    def delete(self, req):
        """
        Handle DELETE requests: Marks an existing category as deleted.

        :param request: HttpRequest object containing the category ID to be deleted
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res, status=res['status'])
            body = json.loads(req.body)
            category_id = body.get('id')
            category = Category.objects.filter(id=category_id).first()
            if category:
                category.deleted = True
                category.save()
                # Log the category deletion
                Log.objects.create(user=req.user,
                                   instance='category',
                                   instance_id=category.id,
                                   category_name=category.name,
                                   action='delete')
                res['message'] = 'Category deleted successfully'
                res['status'] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class RouterView(View):
    """
    View for managing routers within a store.
    Supports GET for listing routers, POST for importing routers, PUT for editing router details,
    DELETE for marking routers as deleted, and PATCH for updating router shipment status.
    """

    def get(self, req):
        """
        Handle GET requests: Retrieves a list of routers associated with the user's store.

        :param request: HttpRequest object
        :return: JsonResponse object with a list of routers and operation status
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            user = req.user
            store = user.store
            # Fetch routers from the store, ordered by descending ID
            routers = list(Router.objects.filter(store=store).order_by("-id").values('id', 'category__name', 'emei',
                                                                                     'serial_number', 'created_at'))
            res['routers'] = routers
            del res['message']
            res['status'] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])

    def post(self, req):
        """
        Handle POST requests: Imports a batch of routers from the provided list.

        :param request: HttpRequest object containing the list of routers to be imported
        :return: JsonResponse object with the import operation status and message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            user = req.user
            body = json.loads(req.body)
            routers = body.get('routers')
            imported = 0  # Counter for successfully imported routers
            for new_router in routers:
                try:
                    category = Category.objects.filter(name=new_router.get('category')).first()
                    if category:
                        # Check if the router does not exist or is marked as deleted
                        if not Router.objects.filter(id=new_router.get('id')).exists():
                            if category:
                                router = Router.objects.create(store=user.store, category=category,
                                                               emei=new_router.get('emei'),
                                                               serial_number=new_router.get('serial_number'))
                                router.save()
                                Log.objects.create(user=user, store=user.store, instance='router',
                                                   instance_id=router.id, serial_number=router.serial_number,
                                                   action='add')
                                imported += 1

                        elif Router.objects.filter(id=new_router.get('id'), deleted=True).exists():
                            router = Router.objects.get(id=new_router.get('id'))
                            router.category = category
                            router.emei = new_router.get('emei')
                            router.serial_number = new_router.get('serial_number')
                            router.deleted = False
                            router.save()
                            Log.objects.create(user=user, store=user.store, instance='router', instance_id=router.id,
                                               serial_number=router.serial_number, action='add')
                            imported += 1
                    else:
                        logger.error(f"{new_router.get('category')} not found")


                except Exception as e:
                    logger.exception(e)
            res['status'] = 200
            res['message'] = f'{imported} routers imported'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])

    def put(self, req):
        """
        Handle PUT requests: Edits the details of an existing router.

        :param request: HttpRequest object containing the new details of the router
        :return: JsonResponse object with the edit operation status and message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res, status=res['status'])
            body = json.loads(req.body)
            router_id = body.get('id')
            category = body.get('category')
            serial_number = body.get('serial_number')
            emei = body.get('emei')
            status = body.get('status')

            category_instance = Category.objects.filter(id=category).first()
            router = Router.objects.filter(store=req.user.store, id=router_id).first()
            router.category = category_instance
            router.serial_number = serial_number
            router.emei = emei
            router.status = status
            router.save()
            Log.objects.create(user=req.user, store=req.user.store, instance='router', instance_id=router.id,
                               serial_number=router.serial_number, action='edit')
            res['status'] = 200
            res['message'] = 'Router edited successfully'

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])

    def delete(self, req):
        """
        Handle DELETE requests: Marks an existing router as deleted.

        :param request: HttpRequest object containing the ID of the router to be marked as deleted
        :return: JsonResponse object with the delete operation status and message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res, status=res['status'])
            body = json.loads(req.body)
            router_id = body.get('id')
            router = Router.objects.filter(store=req.user.store, id=router_id).first()
            if router:
                router.deleted = True
                router.save()
                Log.objects.create(user=req.user, store=req.user.store, instance='router', instance_id=router.id,
                                   serial_number=router.serial_number, action='delete')
                logger.info(
                    f'{req.user.username} deleted router with sn: {router.serial_number} - emei : {router.emei}')
                res['message'] = 'Router deleted successfully'
                res['status'] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])

    def patch(self, req):
        """
        Handle PATCH requests: Toggles the shipped status of a router.

        :param request: HttpRequest object containing the ID of the router to update its shipped status
        :return: JsonResponse object with the update operation status and message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            body = json.loads(req.body)
            router_id = body.get('id')
            if router_id:
                router = Router.objects.filter(store=req.user.store, id=router_id).first()
                if router:
                    router.shipped = not router.shipped
                    router.save()
                    res['message'] = 'Router updated successfully'
                    res['status'] = 200
                else:
                    res['message'] = 'Router is not in the Database'
                    res['status'] = 400

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class RouterSuggestions(View):
    """
    View for suggesting routers based on partial input for EMEI or serial number.
    """

    def get(self, req):
        """
        Handle GET requests to suggest routers matching the partial EMEI or serial number provided by the user.

        :param request: HttpRequest object containing the partial input in query parameters
        :return: JsonResponse with a list of matching routers or an error message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            user = req.user
            value = req.GET.get('value')
            # Filter routers by store, not deleted, and starting with the given value
            routers = list(Router.objects.filter(Q(store=user.store) & Q(deleted=False) & (
                        Q(emei__startswith=value) | Q(serial_number__startswith=value))).values('emei'))
            res['status'] = 200
            res['routers'] = routers
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class CategorySuggestions(View):
    """
    View for suggesting categories based on partial name input.
    """

    def get(self, req):
        """
        Handle GET requests to suggest categories matching the partial name provided by the user.

        :param request: HttpRequest object containing the partial input in query parameters
        :return: JsonResponse with a list of matching categories or an error message
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            user = req.user
            value = req.GET.get('value')
            # Filter categories by store, name starting with the given value, and not deleted
            categories = list(
                Category.objects.filter(store=user.store, name__startswith=value, deleted=False).values('name'))
            res['status'] = 200
            res['categories'] = categories
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class LogsView(View):
    """
    View for listing logs and actions associated with a user's store.
    Includes filtering and pagination functionality.
    """
    model = Log
    paginate_by = 20
    template_name = "main/logs/list.html"

    def get(self, request):
        user = request.user
        logs = Log.objects.filter(store=user.store).order_by('-id')
        actions = Action.objects.filter(store=user.store).order_by('-id')
        context = {}
        query = self.request.GET
        context['users'] = User.objects.filter(Q(store=request.user.store) | Q(is_superuser=True))
        try:
            logs_page = query.get('logs_page') if query.get('logs_page') else 1
            emei = query.get('emei')
            searched_user = query.get('user')
            action = query.get('action')
            instance = query.get('instance')
            if emei:
                logs = logs.filter(Q(emei__icontains=emei) | Q(category_name__icontains=emei))
            if searched_user:
                searched_user_instance = User.objects.filter(store=user.store, id=searched_user).first()
                if searched_user:
                    logs = logs.filter(user=searched_user_instance)
                else:
                    logs = logs.none()
            if action:
                logs = logs.filter(action=action)
            if instance:
                logs = logs.filter(instance=instance)
            logs_paginator = Paginator(logs, 10)
            logs = logs_paginator.page(logs_page)
            context['logs'] = logs
            context['logs_obj'] = logs_paginator.get_elided_page_range(number=logs_page,
                                                                       on_each_side=1,
                                                                       on_ends=1)

        except Exception as e:
            logger.exception(e)

        try:
            actions_page = query.get('actions_page') if query.get('actions_page') else 1
            router1 = query.get('action_router1')
            action = query.get('action_action')
            action_reason = query.get('action_reason')
            searched_user = query.get('action_user')

            if router1:
                actions = actions.filter(router1=Router.objects.filter(emei=router1).first())

            if searched_user:
                searched_user_instance = User.objects.filter(store=user.store, id=searched_user).first()
                if searched_user:
                    actions = actions.filter(user=searched_user_instance)
                else:
                    actions = actions.none()

            if action:
                actions = actions.filter(action=action)

            if action_reason:
                actions = actions.filter(reason=action_reason)

            actions_paginator = Paginator(actions, 10)
            actions = actions_paginator.page(actions_page)
            context['actions'] = actions
            context['actions_obj'] = actions_paginator.get_elided_page_range(number=actions_page,
                                                                             on_each_side=1,
                                                                             on_ends=1)

        except Exception as e:
            logger.exception(e)

        return render(request, 'main/logs/list.html', context=context)


class LogsOpsView(View):
    """
    View for listing logs and actions associated with a user's store.
    Includes filtering and pagination functionality.
    """

    # Assuming the rest of the method implementation follows the provided structure,
    # focusing on fetching logs and actions, applying filters, and paginating results.
    def get(self, req):
        res = {"status": 500, "message": "Something went wrong"}
        try:
            logs = list(
                Log.objects.filter(store=req.user.store).order_by('-id').values('user__username', 'action', 'instance',
                                                                                'serial_number', 'category_name',
                                                                                'instance_id', 'created_at'))
            res['logs'] = logs
            res['status'] = 200
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class ActionsView(View):
    """
    View for handling actions (e.g., returns, swaps) on routers.
    Supports creating new actions and toggling shipped status of actions.
    """

    def get(self, req):
        return render(req, 'main/actions/main.html')

    def post(self, req):
        """
        Processes a request to create a new action on a router. It supports various action types including returns, swaps,
        collections, and sales, each with its own specific logic and validation.
        """
        res = {"status": 500, "message": "Something went wrong"}
        # Implementation as provided, handling different action types and updating routers accordingly.

        try:
            store = req.user.store
            body = json.loads(req.body)
            action_type = body.get('action_type')
            sn1 = body.get('sn1')
            sn2 = body.get('sn2')
            order_number = body.get('order_number')
            return_cpe_type = body.get('return_cpe_type')
            router1 = RouterMaster.objects.filter(store=store, serial_number=sn1).order_by('-created_at').first()
            router2 = None
            internal_email = body.get('internal_email')

            if action_type == "sale":

                try:

                    meta_json = {"agent": req.user.email,
                                 "action": "allocated"}

                    if router1.status is None:
                        res['message'] = "This router has not been scanned into stock yet - Please do so and try again."
                        return JsonResponse(res, status=res['status'])

                    if router1.status == RouterMaster.STATUSES[1][0]:
                        res['message'] = "This router is already allocated to an order"
                        return JsonResponse(res, status=res['status'])

                    elif router1.status == RouterMaster.STATUSES[2][0]:
                        res['message'] = "This router has been returned - Please issue a new device."
                        return JsonResponse(res, status=res['status'])

                    elif router1.status == RouterMaster.STATUSES[3][0]:
                        res['message'] = "This router is set to be returned to CCD - Please issue a new device."
                        return JsonResponse(res, status=res['status'])
                    elif router1.status == RouterMaster.STATUSES[0][0]:

                        router = RouterMaster.objects.create(store=store,
                                                             category_id=router1.category_id,
                                                             serial_number=sn1,
                                                             event_type=action_type,
                                                             status="onboarded",
                                                             meta=meta_json)
                        router.save()
                        res['status'] = 200
                        del res['message']

                except AttributeError:
                    res['message'] = "This router has not been scanned into stock yet - Please do so and try again."
                    return JsonResponse(res, status=res['status'])


            elif action_type == "collect":

                try:

                    meta_json = {"agent": req.user.email,
                                 "action": "allocated"}

                    if router1.status == RouterMaster.STATUSES[1][0]:
                        res['message'] = "This router is already allocated to an order"
                        return JsonResponse(res, status=res['status'])

                    elif router1.status == RouterMaster.STATUSES[2][0]:
                        res['message'] = "This router has been returned - Please issue a new device."
                        return JsonResponse(res, status=res['status'])

                    elif router1.status == RouterMaster.STATUSES[3][0]:
                        res['message'] = "This router is set to be returned to CCD - Please issue a new device."
                        return JsonResponse(res, status=res['status'])
                    elif router1.status == RouterMaster.STATUSES[0][0]:

                        router = RouterMaster.objects.create(store=store,
                                                             category_id=router1.category_id,
                                                             serial_number=sn1,
                                                             event_type=action_type,
                                                             status="onboarded",
                                                             meta=meta_json)
                        router.save()
                        res['status'] = 200
                        del res['message']

                except AttributeError:
                    res['message'] = "This router has not been scanned into stock yet - Please do so and try again."
                    return JsonResponse(res, status=res['status'])

            elif action_type == "return":

                if router1.status == RouterMaster.STATUSES[0][0]:
                    res['message'] = "This router was never assigned to a customer"
                    return JsonResponse(res, status=res['status'])

                elif router1.status == RouterMaster.STATUSES[2][0]:
                    res['message'] = "This router has already been returned"
                    return JsonResponse(res, status=res['status'])

                elif router1.status == RouterMaster.STATUSES[3][0]:
                    res['message'] = "This router is set to be returned to CCD."
                    return JsonResponse(res, status=res['status'])

                elif router1.status == RouterMaster.STATUSES[1][0]:

                    if not router1:

                        meta_json = {"agent": req.user.email,
                                     "action": "deallocated",
                                     "reason": body.get('return_reason'),
                                     "comment": body.get('comment')}

                        category = Category.objects.filter(name=return_cpe_type).first()
                        category_id = category.id

                        router = RouterMaster.objects.create(store=store,
                                                             category_id=category_id,
                                                             serial_number=sn1,
                                                             event_type=action_type,
                                                             status="returned",
                                                             meta=meta_json)
                        router.save()
                        res['status'] = 200
                        del res['message']

                    elif router1:

                        meta_json = {"agent": req.user.email,
                                     "action": "deallocated",
                                     "reason": body.get('return_reason'),
                                     "comment": body.get('comment')}

                        router = RouterMaster.objects.create(store=store,
                                                             category_id=router1.category_id,
                                                             serial_number=sn1,
                                                             event_type=action_type,
                                                             status="returned",
                                                             meta=meta_json)
                        router.save()
                        res['status'] = 200
                        del res['message']


            elif action_type == "swap":

                unique_swap_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
                router2 = RouterMaster.objects.filter(store=store, serial_number=sn2).order_by('-updated_at').first()
                # Allocate the new CPE
                meta_json = {"agent": req.user.email,
                             "action": "allocated",
                             "reason": body.get('swap_reason'),
                             "comment": body.get('comment'),
                             "swap_reference": unique_swap_id}

                try:

                    if router1.status == RouterMaster.STATUSES[1][0]:
                        res['message'] = "This router is already allocated to an order"
                        return JsonResponse(res, status=res['status'])

                    elif router1.status == RouterMaster.STATUSES[2][0]:
                        res['message'] = "This router has been returned - Please issue a new device."
                        return JsonResponse(res, status=res['status'])

                    elif router1.status == RouterMaster.STATUSES[3][0]:
                        res['message'] = "This router is set to be returned to CCD - Please issue a new device."
                        return JsonResponse(res, status=res['status'])
                    elif router1.status == RouterMaster.STATUSES[0][0]:

                        router = RouterMaster.objects.create(store=store,
                                                             category_id=router1.category_id,
                                                             serial_number=sn1,
                                                             event_type=action_type,
                                                             status="onboarded",
                                                             meta=meta_json)
                        router.save()
                        # Deallocate old CPE
                        if not router2:

                            meta_json = {"agent": req.user.email,
                                         "action": "deallocated",
                                         "reason": body.get('swap_reason'),
                                         "comment": body.get('comment'),
                                         "swap_reference": unique_swap_id}

                            category = Category.objects.filter(
                                name=return_cpe_type).first()
                            category_id = category.id

                            router = RouterMaster.objects.create(store=store,
                                                                 category_id=category_id,
                                                                 serial_number=sn2,
                                                                 event_type=action_type,
                                                                 status="returned",
                                                                 meta=meta_json)
                            router.save()
                            res['status'] = 200
                            del res['message']

                        elif router2:

                            meta_json = {"agent": req.user.email,
                                         "action": "deallocated",
                                         "reason": body.get('swap_reason'),
                                         "comment": body.get('comment'),
                                         "swap_reference": unique_swap_id}

                            router = RouterMaster.objects.create(store=store,
                                                                 category_id=router2.category_id,
                                                                 serial_number=sn2,
                                                                 event_type=action_type,
                                                                 status="returned",
                                                                 meta=meta_json)
                            router.save()

                        res['status'] = 200
                        del res['message']

                except AttributeError:
                    res['message'] = "This router has not been scanned into stock yet - Please do so and try again."
                    return JsonResponse(res, status=res['status'])


            elif action_type == "out":

                action_type = 'internal_allocation'

                meta_json = {"agent": req.user.email,
                             "action": "allocated",
                             "trustee": internal_email}

                try:

                    if router1.status == RouterMaster.STATUSES[1][0]:
                        res['message'] = "This router is already allocated to an order"
                        return JsonResponse(res, status=res['status'])

                    elif router1.status == RouterMaster.STATUSES[2][0]:
                        res['message'] = "This router has been returned - Please issue a new device."
                        return JsonResponse(res, status=res['status'])

                    elif router1.status == RouterMaster.STATUSES[3][0]:
                        res['message'] = "This router is set to be returned to CCD - Please issue a new device."
                        return JsonResponse(res, status=res['status'])
                    elif router1.status == RouterMaster.STATUSES[0][0]:

                        router = RouterMaster.objects.create(store=store,
                                                             category_id=router1.category_id,
                                                             serial_number=sn1,
                                                             event_type=action_type,
                                                             status="onboarded",
                                                             meta=meta_json)
                        router.save()
                        res['status'] = 200
                        del res['message']

                except AttributeError:
                    res['message'] = "This router has not been scanned into stock yet - Please do so and try again."
                    return JsonResponse(res, status=res['status'])

        except Exception as e:
            logger.exception(e)

        return JsonResponse(res, status=res['status'])

    def put(self, req):
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            if not req.user.role == "store_manager":
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res, status=res['status'])
            body = json.loads(req.body)

            action_id = body.get('id')
            action = Action.objects.filter(id=action_id, store=req.user.store).first()
            if action:
                action.shipped = False if action.shipped else True
                action.save()
                res['status'] = 200
                res['message'] = 'Action edited successfully'
            else:
                res['message'] = 'Action not found'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class ReturnView(View):
    """
    View for handling returned routers.
    Displays routers marked as returned and supports pagination.
    """

    def get(self, req):
        res = {"status": 500, "message": "Something wrong hapenned"}
        context = {}
        try:
            routers_page = req.GET.get('router_page') if req.GET.get('router_page') else 1
            routers = Router.objects.filter(store=req.user.store, status="return")
            context['categories'] = Category.objects.filter(store=req.user.store, deleted=False)
            context['routers_count'] = routers.count()
            routers_ordered = routers.order_by('-created_at')
            routers_paginator = Paginator(routers_ordered, 10)
            routers = routers_paginator.page(routers_page)
            context['routers_paginator'] = routers_paginator
            context['routers'] = routers
            context['routers_obj'] = routers_paginator.get_elided_page_range(number=routers_page,
                                                                             on_each_side=1,
                                                                             on_ends=1)
        except Exception as e:
            logger.exception(e)
        return render(req, 'main/return/index.html', context=context)


class SwitchStore(View):
    """
    View for handling router trabsferss.
    
    Supports GET for fetching stores excluding the current one,
    PUT for switching a single router to a new store, and
    PATCH for switching multiple routers to a new store based on their serial numbers.
    """

    def get(self, req):
        """
        Handles GET requests to provide a list of stores excluding the current user's store.
        
        Args:
            req: HttpRequest object.
        
        Returns:
            HttpResponse object with the rendered list of stores.
        """
        context = {}
        try:
            store = req.user.store
            other_store = StoreMaster.objects.all().exclude(id=StoreMaster.id)
            context['stores'] = other_store
        except Exception as e:
            logger.exception(e)
        return render(req, 'main/transfer/index.html', context=context)

    def put(self, req):
        """
        Handles PUT requests to switch a router to a new store.
        
        Args:
            req: HttpRequest object containing JSON body with 'router_id' and 'new_store'.
        
        Returns:
            JsonResponse object indicating the status of the store switch operation.
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            body = json.loads(req.body)
            router_id = body.get('router_id')
            new_store = body.get('new_store')
            router = Router.objects.filter(id=router_id).first()
            store = StoreMaster.objects.filter(id=new_store).first()

            if router and store:
                router.store = store
                router.save()

                res['status'] = 200
                res['message'] = "Store switched successfully"
            elif router:
                res['message'] = "Store not found"
            else:
                res['message'] = "Router not found"

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])

    def patch(self, req):
        """
        Handles PATCH requests to switch multiple routers to a new store based on serial numbers.
        
        Args:
            req: HttpRequest object containing JSON body with 'serial_numbers' and 'new_store'.
        
        Returns:
            JsonResponse object indicating the status of the store switch operation for multiple routers.
        """
        res = {"status": 500, "message": "Something wrong hapenned"}
        try:
            body = json.loads(req.body)
            serial_numbers = body.get('serial_numbers')
            new_store = body.get('new_store')
            routers = Router.objects.filter(serial_number__in=serial_numbers)
            store = StoreMaster.objects.filter(id=new_store).first()

            if routers and store:
                for router in routers:
                    router.store = store
                    router.save()

                res['status'] = 200
                res['message'] = "Store switched successfully"
            else:
                res['message'] = "Rotuers not found"

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class ServiceCenter(View):
    """
    View for handling actions (e.g., returns, swaps) on routers.
    Supports creating new actions and toggling shipped status of actions.
    """

    def get(self, req):
        return render(req, 'main/service_center/service_center.html')


class ManagementCenter(View):
    """
    New view given to managers to manage stock
    """

    def get(self, req):
        return render(req, 'main/management_center/main.html')


class ReturnToCCD(View):
    """
    New view given to managers to manage stock to be return to CCD
    """

    def __init__(self):
        self.action = 'returned_CCD'
        self.status = 'to_refurb'

    def get(self, req):

        context = {}
        store = req.user.store
        # Fetch categories that are not marked as deleted and belong to the user's store
        categories = list(Category.objects.filter(deleted=False).values())
        context['categories'] = categories
        return render(req, 'main/router/ccd-return.html', context=context)

    def post(self, req):
        """
        Handle POST requests: Creates a new router with the provided details from the request.

        :param request: HttpRequest object containing the router details in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": "Something went wrong."}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have permissions"
                return JsonResponse(res, status=res['status'])

            user = req.user
            store = user.store
            # We format the body of the request to a python object
            bodies = json.loads(req.body)
            failed_uploads = []

            for body in bodies:

                # We retrieve the name from the body of the request
                category = body.get('category')

                serial_number = body.get('serial_number')

                # Create meta field
                meta_json = {"agent": req.user.email, "action": self.action}

                # Validate and fetch the category
                category = Category.objects.filter(name=category).first()

                router_status_check = RouterMaster.objects.filter(store=store,
                                                                  serial_number=serial_number).order_by(
                    '-updated_at').first()

                if (router_status_check.status == RouterMaster.STATUSES[2][0]):

                    message = ""

                    try:

                        # Create the router instance and save it to the database
                        router = RouterMaster.objects.create(store=store,
                                                             category=category,
                                                             serial_number=serial_number,
                                                             event_type=self.action,
                                                             status=self.status,
                                                             meta=meta_json)

                        router.save()

                    except:
                        body['message'] = "failed to write to database"
                        failed_upload = FailedUploads.objects.create(
                            event_type=self.action,
                            serial_number=serial_number,
                            status_from=router_status_check.status,
                            status_to=self.status,
                            message=message)

                        failed_uploads.append(body)

                else:

                    if router_status_check.status is None:
                        message = "Router wasn't loaded into stock"
                    elif router_status_check.status == RouterMaster.STATUSES[1][0]:
                        message = "Router currently assigned to customer"
                    elif router_status_check.status == RouterMaster.STATUSES[3][0]:
                        message = "Router already assigned to CCD"
                    elif router_status_check.status == RouterMaster.STATUSES[0][0]:
                        message = "Router already in-stock, cannot send back"

                    failed_upload = FailedUploads.objects.create(
                        event_type=self.action,
                        serial_number=serial_number,
                        status_from=router_status_check.status,
                        status_to=self.status,
                        message=message)
                    failed_upload.save()

                    failed_uploads.append(body)

            if len(failed_uploads) == 0:
                res['status'] = 200
                del res['message']

            else:
                res['status'] = 201
                res['message'] = 'Some router uploads failed'
                print(failed_uploads)

        except IntegrityError:
            res['message'] = 'Router already exists in the database'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])


class TransferToStore(View):
    """
    New view given to managers to manage stock to be return to CCD
    """

    def __init__(self):
        self.action = 'transfer'
        self.status = 'in_stock'

    def get(self, req):

        context = {}
        store = req.user.store
        # Fetch categories that are not marked as deleted and belong to the user's store
        stores = list(StoreMaster.objects.values())
        categories = list(Category.objects.filter(deleted=False).values())
        context['stores'] = stores
        context['categories'] = categories
        return render(req, 'main/router/transfer.html', context=context)

    def post(self, req):
        """
        Handle POST requests: Creates a new router with the provided details from the request.

        :param request: HttpRequest object containing the router details in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": "Something went wrong."}

        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have permissions"
                return JsonResponse(res, status=res['status'])

            user = req.user
            store_from = user.store
            # We format the body of the request to a python object
            bodies = json.loads(req.body)
            failed_uploads = []

            for body in bodies:

                # We retrieve the name from the body of the request
                category = body.get('category')

                serial_number = body.get('serial_number')

                store_to_name = body.get('store_to')
                store_to = StoreMaster.objects.get(name=store_to_name)

                # Create meta field
                meta_json = {"agent": req.user.email, "action": self.action,
                             "store_from": req.user.store.name, "store_to": store_to.name}

                # Validate and fetch the category
                category = Category.objects.filter(name=category).first()

                router_status_check = RouterMaster.objects.filter(store=store_from,
                                                                  serial_number=serial_number).order_by(
                    '-updated_at').first()

                if (router_status_check.status == RouterMaster.STATUSES[0][0]):

                    message = ""

                    try:
                        # Create the router instance and save it to the database
                        router = RouterMaster.objects.create(store=store_to,
                                                             category=category,
                                                             serial_number=serial_number,
                                                             event_type=self.action,
                                                             status=self.status,
                                                             meta=meta_json)

                        router.save()

                    except:
                        message = "failed to write to database"
                        failed_upload = FailedUploads.objects.create(
                            event_type=self.action,
                            serial_number=serial_number,
                            status_from=router_status_check.status,
                            status_to=self.status,
                            message=message)

                        failed_uploads.append(body)

                else:

                    if router_status_check.status is None:
                        message = "Router wasn't loaded into stock"
                        res['message'] = message
                    elif router_status_check.status == RouterMaster.STATUSES[1][0]:
                        message = "Router currently assigned to customer"
                        res['message'] = message
                    elif router_status_check.status == RouterMaster.STATUSES[3][0]:
                        message = "Router already assigned to CCD"
                        res['message'] = message
                    elif router_status_check.status == RouterMaster.STATUSES[2][0]:
                        message = "Router is a return, not eligible for transfer"
                        res['message'] = message

                    failed_upload = FailedUploads.objects.create(
                        event_type=self.action,
                        serial_number=serial_number,
                        status_from=router_status_check.status,
                        status_to=self.status,
                        message=message)
                    failed_upload.save()

                    failed_uploads.append(body)

            if len(failed_uploads) == 0:
                res['status'] = 200
                res['message'] = "Successfully transferred"

            else:
                res['status'] = 201
                print(failed_uploads)

        except IntegrityError:
            res['message'] = 'Router already exists in the database'
        except Exception as e:
            logger.exception(e)

        return JsonResponse(res, status=res['status'])
