#region imports
from django.db import models
#endregion


#region user model
class User(models.Model):
    class RoleChoices(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        USER = 'USER', 'User'
        AGENCY = 'AGENCY', 'Agency'

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150,unique=True)
    password = models.CharField(max_length=255)  
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)  
    role = models.CharField(
        max_length=50,
        choices=RoleChoices.choices,
        default=RoleChoices.USER
    )

    def __str__(self):
        return self.username
#endregion
 
class Membership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    membership_type = models.CharField(max_length=50)  # e.g., 'Basic', 'Premium'
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.membership_type}"

#region profile models
class CompanyProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/')
    url = models.URLField()
    contact_no = models.CharField(max_length=20)
 
    def __str__(self):
        return self.name
 
class EmployeeProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='employee_images/')
    designation = models.CharField(max_length=100)
    emp_id = models.CharField(max_length=50, unique=True)
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE)
 
    def __str__(self):
        return self.name
#endregion

class VideoRecording(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recordings")
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    video_url = models.URLField()

    def __str__(self):
        return f"{self.title} by {self.user.username}"