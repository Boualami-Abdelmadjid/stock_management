#Best practice is to divide the imports 
#First import Built-in methods
#Then import Django methods
#Last import custom method written by you

import json

from django.shortcuts import render
from django.views.generic import View
from django.views.generic.list import ListView
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import authenticate, login

from main.models import *
from main.common import *

# Create your views here.

class HomePage(View):
    def get(self,req):
        context = {}
        user = req.user
        #Get 6 categories and routers, display 5 only, if there are more than 6 then we know there is more than 5 and we show the button 
        #that redirect to page that shows all the categories/routers
        categories = Category.objects.filter(store=user.store)[:6]
        routers = Router.objects.filter(store=user.store)[:6]
        context['more_categories'] = len(categories) > 1
        context['more_routers'] = len(routers) > 1
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
                    print(len(password1))
                    res['message'] = 'The password is too short'
                elif username_or_email_exists(username,email):
                    res['message'] = 'Username or email already exists'
                else:
                    print('here')
                    #First create the user instance with the username only
                    user = User.objects.create(username=username,email=email)
                    #Later use set_password method, this method will hash the password of the user instead of leaving it in plain text (For security)
                    user.set_password(password1)
                    user.save()
                    res['status'] = 200
                    del res['message']

                
        except Exception as e:
            print(e)
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
            print(username,password)
            if username and password:
                #Check if a user with the username or email provided exists
                print(username,password)
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
            print(e)
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
            store = req.user.store
            body = json.loads(req.body)
            username = body.get('username')
            role = body.get('role')
            
            added_user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            if added_user:
                added_user.store = store
                added_user.role = role
                added_user.save()
                res['status'] = 200
                res['message'] = 'User added successfully'
            else :
                res['message'] = 'User not found'
        except Exception as e:
            print(e)
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
            print(e)
        return JsonResponse(res,status=res['status'])

        

    

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
            print(e)
        return JsonResponse(res,status=res['status'])

class CreateCategoryView(View):
    def get(self,req):
        return render(req,'main/category/create-category.html')
    def post(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
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

            res['status'] = 200
            del res['message']
        except Exception as e:
            print(e)
        return JsonResponse(res,status=res['status'])
    
class CreateRouterView(View):
    def get(self,req):
        context = {}
        store = req.user.store
        categories = list(Category.objects.filter(store=store).values())
        context['categories'] = categories
        return render(req,'main/router/create-router.html',context=context)
    def post(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
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

            res['status'] = 200
            del res['message']
        except Exception as e:
            print(e)
        return JsonResponse(res,status=res['status'])
    
class CategoriesView(ListView):
    model = Category
    paginate_by = 10
    template_name = 'main/category/list.html'

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(store=user.store).order_by('-id')
    
class CategoryView(View):
    def put(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            body = json.loads(req.body)
            category_id = body.get('id')
            name = body.get('name')
            category_type = body.get('type')

            category = Category.objects.filter(store = req.user.store,id=category_id).first()
            if category:
                category.name = name
                category.type = category_type
                category.save()
                res['status'] = 200
                res['message'] = 'Category edited successfully'

        except Exception as e:
            print(e)
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
                category.delete()
                res['message'] = 'Category deleted successfully'
                res['status'] = 200
        except Exception as e:
            print(e)
        return JsonResponse(res,status=res['status'])

    
class RoutersView(ListView):
    model = Router
    paginate_by = 10
    template_name = 'main/router/list.html'

    def get_queryset(self):
        user = self.request.user
        return Router.objects.filter(store=user.store).order_by('-id')  
    
    def get_context_data(self,**kwargs):
        context = super(RoutersView,self).get_context_data(**kwargs)
        context['categories'] =  Category.objects.filter(store=self.request.user.store)
        return context

class RouterView(View):
    def put(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
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
            res['status'] = 200
            res['message'] = 'Router edited successfully'

        except Exception as e:
            print(e)
        return JsonResponse(res,status=res['status'])
    
    def delete(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try:
            print(req.user.role)
            if req.user.role != "store_manager":
                res['status'] = 403
                res['message'] = "You don't have enough permissions"
                return JsonResponse(res,status=res['status'])
            body = json.loads(req.body)
            router_id = body.get('id')
            router = Router.objects.filter(store = req.user.store, id=router_id).first()
            if router:
                router.delete()
                res['message'] = 'Router deleted successfully'
                res['status'] = 200
        except Exception as e:
            print(e)
        return JsonResponse(res,status=res['status'])



class RouterSuggestions(View):
    def get(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try :
            user = req.user
            value = req.GET.get('value')
            routers = list(Router.objects.filter(Q(store = user.store) & (Q(emei__startswith=value) | Q(serial_number__startswith=value))).values('emei'))
            res['status'] = 200
            res['routers'] = routers
            del res['message']
        except Exception as e:
            print(e)
        return JsonResponse(res,status=res['status'])
    
class CategorySuggestions(View):
    def get(self,req):
        res = {"status":500,"message":"Something wrong hapenned"}
        try :
            user = req.user
            value = req.GET.get('value')
            categories = list(Category.objects.filter(store = user.store ,name__startswith=value).values('name'))
            res['status'] = 200
            res['categories'] = categories
            del res['message']
        except Exception as e:
            print(e)
        return JsonResponse(res,status=res['status'])



