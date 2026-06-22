from django.contrib import admin
from advanced_prompt.models import AccountantInfo, AccountantCategories, DisclaimerInfo, ImportAdvisorData, UserInfo, Panel, ChatLogs, MessageLogs, PanelChatLogs, PanelMessageLogs, Experties, ForgetPassword
from django import forms
from django.forms.widgets import TextInput
import pandas as pd
from django.utils.html import format_html
from django.contrib import messages
from django.core.files import File
from django.utils import timezone
from django.core.exceptions import ValidationError
import zipfile



admin.site.register(Experties)

# admin.site.register(Experties, ExpertiesAdmin)



class AccountantCategoriesForm(forms.ModelForm):
    color = forms.CharField(max_length=7, widget=TextInput(attrs={'type': 'color'}))

    class Meta:
        model = AccountantCategories
        fields = '__all__'

class AccountantInfoAdmin(admin.ModelAdmin):
    list_display = ('header_text','tagline_text','description','context','accountant_image', 'category_id','rating')

admin.site.register(AccountantInfo, AccountantInfoAdmin)

class AccountantCategoryAdmin(admin.ModelAdmin):
    form = AccountantCategoriesForm
    list_display = ('category', 'color')


admin.site.register(AccountantCategories, AccountantCategoryAdmin)


class DisclaimerInfoAdmin(admin.ModelAdmin):
    list_display = ('disclaimer_text',)

admin.site.register(DisclaimerInfo, DisclaimerInfoAdmin)


class ImportAdvisorDataAdmin(admin.ModelAdmin):
    list_display = ('title','advisor_data','advisor_images_data', 'upload_datetime', 'import_datetime')
    readonly_fields = ('upload_datetime','import_datetime', 'is_disabled')
    actions = ['test_action', 'enable_files', 'disable_files']

    def enable_files(self, request, queryset):
        queryset.update(is_disabled=False)
        self.message_user(request, "Selected files are now enabled for import.")

    enable_files.short_description = "Enable selected files"

    def disable_files(self, request, queryset):
        queryset.update(is_disabled=True)
        self.message_user(request, "Selected files are now disabled for import.")

    disable_files.short_description = "Disable selected files"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @admin.action(description='Import Data')
    def test_action(self, request, queryset):
        for obj in queryset:
            if obj.is_disabled:
                self.message_user(request, f"File {obj.advisor_data} is disabled and cannot be imported.")
            else:
                try:
                    if not obj.advisor_images_data.name.endswith('.zip'):
                        raise ValidationError("Only Zip files (.zip) are allowed for images import.")
                    # Specify the path to the zip file
                    zip_file_path = obj.advisor_images_data

                    # Open the zip file
                    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                        # Extract all the contents of the zip file to a directory
                        zip_ref.extractall('./media/occupational_images')
                    if not obj.advisor_data.name.endswith('.xlsx'):
                        raise ValidationError("Only Excel files (.xlsx) are allowed for import.")
                    
                    df = pd.read_excel(obj.advisor_data)
                except FileNotFoundError:
                    self.message_user(request, f"File {obj.advisor_data} not found.")
                    continue  # Skip to the next iteration
                except ValidationError as e:
                    self.message_user(request, str(e))
                    continue  # Skip to the next iteration

                required_columns = [
                    'Header', 'Tagline', 'Description of questions', 'Prompt', 'Category',
                    'Image', 'Color'
                ]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    self.message_user(request, f"File {obj.advisor_data} is missing columns: {', '.join(missing_columns)}.")
                    continue  # Skip to the next iteration

                for index, row in df.iterrows():
                    header_text = row['Header']
                    tagline_text = row['Tagline']
                    description = row['Description of questions']
                    context = row['Prompt']
                    category_name = row['Category']
                    image_path = row['Image']  # Assuming the column name in the Excel file is 'Image'
                    color = row['Color']  # Assuming the column name in the Excel file is 'Color'

                    try:
                        accountant_info = AccountantInfo.objects.get(header_text=header_text)
                        # Update the existing record with the new values
                        accountant_info.tagline_text = tagline_text
                        accountant_info.description = description
                        accountant_info.context = context
                        category, _ = AccountantCategories.objects.get_or_create(category=category_name)
                        category.color = color  # Update the color field
                        category.save()
                        accountant_info.category_id = category
                        accountant_info.accountant_image = image_path
                        accountant_info.save()

                    except AccountantInfo.DoesNotExist:
                        # Create a new record since the header_text doesn't exist
                        category, _ = AccountantCategories.objects.get_or_create(category=category_name, color=color)
                        accountant_info = AccountantInfo.objects.create(
                            header_text=header_text,
                            tagline_text=tagline_text,
                            description=description,
                            context=context,
                            category_id=category,
                            accountant_image=image_path,
                            
                        )

                obj.import_datetime = timezone.now()
                obj.is_disabled = True  # Disable the file after import
                obj.save()
                self.message_user(request, f"File {obj.advisor_data} imported successfully and disabled.")

    test_action.short_description = 'Import selected files'

admin.site.register(ImportAdvisorData, ImportAdvisorDataAdmin)

admin.site.register(UserInfo)

class PanelAdmin(admin.ModelAdmin):
    inlines = ['accountant_info']
admin.site.register(Panel)

class ChatLogAdmin(admin.ModelAdmin):
    # class Meta:
    #     model = AccountantInfo
    #     fields = ['header_text',]

    list_display = ['advisor_id','user_id']
    # def related_field_message(self, obj):
    #     return obj.advisor_id.header_text


admin.site.register(ChatLogs,ChatLogAdmin)

# class MessageLogAdmin(admin.ModelAdmin):
#     list_display = ['response_message','prompt_message','message_type','chat_id']
class MessageLogsAdmin(admin.ModelAdmin):
    list_display = ['content', 'message_type']  # Update the list_display
admin.site.register(MessageLogs, MessageLogsAdmin)

# admin.site.register(MessageLogs,MessageLogAdmin)

class PanelChatLogAdmin(admin.ModelAdmin):
    # class Meta:
    #     model = AccountantInfo
    #     fields = ['header_text',]

    list_display = ['panel_id','user_id']
    # def related_field_message(self, obj):
    #     return obj.advisor_id.header_text


admin.site.register(PanelChatLogs,PanelChatLogAdmin)

class PanelMessageLogAdmin(admin.ModelAdmin):
    list_display = ['response_message','prompt_message','panel_chat_id','advisor_id']

admin.site.register(PanelMessageLogs,PanelMessageLogAdmin)

# admin.site.register(Experties,ExpertiesAdmin)


class ForgetPasswordAdmin(admin.ModelAdmin):
    list_display = ('email', 'code')

admin.site.register(ForgetPassword, ForgetPasswordAdmin)