#Best practice is to divide the imports 
#First import Built-in methods
#Then import Django methods
#Last import custom method written by you

import json
from datetime import date, datetime, time,timedelta

from django.shortcuts import render
from django.views.generic import View
from django.views.generic.list import ListView
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.db.models import Q,Sum, F, Case, When, IntegerField
from django.utils.timezone import get_current_timezone, make_aware, now
from django.core.paginator import Paginator


from main.models import *
from main.common import *

import logging
logger = logging.getLogger(__name__)

# Create your views here.

class HomePage(View):
    def get(self,req):
        context = {}
        user = req.user
        #Get 6 categories and routers, display 5 only, if there are more than 6 then we know there is more than 5 and we show the button 
        #that redirect to page that shows all the categories/routers
        categories = Category.objects.filter(store=user.store,deleted=False)[:6]
        routers = Router.objects.filter(store=user.store,deleted=False)[:6]
        context['more_categories'] = len(categories) > 5
        context['more_routers'] = len(routers) > 5
        context['categories'] = categories[:5]
        context['routers'] = routers[:5]
        
        return render(req,'main/other/homepage.html',context=context)

class SignupView(View):
    def get(self,req):
        return render(req,'main/account/signup.html')
    
    def post(self,req):
        res = {'status':500,'message':'Something wrong hapenned'}
        try:
            body = json.loads(req.body)
            username = body.get('username')
            email = body.get('email')
            password1 = body.get('password1')
            password2 = body.get('password2')
            if not all([username,email,password1,password2]):
                res['message'] = 'All fields are required'
            else:
                if password1 != password2:
                    res['message'] = 'Passwords do not match'
                elif len(password1) < 8:
                    res['message'] = 'The password is too short'
                elif username_or_email_exists(username,email):
                    res['message'] = 'Username or email already exists'
                else:
                    #First create the user instance with the username only
                    user = User.objects.create(username=username,email=email)
                    #Later use set_password method, this method will hash the password of the user instead of leaving it in plain text (For security)
                    user.set_password(password1)
                    user.save()
                    res['status'] = 200
                    del res['message']

                
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])
    
class LoginView(View):
    def get(self,req):
        return render(req,'main/account/login.html')
    
    def post(self,req):
        res = {'status':500,'message':'Something wrong hapenned'}
        try:
            body = json.loads(req.body)
            username = body.get('username')
            password = body.get('password')
            if username and password:
                #Check if a user with the username or email provided exists
                user = authenticate(req, username = username, password=password)
                if not user:
                    #In case the user tried to login using his email, find the user and authenticate using the username of the found user
                    email_user = User.objects.filter(email = username).first()
                    if email_user:
                        user = authenticate(req, username = email_user.username, password=password)
                if user:
                    #When authenticated log the user in and we will redirect him to the homepage from the frontend
                    login(req, user)
                    res['status'] = 200
                    del res['message']
                else:
                    matched_user = User.objects.filter(Q(username = username) | Q(email = username))
                    if not matched_user:
                        res['message'] = ('Invalid username or email')
                    elif not matched_user[0].check_password(password):
                        res['message'] = ('Invalid password')


                
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res, status=res['status'])
    
class ProfileView(View):
    def get(self,req):
        context = {}
        user = req.user
        store_users = list(req.user.store.user_set.all().exclude(id=user.id).values())
        context['store_users'] = store_users
        return render(req,'main/account/profile.html',context=context)
    
    def post(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            store = req.user.store
            body = json.loads(req.body)
            username = body.get('username')
            role = body.get('role')
            
            added_user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            if added_user:
                if added_user.store == store :
                    added_user.role = role
                    message = 'edited'
                else:
                    added_user.store = store
                    added_user.role = role
                    message = 'added'
                added_user.save()
                res['status'] = 200
                res['message'] = f'User {message} successfully'
            else :
                res['message'] = 'User not found'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
    def delete(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            body = json.loads(req.body)
            user_id = body.get('id')
            
            store_user = User.objects.filter(id=user_id).first()
            if store_user:
                store_user.role = None
                store_user.store = None
                store_user.save()
                res['status'] = 200
                res['message'] = 'User deleted successfully'
            else:
                res['message'] = "Can't find the user"
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])

        
class DashboardView(View):
    def get(self,req):
        user = req.user
        store = user.store
        query = req.GET
        context = {}
        colors = ["#e58989","#edcb8d","#6868e5"]
        days = list(reversed([today_midnight() - timedelta(days=x) for x in range(5)]))
        
        #Routers part
        router_page = query.get('router_page') if query.get('router_page') else 1
        routers = Router.objects.filter(store=user.store,deleted=False).order_by('-id')
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
        router_paginator = Paginator(routers,10)
        routers = router_paginator.page(router_page)
        context['routers_count'] = router_paginator.count
        context['routers_paginator'] = router_paginator.get_elided_page_range(number=router_page, 
                                           on_each_side=1,
                                           on_ends=1)
        
        #Category page
        categories_page = query.get('categories_page') if query.get('categories_page') else 1
        categories = Category.objects.filter(store=user.store,deleted=False).order_by('-id')
        category_name = query.get('category_name')
        category_type = query.get('category_type')
        if category_name:
            categories = categories.filter(name__icontains=category_name)
        if category_type:
            categories = categories.filter(type=category_type)

        category_paginator = Paginator(categories,10)
        categories = category_paginator.page(categories_page)
        context['categories_paginator'] = category_paginator.get_elided_page_range(number=categories_page, 
                                           on_each_side=1,
                                           on_ends=1)
        
        

        

        #Employees part
        employees = User.objects.filter(store=store)
        actions = ['add','edit','delete']
        for action in actions:
            context[action] =  {}
            for emp_index,employee in enumerate(employees):
                obj = []
                for day_index,day in enumerate(days):
                    date_start = make_aware(day)
                    date_end = make_aware(day + timedelta(days=1))
                    logs = Log.objects.filter(store=store,user=employee,action=action,instance="router",created_at__gte=date_start,created_at__lt=date_end).count()
                    if logs:
                        obj.append(logs)
                    else:
                        obj.append(0)
                color = colors[emp_index % len(colors)]
                context[action][employee.username] = {'obj':obj,'color':color+'33','border':color}
        #Moniors part
        context['monitors'] = []
        store_monitors = []

        #Routers per category section
        routers_categories = Category.objects.filter(store=store,deleted=False)

        
        for index,category in enumerate(routers_categories):
            obj = []
            for day_index,day in enumerate(days):
                if day_index == 4:
                    obj.append(category.count_routers())
                else:
                    date_start = day
                    date_end = day + timedelta(days=1)
                    monitoring = Monitoring.objects.filter(store=store,category=category,day__gte=date_start,day__lt=date_end).first()
                    if monitoring:
                        obj.append(monitoring.routers)
                    else:
                        default = 0
                        if day_index > 0:
                            default = obj[day_index - 1]
                        obj.append(default)
            color = colors[index % len(colors)]
            monitor_obj = {'label':category.name,'values':obj,'color':color+'33','border':color}
            
            context['monitors'].append(monitor_obj)
        
        #Routers by store section
        for day_index,day in enumerate(days):
            if day_index == 4:
                store_monitors.append(store.count_routers())
                print(store.count_routers())
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
                #When there is no entry for this date, and index > 1, keep the same amount of routers of yesterday for today
                if not total and day_index > 0 and not Monitoring.objects.filter(store=store,day__gte=date_start,day__lt=date_end):
                    total = store_monitors[day_index - 1]

                    
                store_monitors.append(total)


        context['routers'] = routers
        context['categories_obj'] = categories
        context['categories'] = routers_categories
        context['action'] = actions
        context['store_monitors'] = store_monitors    
        context['days'] = [day.strftime("%A") for day in days]
        return render(req,'main/dashboard/index.html',context=context)
    

class CreateStoreView(View):
    def get(self,req):
        return render(req,'main/store/create-store.html')
    def post(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            #We format the body of the request to a python object
            body = json.loads(req.body)
            #We retrieve the name from the body of the request
            name = body.get("name")
            #Create the store and save it
            store = Store.objects.create(name=name)
            store.save()
            #Associate the store to the user and assign him as the store manager
            user = req.user
            user.store = store
            user.role = 'store_manager'
            user.save()
            res['status'] = 200
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])

class CreateCategoryView(View):
    def get(self,req):
        return render(req,'main/category/create-category.html')
    def post(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            user = req.user
            store = user.store
            #We format the body of the request to a python object
            body = json.loads(req.body)
            #We retrieve the name from the body of the request
            name = body.get("name")
            category_type = body.get('type')
            #Create the Category and save it
            category = Category.objects.create(name=name,type=category_type,store=store)
            category.save()
            Log.objects.create(user = user,store = store,instance='category',instance_id=category.id,category_name=category.name,action='add')

            res['status'] = 200
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
class CreateRouterView(View):
    def get(self,req):
        context = {}
        store = req.user.store
        categories = list(Category.objects.filter(store=store,deleted=False).values())
        context['categories'] = categories
        return render(req,'main/router/create-router.html',context=context)
    def post(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            user = req.user
            store = user.store
            #We format the body of the request to a python object
            body = json.loads(req.body)
            #We retrieve the name from the body of the request
            category = body.get('category')
            serial_number = body.get('serial_number')
            emei = body.get('emei')
            #Create the Category and save it
            category = Category.objects.filter(id=category).first()
            router = Router.objects.create(store=store,category=category,emei=emei,serial_number=serial_number)
            router.save()
            category.alerted = False
            category.save()
            Log.objects.create(user = user,store = store,instance='router',instance_id=router.id,emei=router.emei,action='add')

            res['status'] = 200
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    

class CategoryView(View):
    def put(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            body = json.loads(req.body)
            category_id = body.get('id')
            name = body.get('name')
            category_type = body.get('type')

            category = Category.objects.filter(store = req.user.store,id=category_id).first()
            if category:
                category.name = name
                category.type = category_type
                category.save()
                Log.objects.create(user = req.user,store = req.user.store,instance='category',instance_id=category.id,category_name=category.name,action='edit')
                res['status'] = 200
                res['message'] = 'Category edited successfully'

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
    def delete(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            body = json.loads(req.body)
            category_id = body.get('id')
            category = Category.objects.filter(store = req.user.store, id=category_id).first()
            if category:
                category.deleted = True
                category.save()
                Log.objects.create(user = req.user,store = req.user.store,instance='category',instance_id=category.id,category_name=category.name,action='delete')
                res['message'] = 'Category deleted successfully'
                res['status'] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])

    

class RouterView(View):
    def get(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            user = req.user
            store = user.store
            routers = list(Router.objects.filter(store=store).order_by("-id").values('id','category__name','emei','serial_number','created_at'))
            res['routers'] = routers
            del res['message']
            res['status'] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
    def post(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            user = req.user
            body = json.loads(req.body)
            routers = body.get('routers')
            imported = 0
            for new_router in routers:
                try:
                    category = Category.objects.filter(name=new_router.get('category')).first()
                    if category:
                        if not Router.objects.filter(id=new_router.get('id')).exists():
                            if category:
                                router = Router.objects.create(store = user.store,category=category,emei=new_router.get('emei'),serial_number=new_router.get('serial_number'))
                                router.save()
                                Log.objects.create(user = user,store = user.store,instance='router',instance_id=router.id,emei=router.emei,action='add')
                                imported += 1

                        elif Router.objects.filter(id=new_router.get('id'),deleted=True).exists():
                                router = Router.objects.get(id=new_router.get('id'))
                                router.category = category
                                router.emei=new_router.get('emei')
                                router.serial_number=new_router.get('serial_number')
                                router.deleted = False
                                router.save()
                                Log.objects.create(user = user,store = user.store,instance='router',instance_id=router.id,emei=router.emei,action='add')
                                imported += 1
                    else:
                        logger.error(f"{new_router.get('category')} not found")
                                

                except Exception as e:
                    logger.exception(e)
            res['status'] = 200
            res['message'] = f'{imported} routers imported'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])

    def put(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            body = json.loads(req.body)
            router_id = body.get('id')
            category = body.get('category')
            serial_number = body.get('serial_number')
            emei = body.get('emei')
            
            category_instance = Category.objects.filter(id=category).first()
            router = Router.objects.filter(store = req.user.store,id=router_id).first()
            router.category = category_instance
            router.serial_number = serial_number
            router.emei = emei
            router.save()
            Log.objects.create(user = req.user,store = req.user.store,instance='router',instance_id=router.id,emei=router.emei,action='edit')
            res['status'] = 200
            res['message'] = 'Router edited successfully'

        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
    def delete(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            body = json.loads(req.body)
            router_id = body.get('id')
            router = Router.objects.filter(store = req.user.store, id=router_id).first()
            if router:
                router.deleted = True
                router.save()
                Log.objects.create(user = req.user,store = req.user.store,instance='router',instance_id=router.id,emei=router.emei,action='delete')
                logger.info(f'{req.user.username} deleted router with sn: {router.serial_number} - emei : {router.emei}')
                res['message'] = 'Router deleted successfully'
                res['status'] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
    def patch(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            body = json.loads(req.body)
            router_id = body.get('id')
            if router_id:
                router = Router.objects.filter(store=req.user.store,id=router_id).first()
                if router:
                    router.shipped = not router.shipped
                    router.save()
                    res['message'] = 'Router updated successfully'
                    res['status'] = 200
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])



class RouterSuggestions(View):
    def get(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try :
            user = req.user
            value = req.GET.get('value')
            routers = list(Router.objects.filter(Q(store = user.store) & Q(deleted = False) & (Q(emei__startswith=value) | Q(serial_number__startswith=value))).values('emei'))
            res['status'] = 200
            res['routers'] = routers
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
class CategorySuggestions(View):
    def get(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try :
            user = req.user
            value = req.GET.get('value')
            categories = list(Category.objects.filter(store = user.store ,name__startswith=value,deleted=False).values('name'))
            res['status'] = 200
            res['categories'] = categories
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
class LogsView(View):
    model = Log
    paginate_by = 20
    template_name = "main/logs/list.html"

    def get(self,request):
        user = request.user
        logs = Log.objects.filter(store=user.store).order_by('-id')
        actions = Action.objects.filter(store=user.store).order_by('-id')
        context = {}
        query = self.request.GET
        context['users'] = User.objects.filter(Q(store = request.user.store) | Q(is_superuser = True))
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
                    logs = logs.filter(user = searched_user_instance)
                else:
                    logs = logs.none()
            if action:
                logs = logs.filter(action=action)
            if instance:
                logs = logs.filter(instance=instance)
            logs_paginator = Paginator(logs,10)
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
            action_reason =  query.get('action_reason')
            searched_user = query.get('action_user')


            if router1:
                actions = actions.filter(router1=Router.objects.filter(emei=router1).first())
            
            if searched_user:
                searched_user_instance = User.objects.filter(store=user.store, id=searched_user).first()
                if searched_user:
                    actions = actions.filter(user = searched_user_instance)
                else:
                    actions = actions.none()
            
            if action:
                actions = actions.filter(action=action)
            
            if action_reason:
                actions = actions.filter(reason=action_reason)

            actions_paginator = Paginator(actions,10)
            actions = actions_paginator.page(actions_page)
            context['actions'] = actions
            context['actions_obj'] = actions_paginator.get_elided_page_range(number=actions_page, 
                                            on_each_side=1,
                                            on_ends=1)
            
        except Exception as e:
            logger.exception(e)

        return render(request,'main/logs/list.html',context=context)
    
class LogsOpsView(View):
    def get(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try :
            logs = list(Log.objects.filter(store = req.user.store).order_by('-id').values('user__username','action','instance','emei','category_name','instance_id','created_at'))
            res['logs'] = logs
            res['status'] = 200
            del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
class ActionsView(View):
    def get(self,req):
        return render(req,'main/actions/main.html')
    
    def post(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try :
            store = req.user.store
            body = json.loads(req.body)
            action_type = body.get('action')
            imei = body.get('imei')
            sn1 = body.get('sn1')
            type1 = body.get('type1')
            imei2 = body.get('imei2')
            sn2 = body.get('sn2')
            type2 = body.get('type2')
            order_number = body.get('order_number')
            router1 = Router.objects.filter(store=store,emei = imei,serial_number=sn1,category__type=type1).first()
            router2 = None

            if not router1:
                res['message'] = "We can't find the router router with the provided details"
                return JsonResponse(res,status=res['status'])
            if imei2:
                router2 = Router.objects.filter(store=store,emei = imei2,serial_number=sn2,category__type=type2).first()
                if not router2:
                    res['message'] = "We can't find the second router with the provied details"
                    return JsonResponse(res,status=res['status'])
            
            if router1:
                action = Action.objects.create(user = req.user,store=req.user.store,router=router1,action=action_type,comment=body.get('comment'))
                if action_type == 'return':
                    action.reason = body.get('return_reason')
                    router1.status = Router.STATUSES[3][0]#return
                    router1.reason = body.get('return_reason')
                    emails = list(store.user_set.all().values_list('email',flat=True))
                    text = f"""Router with IMEI {router1.emei} was returned
reason: {router1.reason}
comment: {body.get('comment')}
                            """
                    send_email(emails,'Router Returned',text)
                elif action_type == 'swap':
                    action.reason = body.get('swap_reason')
                    action.router2 = router2
                    router1.status = Router.STATUSES[4][0] #swap
                    router1.reason = body.get('return_reason')
                    router2.status = Router.STATUSES[3][0] #return
                elif action_type == 'collect':
                    router1.status = Router.STATUSES[2][0]
                    action.order_number = order_number
                elif action_type == 'sale':
                    router1.status = Router.STATUSES[1][0]
                    action.order_number = order_number
                    emails = list(store.user_set.all().values_list('email',flat=True))
                    text = f"Router with IMEI {router1.emei} was sold"
                    send_email(emails,'New sale',text)

                action.save()
                router1.save()
                if router2:router2.save()

                res['status'] = 200
                del res['message']
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])
    
    def put(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            if not req.user.role == "store_manager":
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            body = json.loads(req.body)
            action_id = body.get('id')
            action =  Action.objects.filter(id=action_id,store = req.user.store).first()
            if action:
                action.shipped = False if action.shipped else True
                action.save()
                res['status'] = 200
                res['message'] = 'Action edited successfully'
            else:
                res['message'] = 'Action not found'
        except Exception as e:
            logger.exception(e)
        return JsonResponse(res,status=res['status'])

class ReturnView(View):
    def get(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        context = {}
        try:
            routers_page = req.GET.get('router_page') if req.GET.get('router_page') else 1 
            routers  = Router.objects.filter(store=req.user.store,status="return")
            context['categories'] = Category.objects.filter(store=req.user.store,deleted=False)
            context['routers_count'] = routers.count()
            routers_paginator = Paginator(routers,10)
            routers = routers_paginator.page(routers_page)
            context['routers_paginator'] = routers_paginator
            context['routers'] = routers
            context['routers_obj'] = routers_paginator.get_elided_page_range(number=routers_page, 
                                            on_each_side=1,
                                            on_ends=1)
        except Exception as e:
            logger.exception(e)
        return render(req,'main/return/index.html',context=context)
