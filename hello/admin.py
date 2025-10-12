from django.contrib import admin
from .models import Destination, Package, Booking, Review


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "added_date")
    list_filter = ("country", "added_date")
    search_fields = ("name", "country", "description")
    ordering = ("name",)
    date_hierarchy = "added_date"


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("title", "destination", "category", "price", "is_available", "created_at")
    list_filter = ("category", "is_available", "destination", "created_at")
    search_fields = ("title", "description", "destination__name")
    autocomplete_fields = ("destination",)
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_available",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "package",
        "travel_date",
        "number_of_people",
        "total_price",
        "status",
        "booking_date",
    )
    list_filter = ("status", "travel_date", "booking_date")
    search_fields = ("user__username", "user__email", "package__title")
    autocomplete_fields = ("user", "package")
    readonly_fields = ("booking_date",)
    ordering = ("-booking_date",)
    list_editable = ("status",)
    date_hierarchy = "travel_date"

    fieldsets = (
        ("Booking Details", {
            "fields": ("user", "package", "travel_date", "number_of_people", "total_price", "status")
        }),
        ("System Info", {
            "fields": ("booking_date",),
            "classes": ("collapse",)
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("package", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("package__title", "user__username", "comment")
    autocomplete_fields = ("user", "package")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
