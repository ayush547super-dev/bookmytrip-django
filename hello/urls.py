from django.urls import path
from . import views

urlpatterns = [
    # --- Main Pages ---
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("help/", views.help_page, name="help"),
    path("enquiry/", views.enquiry, name="enquiry"),
    path("privacy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("cookies/", views.cookies, name="cookies"),

    # --- Packages ---
    path("packages/", views.packages, name="packages"),
    path("packages/<slug:slug>/", views.package_detail, name="package_detail"),

    # --- Booking System ---
    path("book/<slug:slug>/", views.book_package, name="book_package"),
    path("booking/thanks/<int:booking_id>/", views.booking_thanks, name="booking_thanks"),

    # --- User Dashboard ---
    path("dashboard/", views.dashboard, name="dashboard"),

    # --- Authentication ---
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup_view, name="signup"),
]
