from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Destination(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_date']
        verbose_name_plural = "Destinations"

    def __str__(self):
        return f"{self.name}, {self.country}"


class Package(models.Model):
    CATEGORY_CHOICES = [
        ('adventure', 'Adventure'),
        ('beach', 'Beach'),
        ('city', 'City'),
        ('cultural', 'Cultural'),
        ('luxury', 'Luxury'),
        ('family', 'Family'),
        ('honeymoon', 'Honeymoon'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, help_text="Used in the package URL.")
    destination = models.ForeignKey('Destination', on_delete=models.CASCADE, related_name="packages")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Packages"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_available']),
        ]

    def __str__(self):
        return self.title

    def _ensure_unique_slug(self):
        if self.slug:
            return
        base = slugify(self.title) or f"package-{self.pk or 'new'}"
        candidate = base
        i = 1
        Model = type(self)
        while Model.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            i += 1
            candidate = f"{base}-{i}"
        self.slug = candidate

    def save(self, *args, **kwargs):
        self._ensure_unique_slug()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("package_detail", kwargs={"slug": self.slug})


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name="bookings")
    booking_date = models.DateTimeField(auto_now_add=True)
    travel_date = models.DateField()
    number_of_people = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        ordering = ['-booking_date']
        verbose_name_plural = "Bookings"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['travel_date']),
            models.Index(fields=['booking_date']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(number_of_people__gte=1), name="booking_people_gte_1"),
            models.CheckConstraint(check=models.Q(total_price__gte=0), name="booking_total_price_gte_0"),
        ]

    def __str__(self):
        return f"Booking #{self.id} • {self.user.username} • {self.package.title}"

    def save(self, *args, **kwargs):
        if self.package_id and (self.total_price is None or self.total_price == 0):
            per = self.package.price or Decimal('0')
            qty = Decimal(self.number_of_people or 0)
            self.total_price = per * qty
        super().save(*args, **kwargs)


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Reviews"
        unique_together = [('user', 'package')]
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.package.title} • {self.rating}/5 by {self.user.username}"
