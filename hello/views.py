# mysite/hello/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone

from .models import Booking, Package, Review


def home(request):
    return render(request, "hello/index.html")

def about(request):
    return render(request, "hello/about.html")

def contact(request):
    return render(request, "hello/contact.html")

def help_page(request):
    return render(request, "hello/help.html")

def privacy(request):
    return render(request, "hello/privacy.html")

def terms(request):
    return render(request, "hello/terms.html")

def cookies(request):
    return render(request, "hello/cookies.html")

def enquiry(request):
    return render(request, "hello/enquiry.html")

def packages(request):
    return render(request, "hello/packages.html")



@login_required
def dashboard(request):
    today = timezone.localdate()
    bookings = Booking.objects.filter(user=request.user)

    stats = {
        "total_bookings": bookings.count(),
        "upcoming_count": bookings.filter(travel_date__gte=today).count(),
        "total_spent": bookings.aggregate(s=Sum("total_price"))["s"] or 0,
        "confirmed_count": bookings.filter(status="CONFIRMED").count(), 
    }

    recent_bookings = bookings.order_by("-booking_date")[:5]
    reviews = Review.objects.filter(user=request.user).select_related("package")[:5]
    recommendations = Package.objects.filter(is_available=True).exclude(bookings__user=request.user)[:3]

 
    upcoming_booking = bookings.filter(travel_date__gte=today).order_by("travel_date").first()

    ctx = {
        "stats": stats,
        "recent_bookings": recent_bookings,
        "reviews": reviews,
        "recommendations": recommendations,
        "upcoming_booking": upcoming_booking,
    }
    return render(request, "hello/dashboard.html", ctx)



def login_view(request):
    if request.method == "POST":
        identifier = (request.POST.get("email") or request.POST.get("username") or "").strip()
        password   = request.POST.get("password") or ""
        remember   = request.POST.get("remember") == "on"
        next_url   = request.POST.get("next") or request.GET.get("next")

        User = get_user_model()
        user = None

        try:
           
            u = User.objects.get(Q(email__iexact=identifier) | Q(username__iexact=identifier))
            user = authenticate(request, username=u.username, password=password)
        except User.DoesNotExist:
           
            user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)

        
            if not remember:
                request.session.set_expiry(0)

            messages.success(request, f"Welcome back, {user.get_username()}!")
            return redirect(next_url or "dashboard")
        else:
            messages.error(request, "Invalid email/username or password.")

    context = {"next": request.GET.get("next", "")}
    return render(request, "hello/login.html", context)



def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")



def signup_view(request):
    User = get_user_model()

    if request.method == "POST":
        username  = (request.POST.get("username") or "").strip()
        email     = (request.POST.get("email") or "").strip()
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

      
        if not username or not email or not password1:
            messages.error(request, "All fields are required.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).exists():
            messages.error(request, "Username or email already in use.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            messages.success(request, "Account created successfully. Welcome aboard!")
            return redirect("dashboard")

    return render(request, "hello/signup.html")
