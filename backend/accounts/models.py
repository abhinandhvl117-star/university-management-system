from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        
        role = extra_fields.get('role', None) 
        if role is None:
            raise ValueError('Role is required')
        if role not in self.model.Role.values:
            raise ValueError(f'Invalid role {role}')
        
        if role == self.model.Role.TEACHER:
            approval = self.model.ApprovalStatus.PENDING
        else:
            approval = self.model.ApprovalStatus.APPROVED
            
        email = self.normalize_email(email).lower()
        extra_fields.setdefault('approval_status', approval)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', self.model.Role.ADMIN)
        extra_fields.setdefault('approval_status', self.model.ApprovalStatus.PENDING)
        extra_fields.setdefault('account_status', self.model.AccountStatus.ACTIVE)
        return self.create_user(email, password, **extra_fields)
    
class User(AbstractUser):
    
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        ADMIN = 'admin', 'Admin'
    class ApprovalStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected' 
    
    class AccountStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DISABLED = 'disabled', 'Disabled'
        
    username = None
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, blank=False,)
    approval_status = models.CharField(max_length=20, choices=ApprovalStatus.choices,  default=ApprovalStatus.PENDING)
    account_status = models.CharField(max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Department(models.Model):
    name = models.CharField(max_length=60, unique=True)
    
    def __str__(self):
        return self.name

class Subject(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='subjects')
    name = models.CharField(max_length=60)
    
    class Meta:
        constraints =[
            models.UniqueConstraint(
                fields = ['department', 'name'],
                name = 'name_must_be_unique_per_department'
            )
        ]
        
    def __str__(self):
        return f'{self.department} - {self.name}'

class ClassGroup(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='classes')
    name = models.CharField(max_length=50)
    academic_year = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'class'
        verbose_name_plural = 'classes'
        
        constraints = [
            models.UniqueConstraint(
                fields = ['department', 'name', 'academic_year'],
                name = 'unique_class_per_department_year'
            )
        ]
        
    def __str__(self):
        return f'name: {self.name }, year: {self.academic_year}, department: {self.department}'
    
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='studentprofile')
    student_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    
    def __str__(self):
        return f"{str(self.user)}. Student ID - {self.student_id}"
          
class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='teacherprofile')
    staff_id = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='teachers')
    
    def __str__(self):
        return f"{str(self.user)}. Staff ID - {self.staff_id}"
    
class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='enrollment')
    classgroup = models.ForeignKey(ClassGroup, on_delete=models.PROTECT, related_name='enrollment')
    roll_no = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'classgroup'],
                name='a_student_cant_enroll_a_class_twice'
            ),
            models.UniqueConstraint(
                fields=['student', 'roll_no', 'classgroup'],
                name='a_student_cant_have_the_same_roll_no_on_a_same_class'
            )
        ]