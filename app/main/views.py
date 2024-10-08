import logging
import json
from datetime import datetime


from django.contrib.auth import authenticate, login
from django.db.models import Window, F, Q
from django.db.models.functions import RowNumber
from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse


from main.common import check_missing_routers, check_routers, username_or_email_exists
from main.models import Category, User, Log, Router, Store, FailedUploads, Action
from main.utilities import valid_permissions, valid_action_path
from main.errors import ERRORS


logger = logging.getLogger(__name__)


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

        routers = (
            Router.objects.filter(store_id=user.store)
            .annotate(
                rank=Window(
                    expression=RowNumber(),
                    partition_by=[F("serial_number")],
                    order_by=F("created_at").desc(),
                )
            )
            .filter(rank=1)
            .filter(status="in_stock")[:6]
        )
        # Determine if more than 5 categories or routers exist to control the display of a 'show more' button
        context["more_categories"] = len(categories) > 5
        context["more_routers"] = len(routers) > 5
        # Limit the displayed categories and routers to 5
        context["categories"] = categories[:5]
        context["routers"] = routers[:5]

        return render(req, "main/other/homepage.html", context=context)


class SignupView(View):
    """
    A view to handle user sign-ups.
    """

    def get(self, req):
        """
        Handles GET requests to show the signup form.
        """
        return render(req, "main/account/signup.html")

    def post(self, req):
        """
        Handles POST requests to register a new user.
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            body = json.loads(req.body)
            username = body.get("username")
            email = body.get("email")
            password1 = body.get("password1")
            password2 = body.get("password2")
            # Validate required fields
            if not all([username, email, password1, password2]):
                res["message"] = "All fields are required"
            else:
                if password1 != password2:
                    res["message"] = "Passwords do not match"
                elif len(password1) < 8:
                    res["message"] = "The password is too short"
                elif username_or_email_exists(username, email):
                    res["message"] = "Username or email already exists"
                else:
                    # Create and save the new user
                    user = User.objects.create(username=username, email=email)
                    # Later use set_password method, this method will hash the password of the user instead of leaving it in plain text (For security)
                    user.set_password(password1)
                    user.save()
                    res["status"] = 200
                    del res["message"]
                    login(req, user)
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])


class LoginView(View):
    """
    A view to handle user login.
    """

    def get(self, req):
        """
        Handles GET requests to show the login form.
        """
        return render(req, "main/account/login.html")

    def post(self, req):
        """
        Handles POST requests to authenticate and log in a user.
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            body = json.loads(req.body)
            username = body.get("username")
            password = body.get("password")
            if username and password:
                # Check if a user with the username or email provided exists
                user = authenticate(req, username=username, password=password)
                if not user:
                    # In case the user tried to login using his email, find the user and authenticate using the username of the found user
                    email_user = User.objects.filter(email=username).first()
                    if email_user:
                        user = authenticate(
                            req, username=email_user.username, password=password
                        )
                if user:
                    # When authenticated log the user in and we will redirect him to the homepage from the frontend
                    login(req, user)
                    res["status"] = 200
                    del res["message"]
                else:
                    matched_user = User.objects.filter(
                        Q(username=username) | Q(email=username)
                    )
                    if not matched_user:
                        res["message"] = "Invalid username or email"
                    elif not matched_user[0].check_password(password):
                        res["message"] = "Invalid password"
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])


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
        store_users = (
            list(req.user.store.user_set.all().exclude(id=user.id).values())
            if req.user.store
            else []
        )
        context["store_users"] = store_users
        return render(req, "main/account/profile.html", context=context)

    def post(self, req):
        """
        Handles POST requests to update user information.
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            # Check if the logged-in user has store_manager role
            if req.user.role != "store_manager":
                res["status"] = 403
                res["message"] = ERRORS.DEFAULT_PERMISSIONS_MESSAGE
                return JsonResponse(res, status=res["status"])

            store = req.user.store
            body = json.loads(req.body)
            username = body.get("username")
            role = body.get("role")

            # Try fo find the user by username or email
            added_user = User.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
            if added_user:
                # Update the user's store and role accordingly.
                if added_user.store == store:
                    added_user.role = role
                    message = "edited"
                else:
                    added_user.store = store
                    added_user.role = role
                    message = "added"
                added_user.save()
                res["status"] = 200
                res["message"] = f"User {message} successfully"
            else:
                res["message"] = "User not found"
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def put(self, req):
        """
        Handles PUT requests to update the alert threshold setting for a store.
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            body = json.loads(req.body)
            value = body.get("value")
            if value:
                store = req.user.store
                # Update the store's alert_on value with the new threshold
                store.alert_on = value
                store.save()
                res["status"] = 200
                res["message"] = "Alert threshold edited successfully"
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def delete(self, req):
        """
        Handles DELETE requests to remove a user from a store.
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            # Ensure only users with store_manager role can perform this action
            if req.user.role != "store_manager":
                res["status"] = 403
                res["message"] = ERRORS.DEFAULT_PERMISSIONS_MESSAGE
                return JsonResponse(res, status=res["status"])

            body = json.loads(req.body)
            user_id = body.get("id")

            # Attempt to find and delete the specified user.
            store_user = User.objects.filter(id=user_id).first()
            if store_user:
                # Remove the user from the store and clear their role
                store_user.role = None
                store_user.store = None
                store_user.save()
                res["status"] = 200
                res["message"] = "User deleted successfully"
            else:
                res["message"] = "Can't find the user"
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])


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
        return render(req, "main/store/create-store.html")

    def post(self, req):
        """
        Handle POST requests: Creates a new store with the provided name from the request.

        :param request: HttpRequest object containing the store name in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            # We format the body of the request to a Python dictionary
            body = json.loads(req.body)

            # We retrieve the name from the body of the request
            name = body.get("name")
            full_name = body.get("full_name")
            # Create the store and save it to the database
            store = Store.objects.create(name=name, name_full=full_name)
            store.save()
            # Associate the created store to the user and assign him as the store manager
            user = req.user
            user.store = store
            user.role = "store_manager"
            user.save()
            res["status"] = 200

            del res["message"]  # Remove the error message on success
        except Exception as e:
            logger.exception(e)  # Log the exception for debugging purposes
        return JsonResponse(res, status=res["status"])


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
        return render(req, "main/category/create-category.html")

    def post(self, req):
        """
        Handle POST requests: Creates a new category for the store of the logged-in user.

        :param request: HttpRequest object containing the category name and type in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            if req.user.role != "store_manager":
                res["status"] = 403
                res["message"] = ERRORS.DEFAULT_PERMISSIONS_MESSAGE
                return JsonResponse(res, status=res["status"])
            user = req.user
            store = user.store
            # We format the body of the request to a Python dictionary
            body = json.loads(req.body)
            # We retrieve the name and type from the body of the request
            name = body.get("name")
            category_type = body.get("type")
            # Create the Category instance and save it to the database
            category = Category.objects.create(
                name=name, type=category_type, store=store
            )
            category.save()
            # Log the creation action
            Log.objects.create(
                user=user,
                store=store,
                instance="category",
                instance_id=category.id,
                category_name=category.name,
                action="add",
            )

            res["status"] = 200
            del res["message"]  # Remove the error message on success
        except Exception as e:
            logger.exception(e)  # Log the exception for debugging purposes
        return JsonResponse(res, status=res["status"])


class CreateRouterView(View):
    """
    View for creating a new router within a store.
    Handles GET requests to display the router creation form and POST requests to create a router.
    """

    def __init__(self):
        self.action = "receive"
        self.status = "in_stock"

    def get(self, req):
        """
        Handle GET requests: Renders the router creation form with available categories.

        :param request: HttpRequest object
        :return: HttpResponse object with the rendered router creation form template
        """
        context = {}
        # Fetch categories that are not marked as deleted and belong to the user's store
        categories = list(Category.objects.filter(deleted=False).values())
        context["categories"] = categories
        return render(req, "main/router/create-router.html", context=context)

    def post(self, req):
        """
        Handle POST requests: Creates a new router with the provided details from the request.

        :param request: HttpRequest object containing the router details in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}

        try:

            if not valid_permissions(req.user):
                return JsonResponse(
                    {"status": 403, "message": ERRORS.DEFAULT_PERMISSIONS_MESSAGE},
                    status=403,
                )

            user = req.user
            store = user.store
            bodies = json.loads(req.body)

            for body in bodies:

                category = body.get("category")

                serial_number = body.get("serial_number")

                meta_json = {"agent": req.user.email, "action": self.action}

                category = Category.objects.filter(name=category).first()

                router = Router.objects.filter(
                    store=store, serial_number=serial_number
                ).first()
                router_status = router.status if router else None

                validity_check = valid_action_path(self.action, router_status)

                if validity_check["valid"]:

                    if not router:

                        router = Router.objects.create(
                            store=store,
                            category=category,
                            serial_number=serial_number,
                            event_type=self.action,
                            status=self.status,
                            meta=meta_json,
                        )

                    router.save()
                    res["status"] = validity_check["status"]
                    res["message"] = validity_check["response"]

                elif not validity_check["valid"]:

                    failed_upload = FailedUploads.objects.create(
                        event_type=self.action,
                        serial_number=serial_number,
                        status_from=router_status,
                        status_to=self.status,
                        message=validity_check["response"],
                    )
                    failed_upload.save()
                    res["status"] = validity_check["status"]
                    res["message"] = validity_check["response"]

        except Exception as e:
            logger.exception(e)

        return JsonResponse(res, status=res["status"])


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
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            if req.user.role != "store_manager":
                res["status"] = 403
                res["message"] = ERRORS.DEFAULT_PERMISSIONS_MESSAGE
                return JsonResponse(res, status=res["status"])

            body = json.loads(req.body)
            category_id = body.get("id")
            name = body.get("name")
            category_type = body.get("type")

            category = Category.objects.filter(id=category_id).first()
            if category:
                category.name = name
                category.type = category_type
                category.save()
                # Log the category edit action
                Log.objects.create(
                    user=req.user,
                    instance="category",
                    instance_id=category.id,
                    category_name=category.name,
                    action="edit",
                )
                res["status"] = 200
                res["message"] = "Category edited successfully"

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def delete(self, req):
        """
        Handle DELETE requests: Marks an existing category as deleted.

        :param request: HttpRequest object containing the category ID to be deleted
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            if req.user.role != "store_manager":
                res["status"] = 403
                res["message"] = ERRORS.DEFAULT_PERMISSIONS_MESSAGE
                return JsonResponse(res, status=res["status"])
            body = json.loads(req.body)
            category_id = body.get("id")
            category = Category.objects.filter(id=category_id).first()
            if category:
                category.deleted = True
                category.save()
                # Log the category deletion
                Log.objects.create(
                    user=req.user,
                    instance="category",
                    instance_id=category.id,
                    category_name=category.name,
                    action="delete",
                )
                res["message"] = "Category deleted successfully"
                res["status"] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])


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
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            user = req.user
            store = user.store
            # Fetch routers from the store, ordered by descending ID
            routers = list(
                Router.objects.filter(store=store)
                .order_by("-id")
                .values("id", "category__name", "emei", "serial_number", "created_at")
            )
            res["routers"] = routers
            del res["message"]
            res["status"] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def post(self, req):
        """
        Handle POST requests: Imports a batch of routers from the provided list.

        :param request: HttpRequest object containing the list of routers to be imported
        :return: JsonResponse object with the import operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            user = req.user
            body = json.loads(req.body)
            routers = body.get("routers")
            imported = 0  # Counter for successfully imported routers
            for new_router in routers:
                try:
                    category = Category.objects.filter(
                        name=new_router.get("category")
                    ).first()
                    if category:
                        # Check if the router does not exist or is marked as deleted
                        if not Router.objects.filter(id=new_router.get("id")).exists():
                            if category:
                                router = Router.objects.create(
                                    store=user.store,
                                    category=category,
                                    emei=new_router.get("emei"),
                                    serial_number=new_router.get("serial_number"),
                                )
                                router.save()
                                Log.objects.create(
                                    user=user,
                                    store=user.store,
                                    instance="router",
                                    instance_id=router.id,
                                    serial_number=router.serial_number,
                                    action="add",
                                )
                                imported += 1

                        elif Router.objects.filter(
                            id=new_router.get("id"), deleted=True
                        ).exists():
                            router = Router.objects.get(id=new_router.get("id"))
                            router.category = category
                            router.emei = new_router.get("emei")
                            router.serial_number = new_router.get("serial_number")
                            router.deleted = False
                            router.save()
                            Log.objects.create(
                                user=user,
                                store=user.store,
                                instance="router",
                                instance_id=router.id,
                                serial_number=router.serial_number,
                                action="add",
                            )
                            imported += 1
                    else:
                        logger.error(f"{new_router.get('category')} not found")

                except Exception as e:
                    logger.exception(e)
            res["status"] = 200
            res["message"] = f"{imported} routers imported"
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def put(self, req):
        """
        Handle PUT requests: Edits the details of an existing router.

        :param request: HttpRequest object containing the new details of the router
        :return: JsonResponse object with the edit operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            if req.user.role != "store_manager":
                res["status"] = 403
                res["message"] = ERRORS.DEFAULT_PERMISSIONS_MESSAGE
                return JsonResponse(res, status=res["status"])
            body = json.loads(req.body)
            router_id = body.get("id")
            category = body.get("category")
            serial_number = body.get("serial_number")
            emei = body.get("emei")
            status = body.get("status")

            category_instance = Category.objects.filter(id=category).first()
            router = Router.objects.filter(store=req.user.store, id=router_id).first()
            router.category = category_instance
            router.serial_number = serial_number
            router.emei = emei
            router.status = status
            router.save()
            Log.objects.create(
                user=req.user,
                store=req.user.store,
                instance="router",
                instance_id=router.id,
                serial_number=router.serial_number,
                action="edit",
            )
            res["status"] = 200
            res["message"] = "Router edited successfully"

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def delete(self, req):
        """
        Handle DELETE requests: Marks an existing router as deleted.

        :param request: HttpRequest object containing the ID of the router to be marked as deleted
        :return: JsonResponse object with the delete operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            if req.user.role != "store_manager":
                res["status"] = 403
                res["message"] = ERRORS.DEFAULT_PERMISSIONS_MESSAGE
                return JsonResponse(res, status=res["status"])
            body = json.loads(req.body)
            router_id = body.get("id")
            router = Router.objects.filter(store=req.user.store, id=router_id).first()
            if router:
                router.deleted = True
                router.save()
                Log.objects.create(
                    user=req.user,
                    store=req.user.store,
                    instance="router",
                    instance_id=router.id,
                    serial_number=router.serial_number,
                    action="delete",
                )
                logger.info(
                    f"{req.user.username} deleted router with sn: {router.serial_number} - emei : {router.emei}"
                )
                res["message"] = "Router deleted successfully"
                res["status"] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def patch(self, req):
        """
        Handle PATCH requests: Toggles the shipped status of a router.

        :param request: HttpRequest object containing the ID of the router to update its shipped status
        :return: JsonResponse object with the update operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            body = json.loads(req.body)
            router_id = body.get("id")
            if router_id:
                router = Router.objects.filter(
                    store=req.user.store, id=router_id
                ).first()
                if router:
                    router.shipped = not router.shipped
                    router.save()
                    res["message"] = "Router updated successfully"
                    res["status"] = 200
                else:
                    res["message"] = "Router is not in the Database"
                    res["status"] = 400

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])


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
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            user = req.user
            value = req.GET.get("value")
            # Filter categories by store, name starting with the given value, and not deleted
            categories = list(
                Category.objects.filter(
                    store=user.store, name__startswith=value, deleted=False
                ).values("name")
            )
            res["status"] = 200
            res["categories"] = categories
            del res["message"]
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])


class LogsOpsView(View):
    """
    View for listing logs and actions associated with a user's store.
    Includes filtering and pagination functionality.
    """

    # Assuming the rest of the method implementation follows the provided structure,
    # focusing on fetching logs and actions, applying filters, and paginating results.
    def get(self, req):
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            logs = list(
                Log.objects.filter(store=req.user.store)
                .order_by("-id")
                .values(
                    "user__username",
                    "action",
                    "instance",
                    "serial_number",
                    "category_name",
                    "instance_id",
                    "created_at",
                )
            )
            res["logs"] = logs
            res["status"] = 200
            del res["message"]
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])


class ActionsView(View):
    """
    View for handling actions (e.g., returns, swaps) on routers.
    Supports creating new actions and toggling shipped status of actions.
    """

    def get(self, req):
        return render(req, "main/actions/main.html")

    def post(self, req):
        """
        Processes a request to create a new action on a router. It supports various action types including returns, swaps,
        collections, and sales, each with its own specific logic and validation.
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        # Implementation as provided, handling different action types and updating routers accordingly.

        try:
            store = req.user.store
            body = json.loads(req.body)
            action_type = body.get("action_type")
            sn1 = body.get("sn1")
            sn2 = body.get("sn2")
            return_cpe_type = body.get("return_cpe")
            router1 = (
                Router.objects.filter(store=store, serial_number=sn1)
                .order_by("-updated_at")
                .first()
            )
            internal_email = body.get("internal_email")
            router_status = router1.status if router1 else None

            if not router1:
                router1 = Router(store=store)
            validity_check = valid_action_path(action_type, router_status)

            if action_type == "sale" or action_type == "collect":
                self.process_sale_or_collect(
                    req,
                    res,
                    validity_check,
                    router1,
                    action_type,
                    store,
                    sn1,
                    router_status,
                )

            elif action_type == "return":
                self.process_return(
                    req,
                    res,
                    validity_check,
                    body,
                    router1,
                    action_type,
                    store,
                    sn1,
                    router_status,
                )

            elif action_type == "swap":
                self.process_swap(
                    req,
                    res,
                    store,
                    sn1,
                    sn2,
                    body,
                    validity_check,
                    router1,
                    router_status,
                    action_type,
                    return_cpe_type,
                )

            elif action_type == "out":
                self.process_out(
                    req,
                    res,
                    internal_email,
                    validity_check,
                    router1,
                    sn1,
                    router_status,
                    action_type,
                )

        except Exception as e:
            logger.exception(e)

        return JsonResponse(res, status=res["status"])

    def put(self, req):
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            if req.user.role != "store_manager":
                res["message"] = ERRORS.DEFAULT_PERMISSIONS_MESSAGE
                return JsonResponse(res, status=res["status"])
            body = json.loads(req.body)

            action_id = body.get("id")
            action = Action.objects.filter(id=action_id, store=req.user.store).first()
            if action:
                action.shipped = False if action.shipped else True
                action.save()
                res["status"] = 200
                res["message"] = "Action edited successfully"
            else:
                res["message"] = "Action not found"
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def process_sale_or_collect(
        self, req, res, validity_check, router, action_type, store, sn1, router_status
    ):
        if validity_check["valid"]:

            meta_json = {"agent": req.user.email, "action": "allocated"}

            router.event_type = action_type
            router.store = store
            router.serial_number = sn1
            router.status = "onboarded"
            router.meta = meta_json

            router.save()
            res["status"] = validity_check["status"]
            res["message"] = validity_check["response"]

        else:

            failed_upload = FailedUploads.objects.create(
                event_type=action_type,
                serial_number=sn1,
                status_from=router_status,
                status_to="onboarded",
                message=validity_check["response"],
            )
            failed_upload.save()
            res["status"] = validity_check["status"]
            res["message"] = validity_check["response"]

    def process_return(
        self,
        req,
        res,
        validity_check,
        body,
        router,
        action_type,
        store,
        sn1,
        router_status,
    ):
        if validity_check["valid"]:

            meta_json = {
                "agent": req.user.email,
                "action": "deallocated",
                "reason": body.get("return_reason"),
                "comment": body.get("comment"),
            }

            router.event_type = action_type
            router.serial_number = sn1
            router.store = store
            router.status = "returned"
            router.meta = meta_json

            router.save()
            res["status"] = validity_check["status"]
            res["message"] = validity_check["response"]

        else:

            failed_upload = FailedUploads.objects.create(
                event_type=action_type,
                serial_number=sn1,
                status_from=router_status,
                status_to="returned",
                message=validity_check["response"],
            )
            failed_upload.save()
            res["status"] = validity_check["status"]
            res["message"] = validity_check["response"]

    def process_swap(
        self,
        req,
        res,
        store,
        sn1,
        sn2,
        body,
        validity_check,
        router,
        router_status,
        action_type,
        return_cpe_type,
    ):
        unique_swap_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        router2 = Router.objects.filter(store=store, serial_number=sn2).first()

        meta_json = {
            "agent": req.user.email,
            "action": "allocated",
            "reason": body.get("swap_reason"),
            "comment": body.get("comment"),
            "swap_reference": unique_swap_id,
        }

        if validity_check["valid"]:
            # Allocate the new CPE
            router.event_type = action_type
            router.serial_number = sn1
            router.status = "onboarded"
            router.meta = meta_json
            router.save()

            # Meta for the second router
            meta_json2 = {
                "agent": req.user.email,
                "action": "deallocated",
                "reason": body.get("swap_reason"),
                "comment": body.get("comment"),
                "swap_reference": unique_swap_id,
            }
            # Deallocate old CPE
            if not router2:
                category = Category.objects.filter(name=return_cpe_type).first()

                router2 = Router(store=store, category=category)

            router2.event_type = action_type
            router2.serial_number = sn2
            router2.status = "returned"
            router2.meta = meta_json2
            router2.save()

            res["status"] = validity_check["status"]
            res["message"] = validity_check["response"]

        else:

            failed_upload = FailedUploads.objects.create(
                event_type=action_type,
                serial_number=sn1,
                status_from=router_status,
                status_to="onboarded",
                message=validity_check["response"],
            )
            failed_upload.save()

            failed_upload = FailedUploads.objects.create(
                event_type=action_type,
                serial_number=sn2,
                status_from="onboarded",
                status_to="returned",
                message=validity_check["response"],
            )
            failed_upload.save()
            res["status"] = validity_check["status"]
            res["message"] = validity_check["response"]

    def process_out(
        self,
        req,
        res,
        internal_email,
        validity_check,
        router,
        sn1,
        router_status,
        action_type,
    ):
        meta_json = {
            "agent": req.user.email,
            "action": "allocated",
            "trustee": internal_email,
        }

        if validity_check["valid"]:

            router.event_type = "internal_allocation"
            router.status = "onboarded"
            router.serial_number = sn1
            router.meta = meta_json

            router.save()
            res["status"] = validity_check["status"]
            res["message"] = validity_check["response"]

        elif not validity_check["valid"]:

            failed_upload = FailedUploads.objects.create(
                event_type=action_type,
                serial_number=sn1,
                status_from=router_status,
                status_to="onboarded",
                message=validity_check["response"],
            )
            failed_upload.save()
            res["status"] = validity_check["status"]
            res["message"] = validity_check["response"]


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
            other_stores = Store.objects.all().exclude(id=store.id)
            context["stores"] = other_stores
        except Exception as e:
            logger.exception(e)
        return render(req, "main/transfer/index.html", context=context)

    def put(self, req):
        """
        Handles PUT requests to switch a router to a new store.

        Args:
            req: HttpRequest object containing JSON body with 'router_id' and 'new_store'.

        Returns:
            JsonResponse object indicating the status of the store switch operation.
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            body = json.loads(req.body)
            router_id = body.get("router_id")
            new_store = body.get("new_store")
            router = Router.objects.filter(id=router_id).first()
            store = Store.objects.filter(id=new_store).first()

            if router and router.store != req.user.store:
                res["status"] = 403
                res["message"] = "This router does not belong to your store"
                return JsonResponse(res, status=res["status"])

            if router and store:
                router.store = store
                router.save()

                res["status"] = 200
                res["message"] = "Store switched successfully"
            elif router:
                res["message"] = "Store not found"
            else:
                res["message"] = "Router not found"

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])

    def patch(self, req):
        """
        Handles PATCH requests to switch multiple routers to a new store based on serial numbers.

        Args:
            req: HttpRequest object containing JSON body with 'serial_numbers' and 'new_store'.

        Returns:
            JsonResponse object indicating the status of the store switch operation for multiple routers.
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            body = json.loads(req.body)
            serial_numbers = body.get("serial_numbers")
            new_store = body.get("new_store")
            routers = Router.objects.filter(serial_number__in=serial_numbers)
            store = Store.objects.filter(id=new_store).first()

            if routers and store:
                for router in routers:
                    router.store = store
                    router.save()

                res["status"] = 200
                res["message"] = "Store switched successfully"
            else:
                res["message"] = "Rotuers not found"

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])


class ServiceCenter(View):
    """
    View for handling actions (e.g., returns, swaps) on routers.
    Supports creating new actions and toggling shipped status of actions.
    """

    def get(self, req):
        return render(req, "main/service_center/service_center.html")


class ManagementCenter(View):
    """
    New view given to managers to manage stock
    """

    def get(self, req):
        return render(req, "main/management_center/main.html")


class ReturnToCCD(View):
    """
    New view given to managers to manage stock to be return to CCD
    """

    def __init__(self):
        self.action = "returned_CCD"
        self.status = "to_refurb"

    def get(self, req):

        context = {}
        # Fetch categories that are not marked as deleted and belong to the user's store
        categories = list(Category.objects.filter(deleted=False).values())
        context["categories"] = categories
        return render(req, "main/router/ccd-return.html", context=context)

    def post(self, req):
        """
        Handle POST requests: Creates a new router with the provided details from the request.

        :param request: HttpRequest object containing the router details in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}
        try:
            if not valid_permissions(req.user):
                return JsonResponse(
                    {"status": 403, "message": ERRORS.DEFAULT_PERMISSIONS_MESSAGE},
                    status=403,
                )

            user = req.user
            store = user.store
            # We format the body of the request to a python object
            bodies = json.loads(req.body)

            for body in bodies:

                # We retrieve the name from the body of the request
                category = body.get("category")

                serial_number = body.get("serial_number")

                # Create meta field
                meta_json = {"agent": req.user.email, "action": self.action}

                # Validate and fetch the category
                category = Category.objects.filter(name=category).first()
                router = Router.objects.filter(
                    store=store, serial_number=serial_number
                ).first()

                if not router:
                    router = Router()

                router.store = store
                router.category = category
                router.event_type = self.action
                router.status = self.status
                router.meta = meta_json

                router.save()

                res["status"] = 200
                res["message"] = "Success"

        except Exception as e:
            logger.exception(e)

        return JsonResponse(res, status=res["status"])


class TransferToStore(View):
    """
    New view given to managers to manage stock to be return to CCD
    """

    def __init__(self):
        self.action = "transfer"
        self.status = "in_stock"

    def get(self, req):

        context = {}
        # Fetch categories that are not marked as deleted and belong to the user's store
        stores = list(Store.objects.values())
        categories = list(Category.objects.filter(deleted=False).values())
        context["stores"] = stores
        context["categories"] = categories
        return render(req, "main/router/transfer.html", context=context)

    def post(self, req):
        """
        Handle POST requests: Creates a new router with the provided details from the request.

        :param request: HttpRequest object containing the router details in its body
        :return: JsonResponse object with the operation status and message
        """
        res = {"status": 500, "message": ERRORS.DEFAULT_ERROR_MESSAGE}

        try:
            if not valid_permissions(req.user):
                return JsonResponse(
                    {"status": 403, "message": ERRORS.DEFAULT_PERMISSIONS_MESSAGE},
                    status=403,
                )

            user = req.user
            store_from = user.store
            # We format the body of the request to a python object
            bodies = json.loads(req.body)

            for body in bodies:
                # We retrieve the name from the body of the request
                category = body.get("category")

                serial_number = body.get("serial_number")

                store_to_name = body.get("store_to")
                store_to = Store.objects.get(name=store_to_name)

                # Create meta field
                meta_json = {
                    "agent": req.user.email,
                    "action": self.action,
                    "store_from": req.user.store.name,
                    "store_to": store_to.name,
                }

                # Validate and fetch the category
                category = Category.objects.filter(name=category).first()

                try:
                    router_status = (
                        Router.objects.filter(
                            store=store_from, serial_number=serial_number
                        )
                        .order_by("-updated_at")
                        .first()
                        .status
                    )

                    router_created_at = (
                        Router.objects.filter(
                            store=store_from, serial_number=serial_number
                        )
                        .order_by("updated_at")
                        .first()
                        .created_at
                    )
                except AttributeError:
                    router_status = None

                validity_check = valid_action_path(self.action, router_status)
                if validity_check["valid"]:

                    if not router_status:
                        router = Router.objects.create(
                            store=store_to,
                            category=category,
                            serial_number=serial_number,
                            event_type=self.action,
                            created_at=router_created_at,
                            status=self.status,
                            meta=meta_json,
                        )

                    elif router_status:
                        router = Router.objects.filter(
                            serial_number=serial_number
                        ).first()
                        router.store = store_to

                    router.save()
                    res["status"] = validity_check["status"]
                    res["message"] = validity_check["response"]

                elif not validity_check["valid"]:

                    failed_upload = FailedUploads.objects.create(
                        event_type=self.action,
                        serial_number=serial_number,
                        status_from=router_status,
                        status_to=self.status,
                        message=validity_check["response"],
                    )
                    failed_upload.save()
                    res["status"] = validity_check["status"]
                    res["message"] = validity_check["response"]

        except Exception as e:
            logger.exception(e)

        return JsonResponse(res, status=res["status"])


class StockTakeView(View):
    def get(self, request):
        context = {}

        try:
            store = request.user.store if request.user.is_authenticated else None
            categories = Category.objects.filter(store=store)
            context["categories"] = categories
        except Exception as e:
            logger.exception(e)

        return render(request, "main/router/stock-take.html", context=context)

    def post(self, request):
        res = {
            "status": 500,
            "message": ERRORS.DEFAULT_ERROR_MESSAGE,
            "results": [],
            "new_routers": [],
            "missing_routers": [],
        }
        try:
            check_routers(request, res)
            check_missing_routers(request, res)
            res["status"] = 200
            res["message"] = "Stock take successful"

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res["status"])
