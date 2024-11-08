from django.db import models

class Brand(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Category(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Merchant(models.Model):
    title = models.CharField(max_length=64)
    brands = models.ManyToManyField(Brand, related_name='merchants')  # Many-to-many relationship with Brand

    def __str__(self):
        return self.title

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('merchant', 'Merchant'),
    ]
    
    telegram_id = models.BigIntegerField(unique=True)  
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)  
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True) 
    birthday = models.DateField(null=True, blank=True)  
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    location = models.CharField(max_length=255, blank=True, null=True)  
    language = models.CharField(max_length=10, choices=[('az', 'Azerbaijani'), ('en', 'English'), ('tr', 'Turkish'), ('ru', 'Russian')])
    merchant_role = models.ForeignKey(Merchant, on_delete=models.CASCADE, null=True, blank=True)  
    favorite_categories = models.ManyToManyField(Category, blank=True)
    favorite_brands = models.ManyToManyField(Brand, blank=True) 
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_merchant_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    min_discount = models.IntegerField(null=True, blank=True) 
    max_discount = models.IntegerField(null=True, blank=True) 
    min_time = models.TimeField(null=True, blank=True)  
    max_time = models.TimeField(null=True, blank=True)  

    def is_admin(self):
        return self.role == 'admin'
    def is_merchant(self):
        return self.role == 'merchant'
    def is_user(self):
        return self.role == 'user'
    def has_merchant_admin_privileges(self):
        return self.is_merchant() and self.is_merchant_admin
    
    def assign_role(self, role):
        if role in dict(self.ROLE_CHOICES).keys():
            self.role = role
            self.save()
        else:
            raise ValueError(f"{role} is not a valid role. Choose from {', '.join(dict(self.ROLE_CHOICES).keys())}.")
    
    def __str__(self):
        return self.username
    

from decimal import Decimal

class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)  
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)  
    image_url = models.URLField(max_length=200, blank=True)  
    url = models.URLField(max_length=200, blank=True)  
    click_count = models.IntegerField(default=0)  
    discount_start_date = models.DateTimeField(null=True, blank=True) 
    discount_end_date = models.DateTimeField(null=True, blank=True)  
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    normal_price = models.DecimalField(max_digits=10, decimal_places=2) 
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Yeni alan
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.discount_price and self.discount_percentage:
            self.discount_percentage = (1 - (Decimal(self.discount_price) / Decimal(self.normal_price))) * 100
        elif self.discount_percentage and not self.discount_price:
            self.discount_price = Decimal(self.normal_price) * (1 - (Decimal(self.discount_percentage) / 100))
        elif self.discount_price and not self.discount_percentage:
            self.discount_percentage = (1 - (Decimal(self.discount_price) / Decimal(self.normal_price))) * 100

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Recommendations(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)  
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Recommendation by {self.user.username}: {self.description[:20]}'


class Feedback(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE) 
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback from {self.user.username}: {self.description[:20]}'


class Stats(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    views = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    user = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL)   
    created_at = models.DateTimeField(auto_now_add=True)


class SavedProduct(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)  
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='saved_by') 
    saved_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f'{self.user.username} saved {self.product.name}'


