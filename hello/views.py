from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Package, Review


# ---------- Static pages ----------
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


# ---------- Packages ----------
def packages(request):
    """Display all available travel packages (from DB)."""
    qs = (
        Package.objects.filter(is_available=True)
        .select_related("destination")
        .order_by("-created_at")
    )
    return render(request, "hello/packages.html", {"packages": qs})


def package_detail(request, slug):
    """Show details for one package."""
    package = get_object_or_404(
        Package.objects.select_related("destination"),
        slug=slug
    )
    reviews = Review.objects.filter(package=package).select_related("user")
    return render(request, "hello/package_detail.html", {"package": package, "reviews": reviews})


# ---------- Dashboard ----------
@login_required
def dashboard(request):
    today = timezone.localdate()
    bookings = Booking.objects.filter(user=request.user).select_related("package")

    stats = {
        "total_bookings": bookings.count(),
        "upcoming_count": bookings.filter(travel_date__gte=today).count(),
        "total_spent": bookings.aggregate(s=Sum("total_price"))["s"] or 0,
        "confirmed_count": bookings.filter(status="CONFIRMED").count(),
    }

    ctx = {
        "stats": stats,
        "recent_bookings": bookings.order_by("-booking_date")[:5],
        "reviews": Review.objects.filter(user=request.user).select_related("package")[:5],
        "recommendations": (
            Package.objects.filter(is_available=True)
            .exclude(bookings__user=request.user)
            .select_related("destination")[:3]
        ),
        "upcoming_booking": bookings.filter(travel_date__gte=today).order_by("travel_date").first(),
    }
    return render(request, "hello/dashboard.html", ctx)


# ---------- Auth ----------
def login_view(request):
    if request.method == "POST":
        identifier = (request.POST.get("email") or request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        remember = request.POST.get("remember") == "on"
        next_url = request.POST.get("next") or request.GET.get("next")

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
                request.session.set_expiry(0)  # session ends on browser close
            messages.success(request, f"Welcome back, {user.get_username()}!")
            return redirect(next_url or "dashboard")
        messages.error(request, "Invalid email/username or password.")

    return render(request, "hello/login.html", {"next": request.GET.get("next", "")})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


def signup_view(request):
    User = get_user_model()
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip()
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


# ---------- Booking ----------
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["number_of_people", "travel_date"]
        widgets = {
            "travel_date": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "number_of_people": forms.NumberInput(attrs={"min": 1, "class": "input"}),
        }

    def clean_travel_date(self):
        date = self.cleaned_data["travel_date"]
        if date < timezone.localdate():
            raise forms.ValidationError("Travel date cannot be in the past.")
        return date

    def clean_number_of_people(self):
        n = self.cleaned_data["number_of_people"]
        if n is None or n < 1:
            raise forms.ValidationError("Please enter at least 1 traveler.")
        return n


@login_required(login_url="/login/")
def book_package(request, slug):
    """
    Create a booking for the given package.
    If user was redirected here by login_required, login_view will send them back via ?next.
    """
    package = get_object_or_404(
        Package.objects.select_related("destination"),
        slug=slug,
        is_available=True
    )

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.package = package
            booking.total_price = (package.price or Decimal("0")) * Decimal(form.cleaned_data["number_of_people"])
            booking.save()
            messages.success(request, f"Booking created successfully! #{booking.id}")
            return redirect(reverse("booking_thanks", kwargs={"booking_id": booking.id}))
        messages.error(request, "Please fix the errors below.")
    else:
        form = BookingForm(initial={"number_of_people": 1})

    return render(request, "hello/booking_form.html", {"form": form, "package": package})


@login_required(login_url="/login/")
def booking_thanks(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("package", "package__destination"),
        id=booking_id,
        user=request.user
    )
    return render(request, "hello/booking_thanks.html", {"booking": booking})
