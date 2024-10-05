from django.db import models

class Brand(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Category(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title



class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('moderator', 'Moderator'),
        # Add more roles as needed
    ]
    
    telegram_id = models.BigIntegerField(unique=True)  # Unique Telegram user ID
    username = models.CharField(max_length=100, unique=True)  # Telegram username
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)  # Optional last name
    birthday = models.DateField(null=True, blank=True)  # User's birthday
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    location = models.CharField(max_length=255, blank=True)  # Optional location
    language = models.CharField(max_length=10, choices=[('az', 'Azerbaijani'), ('en', 'English'), ('tr', 'Turkish'), ('ru', 'Russian')])
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')  # Default role is 'user'
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_admin(self):
        return self.role == 'admin'
    def is_moderator(self):
        return self.role == 'moderator'
    def is_user(self):
        return self.role == 'user'
    
    def assign_role(self, role):
        if role in dict(self.ROLE_CHOICES).keys():
            self.role = role
            self.save()
        else:
            raise ValueError("Invalid role provided.")
    def __str__(self):
        return self.username
    

class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)  # Link to Brand model
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # Link to Category model
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)  # Optional description
    image_url = models.URLField(max_length=200, blank=True)  # URL for the product image
    url = models.URLField(max_length=200, blank=True)  # URL for the product page
    click_count = models.IntegerField(default=0)  # Count of how many times the product was clicked
    discount_start_date = models.DateTimeField(null=True, blank=True)  # Start date of the discount
    discount_end_date = models.DateTimeField(null=True, blank=True)  # End date of the discount
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Discounted price
    normal_price = models.DecimalField(max_digits=10, decimal_places=2)  # Original price
    is_active = models.BooleanField(default=True)  # To track if the product is active
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Recommendations(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)  # Link to User model
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Recommendation by {self.user.username}: {self.description[:20]}'


class Feedback(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)  # Link to User model
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback from {self.user.username}: {self.description[:20]}'


class Stats(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Link to Product model
    views = models.IntegerField(default=0)  # Number of views
    clicks = models.IntegerField(default=0)  # Number of clicks
    purchases = models.IntegerField(default=0)  # Number of purchases
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Stats for {self.product.name}'
