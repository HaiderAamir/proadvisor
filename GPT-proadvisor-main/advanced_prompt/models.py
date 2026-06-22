from django.db import models
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_xlsx_file(value):
    if not value.name.endswith('.xlsx'):
        raise ValidationError("Only Excel files (.xlsx) are allowed for advisor import.")
    

def validate_zip_file(value):
    if not value.name.endswith('.zip'):
        raise ValidationError("Only Zip files (.zip) are allowed for advisor images import.")
    

class ImportAdvisorData(models.Model):
    title = models.CharField(max_length=100)
    advisor_data = models.FileField(validators=[validate_xlsx_file])
    advisor_images_data = models.FileField(validators=[validate_zip_file])
    upload_datetime = models.DateTimeField(auto_now_add=True)
    import_datetime = models.DateTimeField(null=True, blank=True)
    is_disabled = models.BooleanField(default=False, verbose_name='Import Status')


class AccountantCategories(models.Model):
    category = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return self.category

class UserInfo(models.Model):
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)  # Use EmailField for email addresses
    password = models.CharField(max_length=50)
    organization_name = models.CharField(max_length=200, null=True)
    location = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, null=True)
    birthdate = models.DateField(null=True, blank=True)
    favorite_advisors = models.ManyToManyField('AccountantInfo', through='FavoriteAdvisor', related_name='favorited_by')

    @classmethod
    def check_email(cls, email):
        try:
            return cls.objects.get(email=email)
        except cls.DoesNotExist:
            return False

    def __str__(self):
        return self.email

class AccountantInfo(models.Model):
    header_text = models.CharField(max_length=500)
    tagline_text = models.CharField(max_length=1000)
    description = models.TextField()
    context = models.TextField()
    question = models.TextField()
    category_id = models.ForeignKey(AccountantCategories, on_delete=models.CASCADE)
    accountant_image = models.ImageField(upload_to='media/images/')
    rating = models.IntegerField(default=1)
    user_id = models.ForeignKey(UserInfo, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.header_text

class FavoriteAdvisor(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    advisor = models.ForeignKey(AccountantInfo, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'advisor']

class DisclaimerInfo(models.Model):
    disclaimer_text = models.TextField()

class ImportAdvisorData(models.Model):
    title = models.CharField(max_length=100)
    advisor_data = models.FileField(validators=[validate_xlsx_file])
    advisor_images_data = models.FileField(validators=[validate_zip_file])
    upload_datetime = models.DateTimeField(auto_now_add=True)
    import_datetime = models.DateTimeField(null=True, blank=True)
    is_disabled = models.BooleanField(default=False, verbose_name='Import Status')

class ChatLogs(models.Model):
    advisor_id = models.ForeignKey(AccountantInfo, on_delete=models.CASCADE)
    user_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)

class MessageLogs(models.Model):
    chat_id = models.ForeignKey(ChatLogs, on_delete=models.CASCADE)
    role = models.CharField(max_length=255)
    content = models.TextField()
    message_type = models.CharField(max_length=1)

class Panel(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    panel_name = models.CharField(max_length=500)
    panel_id = models.CharField(max_length=200)
    panel_topic = models.CharField(max_length=200)
    accountant_info = models.ManyToManyField(AccountantInfo)

    def __str__(self):
        return self.panel_name

class PanelChatLogs(models.Model):
    panel_id = models.ForeignKey(Panel, on_delete=models.CASCADE)
    user_id = models.ForeignKey(UserInfo, on_delete=models.CASCADE)

class PanelMessageLogs(models.Model):
    response_message = models.TextField()
    prompt_message = models.TextField()
    panel_chat_id = models.ForeignKey(PanelChatLogs, on_delete=models.CASCADE)
    advisor_id = models.ForeignKey(AccountantInfo, on_delete=models.CASCADE)
    created_at= models.DateTimeField(default=timezone.now())

class Experties(models.Model):
    name = models.CharField(max_length=100)
    tag_line = models.CharField(max_length=200)
    image = models.ImageField(upload_to='experties/')
    category_id = models.ForeignKey(AccountantCategories, on_delete=models.CASCADE)

class ForgetPassword(models.Model):
    email = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    code = models.CharField(max_length=8)

    def __str__(self):
        return self.code
