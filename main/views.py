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
            print(user,store)
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
        return Category.objects.filter(store=user.store)
    
        


