from django.shortcuts import render, redirect
import requests

def signIn(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        api_url = "http://127.0.0.1:8000/api/signin/"
        response = requests.post(api_url, json={"username": username, "password": password})
        if response.status_code == 200:
            return redirect('/userCrud/')
        else:
            return render(request, "Capture_auth/sign-in.html", {"error": "Invalid credentials."})
    return render(request, "Capture_auth/sign-in.html")



def signUp(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        api_url = "http://127.0.0.1:8000/api/signup/"
        response = requests.post(api_url, data={"username": username, "email": email, "password": password})

        if response.status_code == 201:
            return redirect('/') 
        else:
            return render(request, "Capture_auth/sign-up.html", {"error": "Signup failed, please try again."})
    
    return render(request, "Capture_auth/sign-up.html")

def adminDashboard(request):
    return render(request, "Admin/admin-dashboard.html")

def userCrud(request):
    return render(request, "Admin/crud-user.html")