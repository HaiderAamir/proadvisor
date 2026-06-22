from collections import defaultdict
import re
import secrets
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponse, JsonResponse
from .models import AccountantInfo, AccountantCategories, DisclaimerInfo,FavoriteAdvisor, Panel, UserInfo, ChatLogs, MessageLogs, PanelChatLogs, PanelMessageLogs, Experties, ForgetPassword
from django.contrib.auth import get_user_model
import openai
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import json
from django.core.serializers.json import DjangoJSONEncoder
import random
import string
from .models import Panel
from django.shortcuts import get_object_or_404
import requests
from django.forms.models import model_to_dict
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from django.db.models import Q
import os
from django.utils import timezone


def serialize_message_log(message_log):
    return {
        "response_message": message_log.response_message,
        "prompt_message": message_log.prompt_message,
        "message_type": message_log.message_type,
        "chat_id": message_log.chat_id_id  # Assuming 'chat_id' is a foreign key field
    }


def escape_non_visible_characters(text):
    escape_dict = {
        '\a': r'\a',  # Bell (alert)
        '\b': r'\b',  # Backspace
        '\f': r'\f',  # Formfeed
        '\n': r'\n',  # Newline
        '\r': r'\r',  # Carriage Return
        '\t': r'\t',  # Tab
        '\v': r'\v',  # Vertical Tab
        '\0': r'\0',  # Null
        '**': r'\*\*',  # Bold text
        '##': r'\#\#',  # Heading text
    }

    escaped_text = ""
    for char in text:
        if char in escape_dict:
            escaped_text += escape_dict[char]
        else:
            escaped_text += char

    return escaped_text

def generate_8_digit_code():
    # Generate a random 8-digit code
    code = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return code

# panel name creation function
def panel_name_generate(question):
    system_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Generate a topic heading and a group chat title 3 - 4 words long, for the discussion on the following question:"},
            {"role": "user", "content": question}
        ]
    )
    # Extract the responses
    system_message_response = system_response.choices[0].message["content"].strip()

    # Split the response into topic heading and group chat title
    parts = system_message_response.split("Topic Heading:")
    if len(parts) == 2:
        topic_heading, group_chat_title = map(
            str.strip, parts[1].split("Group Chat Title:"))

        # Remove double quotations from the topic heading and group chat title
        topic_heading = topic_heading.strip('""')
        group_chat_title = group_chat_title.strip('""')

        return topic_heading, group_chat_title
    else:
        # Handle the case where the response format is unexpected
        return None, None
        

# def send_email(subject, message, recipient_list):
#     try:
#         send_mail(subject, message, 'haideraamir09@gmail.com', recipient_list, fail_silently=False)
#         return True
#     except Exception as e:
#         print(f"Email sending failed: {str(e)}")
#         return False

def changepassword(request):
    if request.method == 'POST':

        data = json.loads(request.body.decode('utf-8'))

        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        confirm = data.get('confirmPassword')

        if(new_password=='' or old_password=='' or confirm==''):
            return JsonResponse({'message': 'Please  fill all fields'})

        if(new_password!=confirm):
            return JsonResponse({'message': 'not maching  new and confirm passwords'})

        
        
        if(new_password==old_password):
            return JsonResponse({'status': 'error', 'message': 'New Password must be  diffrent'}) 

        user_id = request.session['user_id']
        user_info_record = UserInfo.objects.filter(id=user_id).first()
        if user_info_record:
            if(old_password!=user_info_record.password):
                print("old pasworrrdddddddddd",user_info_record.password)
                return JsonResponse({'status': 'error', 'message': 'please enter Correct old Password'})
                
            user_info_record.password = new_password
            user_info_record.save()
            return JsonResponse({'status': 'success', 'message': 'Password updated successfully'})
        else:
            return JsonResponse({'message': 'Password not changed database error'})
        

        return JsonResponse({'message': 'Password changed successfully'})

    return JsonResponse({'message': 'Invalid request'}, status=400)



    
def email_forget_password(email):
    
        subject = 'Forget Password'
        code = generate_8_digit_code()

        message = 'Your 8 digit verfication code is: '+code
        
        recipient_list = [email]

        send_mail(
            'Forget Password', #title
            message, #message
            'help@proadvisor.ai',
            recipient_list,
            fail_silently=False
        )

        try:
            # Try to get the first UserInfo record with the same email
            user_info = UserInfo.objects.filter(email=email).first()
            
            if user_info:
                # Delete any existing ForgetPassword record for this UserInfo
                ForgetPassword.objects.filter(email=user_info).delete()

                # Create and save a new ForgetPassword record
                new_record = ForgetPassword(email=user_info, code=code)
                new_record.save()
            else:
                # Handle the case when no UserInfo with the given email exists
                pass
        except Exception as e:
            # Handle exceptions, e.g., database errors
            print(f"Error: {str(e)}")

openai.api_key = ""
# openai.api_key = ""

# Set up the model and prompt
model_engine = "text-davinci-003"

# middleware to check the user is in session or not


def check_user_login(view_func):
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if user_id is not None:
            user = UserInfo.objects.get(pk=user_id)
            return view_func(request, *args, **kwargs)
        else:
            return redirect('/signin')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def signup(request):
    if request.method == "GET":
        return render(request, "signup.html")

    elif request.method == "POST":
        data = json.loads(request.body)

        firstname = data.get('firstname')
        lastname = data.get('lastname')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        print("this is username: ", firstname)
        print("this is last name: ", lastname)
        print("this is email: ", email)
        print("this is password: ", password)
        print("this is confirm password: ", confirm_password)

        if (password != confirm_password):
            return JsonResponse({'error': 'Password and Confirm Password are not matched!'}, status=402)

        if UserInfo.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email is already in use'}, status=406)

        data = UserInfo.objects.create(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password=password,
            
        )

        if data.pk:
            success_message = "Submitted"
            request.session['active_user_id'] = data.id
            return JsonResponse({'status': 'success', 'message': 'User authenticated successfully'})

        else:
            error_message = "Form submission failed. Please check the input fields and try again."
            return JsonResponse({'error': 'Password and Confirm Password are not matched!'}, status=401)


def signin(request):
    if request.method == "GET":
        return render(request, "signin.html")

    elif request.method == "POST":
        data = json.loads(request.body)
        useremail = data.get('email')
        userpassword = data.get('password')

        user = UserInfo.check_email(useremail)
        if user:
            if user.password == userpassword:  # You should hash or encrypt the password in practice
                request.session['user_id'] = user.id
                request.session['user_name'] = user.firstname
                return JsonResponse({'status': 'success', 'message': 'User authenticated successfully'})

            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)


def forget_password(request):
    if request.method == "GET":
        return render(request, "forget.html")

    if request.method == "POST":

        useremail = request.POST.get('email')

        email_forget_password(useremail)

        return render(request, 'verification.html', {'email': useremail})




def change_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        code = request.POST.get('code')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        # Verify if the email and code exist in the ForgetPassword model
        try:
            forget_password_record = ForgetPassword.objects.get(email__email=email, code=code)
        except ObjectDoesNotExist:

            return redirect("/signin", JsonResponse({'error': 'Invalid email or code.'}, status=400))

        # Check if the password matches the confirm password
        if password != confirm_password:
            return redirect("/signin", JsonResponse({'error': 'Passwords do not match.'}, status=400))

        # Update the password in the first UserInfo model found with the same email
        try:
            user_info_record = UserInfo.objects.filter(email=email).first()
            if user_info_record:
                user_info_record.password = password
                user_info_record.save()
            else:
                return redirect("/signin", JsonResponse({'error': 'User not found.'}, status=400))

            # Delete the ForgetPassword record
            forget_password_record.delete()
            return redirect("/signin")
        except ObjectDoesNotExist:
            return redirect("/signin", JsonResponse({'error': 'Error updating the password.'}, status=400))

    return redirect("/signin", JsonResponse({'error': 'Method not allowed.'}, status=400))



# def signin(request):
#     if request.method == "GET":
#         return render(request, "signin.html")

#     elif request.method == "POST":
#         # useremail = request.POST.get('email')
#         # userpassword = request.POST.get('password')

#         # Retrieve the JSON data from the frontend
#         data = json.loads(request.body)
#         useremail = data.get('email')
#         userpassword = data.get('password')

#         user = UserInfo.check_email(useremail)
#         if user:
#             if (user.password==userpassword):
#                 request.session['user_id'] = user.id
#                 request.session['user_name'] = user.firstname
#                 return JsonResponse({'status': 'success', 'message': 'User authenticated successfully'})
#             else:
#                 return JsonResponse({'status': 'error', 'message': 'Password does not match'})
#         else:
#             return JsonResponse({'status': 'error', 'message': 'User email does not exist'})
#     else:
#         return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@check_user_login
def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    return redirect('/signin')


def generate_unique_panel_id():
    panel_id_length = 8
    characters = string.ascii_uppercase + string.digits
    while True:
        panel_id = ''.join(random.choices(characters, k=panel_id_length))
        # Check if the generated panel_id is unique in the database
        if not Panel.objects.filter(panel_id=panel_id).exists():
            return panel_id


@check_user_login
def show_home(request):
    specific_user_id = request.session.get('user_id')
    
    # Get the ID of the "Custom" category
    cat_id_queryset = AccountantCategories.objects.filter(category='Custom')
    if cat_id_queryset.exists():
        cat_id = cat_id_queryset.first().id
    else:
        cat_id = None
    
    # Get the "Panel" category
    excluded_category_queryset = AccountantCategories.objects.filter(category='Panel')
    if excluded_category_queryset.exists():
        excluded_category = excluded_category_queryset.get()
    else:
        excluded_category = None
    
    print("Excluded Category ID:", excluded_category.id if excluded_category else None)
    
    search_accountant_info = AccountantInfo.objects.filter(
    ~Q(category_id__id=cat_id) | (Q(category_id__id=cat_id) & Q(user_id__id=specific_user_id)),
    ~Q(category_id__category='Panel')  # Exclude the 'Panel' category
).order_by('header_text')
    
    # Exclude all AccountantInfo objects where the category is 'Panel'
    search_try_saying_accountant_info = AccountantInfo.objects.exclude(category_id=excluded_category.id) if excluded_category else AccountantInfo.objects.all()
    search_try_saying_accountant_info = search_try_saying_accountant_info.filter(
        ~Q(category_id__id=cat_id) | (Q(category_id__id=cat_id) & Q(user_id__id=specific_user_id)),
    ).order_by('-rating')

    print("Search Accountant Info:", search_accountant_info)
    print("Search Try Saying Accountant Info:", search_try_saying_accountant_info)
    
    search_categories = AccountantCategories.objects.exclude(category='Panel').order_by('category')

    print("Search Categories:", search_categories)

    uid = current_user(request)
    user_id = UserInfo.objects.get(id=request.session.get('user_id'))
    
    return render(request, 'home.html', {'user': user_id,
                                          'data': search_accountant_info,
                                          'categories': search_categories,
                                          'current_user': uid,
                                          'try_saying_data': search_try_saying_accountant_info})

@check_user_login
def get_info(request):
    specific_user_id = request.session.get('user_id')
    id = request.GET.get('id')  # Get the ID from the query parameters
    search_accountant_info = AccountantInfo.objects.filter(
        (Q(category_id__id=id) & Q(user_id__isnull=True)) | (Q(category_id=id) & Q(user_id__id=specific_user_id))).order_by('header_text')
    
    search_try_saying_accountant_info = AccountantInfo.objects.all().order_by('-rating')
    search_categories = AccountantCategories.objects.all().order_by('category')
    uid = current_user(request)
    return render(request, 'home.html', {'data': search_accountant_info, 'categories': search_categories, 'current_user': uid, 'try_saying_data': search_try_saying_accountant_info})


@check_user_login
def current_user(request):
    return request.session.get('current_user_id')


@check_user_login
@csrf_exempt
def get_Card_ID(request):

    account_id = request.POST.get('id', '')
    print("id is coming here: ", account_id)
    request.session['account_id'] = account_id
    return HttpResponse(show_chat_screen(request))


@check_user_login
@csrf_exempt
def get_selected_category(request):
    category_id = request.GET.get('category_btn_id')
    if category_id:
        search_accountant_info = AccountantInfo.objects.filter(
            category_id=category_id)
        new_search_list = []
        for rec in search_accountant_info:
            rec_dict = {
                'id': rec.id,
                'header_text': rec.header_text,
                'tagline_text': rec.tagline_text,
                'description': rec.description,
                'context': rec.context,
                'category_id': rec.category_id.id,
                'accountant_image': str(rec.accountant_image),
                'category_color': rec.category_id.color,
            }
            new_search_list.append(rec_dict)
        if new_search_list:
            my_js_list = json.dumps(new_search_list)
            return JsonResponse(my_js_list, safe=False)


def interact_with_chatgpt(context, username):
    # Combine system and user messages in the prompt
    prompt = f"System: {context}. give me some greeting message and list of 2-3 point in which ways you can help me. the user name is {username} and use your title as your name. IMPORTANT to give reply in maxmimum 60-70 words. DO not add best regards or something like this in message."

    message_list = []
    message_list.append({"role": "system", "content": prompt})

    completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message_list
        )
    chatgpt_response = completion.choices[0].message['content']


    # Retrieve the generated text from the response
    # chatgpt_response = response['choices'][0]['text'].strip()

    print(chatgpt_response)
    print("---------- this is reponse coming from chatgpt----------")


    return chatgpt_response



def greeting_line(context, username):
    # Combine system and user messages in the prompt
    prompt = f"System: {context}. Write me single line message of one line so user can start conversation.  Example 'Let me know about your thoughts so we can start to resolve your problem'"

    message_list = []
    message_list.append({"role": "system", "content": prompt})

    completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message_list
        )
    chatgpt_response = completion.choices[0].message['content']


    # Retrieve the generated text from the response
    # chatgpt_response = response['choices'][0]['text'].strip()

    print(chatgpt_response)
    print("---------- this is reponse coming from chatgpt----------")


    return chatgpt_response

def interact_with_chatgpt_panel(context, username):
    # Combine system and user messages in the prompt
    prompt = f"System: {context}. give me some greeting message. the user name is {username} and use your title as your name. IMPORTANT to give reply in maxmimum 60-70 words. DO not add best regards, Regards or extra words Like: 'Summary:', 'Advisor:' in message. Don't add '. Must ask question from user regarding to start further conversation."

    message_list = []
    message_list.append({"role": "system", "content": prompt})

    completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message_list
        )
    chatgpt_response = completion.choices[0].message['content']


    # Retrieve the generated text from the response
    # chatgpt_response = response['choices'][0]['text'].strip()

    print(chatgpt_response)
    print("---------- this is reponse coming from chatgpt----------")


    return chatgpt_response

@check_user_login
def show_chat_screen(request, advisor_id):
    # Retrieve active user information
    active_user = current_user(request)
    account_id = request.session.get('account_id')
    active_user_id = request.session.get('user_id')
    user_id = UserInfo.objects.get(id=active_user_id)
    get_username = UserInfo.objects.filter(id=active_user_id).first()

    # Retrieve advisor information
    active_advisor = get_object_or_404(AccountantInfo, id=advisor_id)
    request.session['active_advisor'] = active_advisor.id
    get_active_advisor_img = active_advisor.accountant_image.url

    # Retrieve or create chat log
    try:
        search_chat_log = ChatLogs.objects.get(advisor_id=active_advisor, user_id=user_id)
        search_message_log = MessageLogs.objects.filter(chat_id=search_chat_log)
        request.session['active_chat_id'] = search_chat_log.id
    except ChatLogs.DoesNotExist:
        chat_log = ChatLogs(advisor_id=active_advisor, user_id=user_id)
        chat_log.save()
        search_chat_log = chat_log
        search_message_log = MessageLogs.objects.filter(chat_id=chat_log)
        request.session['active_chat_id'] = chat_log.id

        # Interact with ChatGPT to generate a helpful prompt
        active_user_name = get_username.firstname
        chatgpt_response = interact_with_chatgpt(active_advisor.context, active_user_name)

        message_log = MessageLogs(chat_id=search_chat_log, role='assistant', content=chatgpt_response, message_type='a')
        message_log.save()

        start_conversation_line = greeting_line(active_advisor.context, active_user_name)
        message_log = MessageLogs(chat_id=search_chat_log, role='assistant', content=start_conversation_line, message_type='a')

        message_log.save()

    # Check if there are no existing messages and generate a ChatGPT response
    if not search_message_log.exists():
        active_user_name = get_username.firstname
        chatgpt_response = interact_with_chatgpt(active_advisor.context, active_user_name)
        message_log = MessageLogs(chat_id=search_chat_log, role='assistant', content=chatgpt_response, message_type='a')
        message_log.save()

        start_conversation_line = greeting_line(active_advisor.context, active_user_name)
        message_log = MessageLogs(chat_id=search_chat_log, role='assistant', content=start_conversation_line, message_type='a')

        message_log.save()

    # Retrieve other necessary data
    search_accountant_info = [active_advisor]
    search_disclaimer_info = DisclaimerInfo.objects.all()

    return render(request, 'chat_layout.html', {
        'data': search_accountant_info,
        'disclaimer_data': search_disclaimer_info.first() if search_disclaimer_info else "disclaimer",
        'message_log': search_message_log,
        'current_username_char': get_username.firstname[0],
        'get_active_advisor_img': get_active_advisor_img
    })

@check_user_login
def get_openai_response(request):
    active_chat_id = request.session.get('active_chat_id')
    active_advisor = request.session.get('active_advisor')
    card_id = request.GET.get('card_id')
    card_context = request.GET.get('card_context')
    message = request.GET.get('msg')
    search_accountant_info = AccountantInfo.objects.filter(id=active_advisor)
    chat_id = ChatLogs.objects.get(id=active_chat_id)

    search_message_log = MessageLogs.objects.filter(chat_id=chat_id).order_by('-id')[:5][::-1]

    advisor_context = ''
    if search_accountant_info:
        for rec in search_accountant_info:
            advisor_context = rec.context

    system_message = "CONTEXT: You are a top-tier [ "+advisor_context + \
        " ]. You possess extensive experience and have successfully helped a diverse range of clients with various needs within your field of expertise. Compulsory to try to give answers in precise form like words 30-40. Compulsory add some questions in last of your message related to your response to increase interaction with user. Don't use word like best regards or greetings like this in last of message."

    message_list = []

    # Always append the system message to set the context
    message_list.append({"role": "system", "content": system_message})

    # Append the previous chat messages to the conversation
    for msg in search_message_log:
        message_list.append({"role": msg.role, "content": msg.content})

    if card_context:
        prompt = card_context
    elif message:
        prompt = message
        # Append the latest user message to the conversation
        message_list.append({"role": "user", "content": message})
    else:
        prompt = ""

    if message_list:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=message_list
        )
        response = completion.choices[0].message['content']

        # Check for non-visible characters in the response
        print("Checking for non-visible characters in the response...")
        import re
        pattern = re.compile(r'\s')
        non_visible_chars_pattern = r'[\x00-\x1F\x7F-\x9F]'
        non_visible_chars = re.findall(non_visible_chars_pattern, response)

        # Print the non-visible characters found
        for char in non_visible_chars:
            print(f"Non-visible character found: {char.encode('unicode_escape')}")

    else:
        response = ""

    if prompt and response and chat_id:
        # Save the message to the MessageLogs model
        MessageLogs(chat_id=chat_id, role="user",
                    content=prompt, message_type="u").save()
        MessageLogs(chat_id=chat_id, role="assistant",
                    content=response, message_type="a").save()
        
    website_links_data,titles, icons = get_website_links(response)

    data_to_frontend = {
        'response': response,
        'website_links': website_links_data,
        'titles': titles,
        'icons': icons,
        # Add other data as needed
    }

    # Return a JSON response containing the data
    return JsonResponse(data_to_frontend)
    # return HttpResponse(response)


# code to create resourse link from chatgpt start
def get_website_links(text):
    # Enhanced context message for better guidance
    system_message = "Generate a list of 3 website links with titles related to this topic: '{}'. Format each entry as 'Title: [Title of the Article] - URL: [URL]'. Ensure the titles and URLs are accurate and relevant to the topic.".format(text)
    message_list = [{"role": "system", "content": system_message}]


    try:
        # Call to OpenAI API
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=message_list
        )

        # Parsing the response
        response = completion.choices[0].message['content']
        print("==== Response is here: ", response)

        # Extract and return website links and titles
        links, titles = extract_website_info(response)
        icons=fetch_favicons(links)
        print("Links are here: ", links)
        print("Titles are here: ", titles)
        print("\n\nicons are here: ", icons)
        return links, titles, icons

    except Exception as e:
        print("An error occurred: ", e)
        return [], []
def extract_website_info(response):
    # Split the response into lines
    lines = response.split('\n')

    links = []
    titles = []

    for line in lines:
        # Identify and split the title and URL parts
        if 'Title:' in line and 'URL:' in line:
            title_part, url_part = line.split('URL:')
            title = title_part.replace('Title:', '').strip().lstrip('0123456789). ').replace('"', '')
            url = url_part.strip()

            titles.append(title)
            links.append(url)

    return links, titles


def convert_to_base_urls(urls):
    base_urls = []
    for url in urls:
        parsed_url = urlparse(url)
        base_url = parsed_url.scheme + '://' + parsed_url.netloc
        base_urls.append(base_url)
    
    return base_urls

def is_valid_url(url):
    """
    Check if the URL is valid and well-formed.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def fetch_favicons(website_urls):
    website_urls=convert_to_base_urls(website_urls)
    favicons = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    session = requests.Session()

    for url in website_urls:
        if not is_valid_url(url):
            favicons.append('error')
            continue

        try:
            response = session.get(url, headers=headers, timeout=10, verify=True)  # SSL verification
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            icon_link = soup.find("link", rel=lambda v: v and any(rel in v for rel in ["icon", "shortcut icon", "apple-touch-icon", "shortcut", "bookmark"]))

            if icon_link and icon_link.get('href'):
                favicon_url = urljoin(url, icon_link['href'])
                favicons.append(favicon_url)
            else:
                root_favicon = urljoin(url, '/favicon.ico')
                root_response = session.head(root_favicon, headers=headers, timeout=10, verify=True)
                if root_response.status_code == 200:
                    favicons.append(root_favicon)
                else:
                    favicons.append('error')
        except requests.exceptions.RequestException as e:
            favicons.append('error')
        except Exception as e:
            favicons.append('error')

    return favicons

@check_user_login
def about(request):
    # user_id = request.session.get('user_id')
    return render(request, "about.html")


# Professional Panel Code
@check_user_login
def prof_panel(request):
    advisors = AccountantInfo.objects.all()
    return render(request, "create_prof_panel.html", {'advisors': advisors})


@check_user_login
def update_custom_advisor(request):
    if request.method == 'POST':
        # Retrieve form data, including user ID
        header_text = request.POST.get('advisor_name')
        advisor_id = request.POST.get('ad_id')
        image = request.FILES.get('image')

        advisor = get_object_or_404(AccountantInfo, id=advisor_id)

        # Handle default values
        if image:
            file_name = image.name
            save_path = os.path.join('media', 'occupational_images', file_name)

            with open(save_path, 'wb') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            advisor.accountant_image = os.path.join('occupational_images', file_name)

        # Create context using your prompt generation function
        # context = get_prompt_for_custom_advisor(header_text, tagline_text, description)

        # Update the advisor object
        advisor.header_text = header_text
        # advisor.tagline_text = tagline_text
        # advisor.description = description
        # Update other fields as needed

        # Save the changes to the database
        advisor.save()

    id=AccountantCategories.objects.filter(category='Custom').first().id
    advisors = AccountantInfo.objects.all()
    specific_user_id = request.session.get('user_id')

    advisors = AccountantInfo.objects.filter(
        (Q(category_id__id=id) & Q(user_id__isnull=True)) | (Q(category_id=id) & Q(user_id__id=specific_user_id))).order_by('header_text')
    return render(request, "create_custom_advisor.html", {'data': advisors})


@check_user_login
def delete_custom_advisor(request):
    # Get the advisor object to delete
    advisorc = AccountantInfo.objects.get(id=request.POST.get('additional_id'))

    # Delete the advisor
    advisorc.delete()
    
    return redirect('/create-custom-advisor')



@check_user_login
def custom_advisor(request):
    id=AccountantCategories.objects.filter(category='Custom').first().id
    advisors = AccountantInfo.objects.all()
    specific_user_id = request.session.get('user_id')

    custom_advisors = AccountantInfo.objects.filter(
        (Q(category_id__id=id) & Q(user_id__isnull=True)) | (Q(category_id=id) & Q(user_id__id=specific_user_id))).order_by('header_text')
    
    advisors = AccountantInfo.objects.all()

    return render(request, "create_custom_advisor.html", {'data': custom_advisors,'advisors':advisors})


@check_user_login
def custom_advisor_submit(request):

    if request.method == 'POST':
        # Retrieve form data, including user ID
        header_text = request.POST.get('advisor_name')
        image = request.FILES.get('image')
        user_id = request.session.get('user_id')

        image = request.FILES.get('image')
        selected_ids = request.POST.getlist('advisors_id')

        # Retrieve header_text and description for the selected advisors
        selected_advisors = AccountantInfo.objects.filter(id__in=selected_ids)
        selected_header_texts = [AccountantInfo.header_text for AccountantInfo in selected_advisors]
        tagline_text = [AccountantInfo.tagline_text for AccountantInfo in selected_advisors]

        print("hhhhhhhhhhhhhhhhhhhheadhfadsffffffffff",selected_header_texts)

    #     # Validate the form data
    #     if not all([header_text, tagline_text, description]):
    #         # Handle validation error, for example, return an error response
    #         return render(request, "create_custom_advisor.html", {'data': advisors})
    #     # Handle default values
        if not image:
            accountant_image = 'occupational_images/default.png'
        else:
            file_name = image.name
            save_path = os.path.join('media', 'occupational_images', file_name)

            with open(save_path, 'wb') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            accountant_image = os.path.join('occupational_images', file_name)


    #     id=AccountantCategories.objects.filter(category='Custom').first().id
    #     advisors = AccountantInfo.objects.all()
    #     specific_user_id = request.session.get('user_id')

    #     advisors = AccountantInfo.objects.filter(
    #         (Q(category_id__id=id) & Q(user_id__isnull=True)) | (Q(category_id=id) & Q(user_id__id=specific_user_id))).order_by('header_text') 
        
    #     # Validate and handle category data
        category_data = AccountantCategories.objects.filter(category='Custom').first()

    #     # Ensure proper data types
    #     try:
        rating = int(request.POST.get('rating', 1))
    #     except ValueError:
    #         # Handle error if rating is not a valid integer
    #         return render(request, "create_custom_advisor.html", {'data': advisors})
        
        user_info_instance = UserInfo.objects.get(id=user_id)

    #     # Ensure the UserInfo instance is valid
    #     if not user_info_instance:
    #         return render(request, "create_custom_advisor.html", {'data': advisors})

    #     # Create context using your prompt generation function
        context = get_prompt_for_custom_advisor(selected_header_texts, tagline_text)

        # Create and save the AccountantInfo object
        accountant_info = AccountantInfo(
            header_text=header_text,
            tagline_text=' '.join(tagline_text),
            description='description',
            context=context,
            question='',
            category_id=category_data,
            accountant_image=accountant_image,
            rating=rating,
            user_id=user_info_instance  # Assuming user_id is a valid foreign key
        )

        accountant_info.save()


        
    id=AccountantCategories.objects.filter(category='Custom').first().id
    advisors = AccountantInfo.objects.all()
    specific_user_id = request.session.get('user_id')

    custom_advisors = AccountantInfo.objects.filter(
        (Q(category_id__id=id) & Q(user_id__isnull=True)) | (Q(category_id=id) & Q(user_id__id=specific_user_id))).order_by('header_text')
    
    advisors = AccountantInfo.objects.all()

    return redirect('/create-custom-advisor')


    
def get_prompt_for_custom_advisor(names,mottos):
    prompt = f"CONTEXT: You are a top-tier one multi-talented advisor professional in these fileds[ {names} ]. You bring your expertise to address various challenges in these fields, providing tailored solutions for your clients. Interact as one advisor who have knwoledge of following area [{names}]"
    return prompt



@check_user_login
def prof_simple_panel_submit(request):
    # if request.method == 'GET':
    #     advisors_ids = request.GET.getlist('advisors_id')
    #     print("---------------------------- ids here: ", advisors_ids)

    if request.method == 'POST':
        advisors = AccountantInfo.objects.all()

        panel_name = request.POST.get('panel_name')
        panel_topic = request.POST.get('panel_topic')
        advisors_ids = request.POST.getlist('advisors_id')

        print("---------------------------- ids here: ", advisors_ids)
        print("---------------------------- name here: ", panel_name)
        print("---------------------------- topic here: ", panel_topic)
        json_str = advisors_ids[0]
        ids_list = json.loads(json_str)

        # parsed_ids = []

        parsed_ids = [int(id_str) for id_str in ids_list]

        for id in parsed_ids:
            print("--------[panel id]", id)

        user_id = request.session.get('user_id')

        error_messages = []
        if not panel_name:
            error_messages.append("Panel Name field cannot be empty.")
        if not panel_topic:
            error_messages.append("Panel Topic field cannot be empty.")
        if not advisors_ids:
            error_messages.append("Select at least one advisor.")
        if error_messages:
            return redirect('/create-professional-panel', {"advisor": advisors, "error_messages": error_messages})

        accountants = AccountantInfo.objects.filter(id__in=parsed_ids)
        if not accountants.exists():
            return redirect('/create-professional-panel', {"advisor": advisors, "error_messages": error_messages})

        panel_id = generate_unique_panel_id()
        print("yahhhhhhhhhhaaaaa")
        print("user id is here", user_id)
        # for accountant in accountants:

        panel = Panel.objects.create(
            user_id=user_id,
            panel_name=panel_name,
            panel_id=panel_id,
            panel_topic=panel_topic,
        )

        userid = UserInfo.objects.get(id=user_id)
        panel.accountant_info.add(*accountants)
        panel_chat = PanelChatLogs.objects.create(
                        panel_id=panel, user_id=userid)
        
        user_name = request.session.get('user_name')
        for accountant in accountants:
            response=interact_with_chatgpt_panel(accountant.context,user_name)

            panel_message_log = PanelMessageLogs.objects.create(
            response_message=response,
            prompt_message='',
            panel_chat_id=panel_chat,
            advisor_id=accountant
        )
            
        panel_message_log.save()
        return redirect(f'/chat-open/{panel_id}/')
# return redirect('/chats')

    else:
        return render(request, "create_prof_panel.html", {'advisors': advisors})
    

    
@check_user_login
def chats(request):
    user_id = request.session.get('user_id')
    user_name = request.session.get('user_name')

    # Retrieve and order panels by 'id' in descending order
    panels = Panel.objects.filter(user_id=user_id).order_by('-id')

    # Retrieve and order advisor chats by 'id' in descending order
    search_advisor_chat = ChatLogs.objects.filter(user_id=user_id).order_by('-id')

    return render(request, "chat.html", {"search_panel": panels, "username": user_name, "advisor_chats": search_advisor_chat})


# ---------------------------------
#        panel chat open
# ---------------------------------

@check_user_login
def chat_open(request, panel_id):
    specific_user_id = request.session.get('user_id')

    cat_id_queryset = AccountantCategories.objects.filter(category='Custom')
    cat_id = cat_id_queryset.first().id if cat_id_queryset.exists() else None

    try:
        excluded_category = AccountantCategories.objects.get(category='Panel')
    except AccountantCategories.DoesNotExist:
        raise Http404("Panel category does not exist.")

    print("Excluded Category ID:", excluded_category.id)

    search_accountant_info = AccountantInfo.objects.filter(
        ~Q(category_id__id=cat_id) | (Q(category_id__id=cat_id) & Q(user_id__id=specific_user_id)),
        ~Q(category_id=excluded_category.id)
    ).order_by('header_text')

    user_name = request.session.get('user_name')
    active_user_id = request.session.get('user_id')

    try:
        active_panel = Panel.objects.get(panel_id=panel_id)
    except Panel.DoesNotExist:
        raise Http404("Panel does not exist.")

    active_panel_id = active_panel.id

    request.session['active_panel_id'] = panel_id
    search_panel = Panel.objects.filter(panel_id=panel_id)

    search_disclaimer_info = DisclaimerInfo.objects.all()

    try:
        search_panel_chat_log = PanelChatLogs.objects.get(
            panel_id=active_panel_id, user_id=active_user_id)
        search_panel_message_log = PanelMessageLogs.objects.filter(
            panel_chat_id=search_panel_chat_log).order_by('created_at')
        request.session['active_panel_chat_id'] = search_panel_chat_log.id
    except PanelChatLogs.DoesNotExist:
        PanelChatLogs(panel_id=active_panel_id, user_id=active_user_id).save()
        search_panel_chat_log = PanelChatLogs.objects.get(
            panel_id=active_panel_id, user_id=active_user_id)
        search_panel_message_log = PanelMessageLogs.objects.filter(
            panel_chat_id=search_panel_chat_log)
        request.session['active_panel_chat_id'] = search_panel_chat_log.id


    # Step 1: Group messages by 'created_at'
    grouped_messages = defaultdict(list)
    for message in search_panel_message_log:
        grouped_messages[message.created_at].append(message)

    # Step 2: Create a list of tuples
    organized_data = []
    for created_at, messages in grouped_messages.items():
        if messages:
            first_prompt = messages[0].prompt_message
            all_responses=[]
            for msg in messages:
                response_data = {
                    'response': msg.response_message,
                    'advisor_header_text': msg.advisor_id.header_text,
                    'accountant_image': msg.advisor_id.accountant_image.url,
                }
                all_responses.append(response_data)

            organized_data.append((first_prompt, all_responses))


    print("\n\n\n\organized_data Messge Logs Panel Caht",organized_data)

    return render(request, "group_chat_inbox.html", {"search_panel": search_panel,
                                                     'disclaimer_data': search_disclaimer_info.first() or "disclaimer",
                                                     'panel_message_log': organized_data,
                                                     "current_username_char": user_name[0],
                                                     'advisors': search_accountant_info})

@check_user_login
def get_openai_response_group(request):
    active_panel_chat_id = request.session.get('active_panel_chat_id')
    active_panel_id = request.session.get('active_panel_id')
    card_id = request.GET.get('card_id')
    card_context = request.GET.get('card_context')
    message = request.GET.get('msg')

    panel = get_object_or_404(Panel, panel_id=active_panel_id)
    panel_chat = get_object_or_404(PanelChatLogs, id=active_panel_chat_id)

    # print("this is panel chat id",active_panel_chat_id)
    # print("this is panel id",active_panel_id)
    # print(panel_chat)

    # search_message_logs = PanelMessageLogs.objects.filter(panel_chat_id=panel_chat)

    response_list = []

    # Fetch all advisors associated with the panel
    advisors = panel.accountant_info.all()
    
    advisors = sorted(advisors, key=lambda x: x.category_id.category == 'Panel', reverse=False)

    # print("this is advisors data: ", advisors)
    time_stamp=timezone.now()

    for advisor in advisors:
        # Construct the conversation context for the advisor
        # conversation = []

        response = generate_response(advisor.id, active_panel_chat_id, message)

        # Save the response to the database
        # message = PanelMessageLogs(response_message=response, prompt_message=message, panel_chat_id=panel_chat, advisor_id=advisor)
        # message.save()
        panel_message_log = PanelMessageLogs.objects.create(
            response_message=response,
            prompt_message=message,
            panel_chat_id=panel_chat,
            advisor_id=advisor,
            created_at=time_stamp
        )
        panel_message_log.save()

        response_data = {
            'response_message': response,
            'accountant_image': advisor.accountant_image.url,
            'advisor_header_text': advisor.header_text
        }
        response_list.append(response_data)

    return JsonResponse({'response_message_data': response_list})


def generate_response(advisor_id, active_panel_chat_id, msg):
    active_advisor = advisor_id
    message = msg
    search_accountant_info = AccountantInfo.objects.filter(id=active_advisor)
    search_message_log = PanelMessageLogs.objects.filter(
        advisor_id=active_advisor, panel_chat_id=active_panel_chat_id)

    advisor_context = ''
    if search_accountant_info:
        for rec in search_accountant_info:
            advisor_context = rec.context

    system_message = "CONTEXT: You are a top-tier [ "+advisor_context + \
        " ]. You possess extensive experience and have successfully helped a diverse range of clients with various needs within your field of expertise. Try to give answers in precise form like words 30-40."

    message_list = []

    # Always append the system message with HTML formatting
    system_message_html = f"{system_message} Read old chat with user and also the new message by the user carefully, and answer according to it. Use \n\t ** escape dictonary in response"
    message_list.append({"role": "system", "content": system_message_html})

    # Append the previous chat messages to the conversation
    for log in search_message_log:
        message_list.append({"role": "user", "content": log.prompt_message})
        message_list.append(
            {"role": "assistant", "content": log.response_message})

    if message:
        # Append the latest user message to the conversation
        message_list.append({"role": "user", "content": message})

    if message_list:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message_list
        )
        response = completion.choices[0].message.content
    else:
        response = ""

    return response




@check_user_login
def group_chat(request):
    list_accountants = []
    # Replace AccountantInfo with your actual model name
    accountants = AccountantInfo.objects.all()
    if request.method == 'POST':
        message = request.POST.get('message', '')
        panel_id = request.POST.get('panel_id', '')
        panel = Panel.objects.filter(panel_id=panel_id)

        for panel in panel:
            accountant_info = panel.accountant_info

            list_accountants.append(accountant_info)

        # responses = get_openai_response_group(list_accountants, message)
        responses = "Testing responses for group chats..."

        return JsonResponse({"responses": responses})
    else:
        return render(request, "group_chat.html", {"accountants": accountants})


@check_user_login
def load_home_search(request):
    experties = Experties.objects.all()
    return render(request, 'home-search.html', {'experties': experties})


@check_user_login
@csrf_exempt
def ask_question(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('userInput')
        categories_list = data.get('categoriesList')

        print("----------------- hey there is list: ", categories_list)
        print("here is the output: ", question)

        advisors = AccountantInfo.objects.all()  # Start with all advisors

        if categories_list:
            # Filter advisors based on category IDs if categories_list is not empty
            advisors = advisors.filter(category_id__in=categories_list)

        print("------- hello im here", advisors)

        advisors_list = [(advisor.header_text, advisor.id)
                         for advisor in advisors]
        # print(advisors_list)
        # print("ad list is here-----------------", advisors_list)

        # Prepare the message list for the OpenAI API
        message_list = [
            {
                "role": "system",
                "content": (
                    "List of Advisors:\n"
                )
            }
        ]

        # Add the list of advisors to the message
        for i, (advisor_name, id) in enumerate(advisors_list, start=1):
            message_list.append(
                {"role": "system", "content": f" {advisor_name}, {id}"})

        message_list.append(
            {
                "role": "system",
                "content": (
                    "Please provide the 9 advisors ids from the provided list who are most suitable to answer the user's question."
                    "It is very important to use their crossponding ids exactly as they appear in the list. (e.g: [1111,2222,3333]) Do not include any additional words just return a python list ids. The advisor names should be selected from the provided list of advisors. Ignore greetings from user."
                )
            }
        )

        try:
            # Send the user's question and advisor names to the OpenAI API
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=message_list + [{"role": "user", "content": question}]
            )

            # Get the response from the API
            response = completion.choices[0].message.content
            print("ddddddddddddddddddddddddddmmmmmmmmmmmmmmm")
            print(response)

            user_provided_advisors = json.loads(response)
        except:
            # user_provided_advisors = json.loads('{}')
            user_provided_advisors = json.loads('{"user_advisors": null}')


        print(user_provided_advisors)

    return JsonResponse({'advisors_ids': user_provided_advisors})


@check_user_login
@csrf_exempt
def ask_advisor(request):
    # message_list.clear()

    print('im working ----------------------------')
    data = json.loads(request.body)
    id = data.get('id')
    question = data.get('question')

    # Initialize a list to store recommended advisors' information
    recommended_advisors_info = []

    # for advisor_name, custom_name in zip(user_provided_advisors, custom_advisor_name):

    try:
        # Get the advisor object
        advisor = AccountantInfo.objects.get(id=id)
        # if advisor not in answered_advisor:
        #     answered_advisor.append(advisor.header_text)
        # if not advisor and custom_name not in answered_advisor:
        #     advisor = AccountantInfo.objects.get(header_text=custom_name)

        # Get the prompt message for the advisor
        prompt_message = advisor.context

        # Prepare the message list for the OpenAI API with the updated prompt
        advisor_prompt = (
            f"Please provide a concise summary max 20 words of the most relevant information regarding '{question}'. Don't add extra words Like: 'Summary:', 'Advisor:'."
            f"based on your expertise as {advisor.header_text}."
        )
        message_list = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "user", "content": advisor_prompt},
            {"role": "system", "content": prompt_message}
        ]

        # Send the messages to the OpenAI API
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message_list
        )

        # Get the response from the API (limit to 20 words)
        response = " ".join(completion.choices[0].message.content.split())

        # to generate message have to stored in database

        # Parsing the response
        main_response = "sample text can be used in future"
        

        print("this is main resonse comingf from got: ", main_response)

        # Extract the advisor's image
        advisor_image = advisor.accountant_image.url
        tag_line = advisor.tagline_text
        advisor_id = advisor.id
        context = advisor.context

        # Print the advisor's name, image, and response
        print(f"Advisor Name: {advisor.header_text}")
        print(f"Advisor Image: {advisor_image}")
        print(f"Response: {response}")

        # Save the advisor's name, image, and response in a list
        recommended_advisors_info.append({
            "id": advisor_id,
            "name": advisor.header_text,
            "image": advisor_image,
            "response": response,
            "main_response": main_response,
            "tag_line": tag_line,
            "context": context,
            "question": question
        })

    except AccountantInfo.DoesNotExist:
        # print(f"Advisor with name '{advisor_name}' does not exist.")
        pass

    return JsonResponse({'advisors': recommended_advisors_info})


@check_user_login
@csrf_exempt
def start_ai_chat(request):
    if request.method == 'POST':
        try:
            # Retrieve GET parameters

            chosenCardsIds_str = request.POST.get('advisors_id')
            chosenCardData_str = request.POST.get('chosenCardData')
            chosenCardMainData_str = request.POST.get('chosenCardMainData')
            
            chosenCardQuestion_str = request.POST.get('chosenCardQuestion')

            # Parse JSON strings into Python lists
            chosenCardsIds = json.loads(chosenCardsIds_str)
            chosenCardData = json.loads(chosenCardData_str)
            chosenCardMainData = json.loads(chosenCardMainData_str)
            chosenCardQuestion = json.loads(chosenCardQuestion_str)

        
            print("this is chosen cards id: ", chosenCardsIds)
            print("this is chosen cards data: ", chosenCardData)
            print("this is chosen cards questions: ", chosenCardQuestion)

            if len(chosenCardsIds) == 1:

                advisor = AccountantInfo.objects.get(id=chosenCardsIds[0])
                user_name = request.session.get('user_name')

                greetings_prompt = f"{advisor.context}. give me some greeting message and list of 2-3 point in which ways you can help me regarding this question {chosenCardQuestion[0]}. the user name is {user_name} and use your title as your name. IMPORTANT to give reply in maxmimum 60-70 words. DO not add best regards or something like this in message. Don't add extra words Like: 'Summary:', 'Advisor:'. Ask question from user regarding further conversation."
                message_list = [{"role": "system", "content": greetings_prompt}]

                # Call to OpenAI API
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=message_list
                )

                # Parsing the response
                main_response = completion.choices[0].message['content']

                # Print or use the result as needed
                print("this is the text coming from new python code",main_response)
                print("\n\n\n")


                # print("-------------this is print for gerret-----------", hidden_text)

                card_id = chosenCardsIds[0]
                card_data = chosenCardData[0]
                card_main_data = main_response
                card_question = chosenCardQuestion[0]

                print("Card ID: ", card_id)
                print("Card Data: ", card_data)
                print("Card Question: ", card_question)

                # Search for the advisor related to the card_id
                try:
                    advisor = AccountantInfo.objects.get(id=card_id)
                    # Process card_id and card_data as needed
                    print("Card ID in try: ", advisor.id)
                except AccountantInfo.DoesNotExist:
                    return JsonResponse({'error': 'Advisor not found'}, status=400)

                print("all advisors are here: ", advisor)
                # Process card_id and card_data as needed
                print("Card ID: ", card_id)
                print("Card Data: ", card_data)

                # Retrieve user_id from the session (check if it's retrieved correctly)
                user_id = request.session.get('user_id')
                if user_id is None:
                    return JsonResponse({'error': 'User not found in session'}, status=400)

                print("User ID: ", user_id)

                advisor_info = get_object_or_404(AccountantInfo, id=card_id)

                user_info = get_object_or_404(UserInfo, id=user_id)

                # Create or retrieve ChatLogs
                chat_log, created = ChatLogs.objects.get_or_create(
                    advisor_id=advisor_info, user_id=user_info)

                # Create MessageLogs

                MessageLogs(chat_id=chat_log, role="user",
                            content=card_question, message_type="u").save()
                MessageLogs(chat_id=chat_log, role="assistant",
                            content=card_main_data, message_type="a").save()
                # Return a JSON response
                response_data = {
                    'message': 'Data received and saved successfully'}
                # show_chat_screen(request, card_id)

                return redirect(f'/chat/{card_id}')

            elif len(chosenCardsIds) > 1:
                chosenCardsIds_str = request.POST.get('advisors_id')
                chosenCardData_str = request.POST.get('chosenCardData')
                chosenCardMainData_str = request.POST.get('chosenCardMainData')
                chosenCardQuestion_str = request.POST.get('chosenCardQuestion')
                panelName = request.POST.get('panel_name')
                panelTopic = request.POST.get('panel_topic')

                # Parse JSON strings into Python lists
                chosenCardsIds = json.loads(chosenCardsIds_str)
                chosenCardData = json.loads(chosenCardData_str)
                chosenCardQuestion = json.loads(chosenCardQuestion_str)
                chosenCardMainData = json.loads(chosenCardMainData_str)

                print("this is chosen cards id: ", chosenCardsIds)
                print("this is chosen cards data: ", chosenCardMainData)
                print("this is chosen cards questions: ", chosenCardQuestion)
                print("------panel name: ", panelName)
                print("------panel topic: ", panelTopic)

                # Now, you can merge the functionality of the prof_panel_submit function here

                if request.method == 'POST':
                    advisors = AccountantInfo.objects.all()
                    advisors_ids = chosenCardsIds
                    user_id = request.session.get('user_id')

                    # creating panel name from openai
                    panel_name, panel_topic = panel_name_generate(panelName)

                    json_str = json.dumps(advisors_ids)

                    parsed_ids = [int(id_str) for id_str in advisors_ids]

                    error_messages = []
                    if not panelName:
                        error_messages.append("Panel Name field cannot be empty.")
                    if not panelTopic:
                        error_messages.append("Panel Topic field cannot be empty.")
                    if not advisors_ids:
                        error_messages.append("Select at least one advisor.")
                    if error_messages:
                        return redirect('/create-professional-panel', {"advisor": advisors, "error_messages": error_messages})

                    accountants = AccountantInfo.objects.filter(id__in=parsed_ids)
                    if not accountants.exists():
                        return redirect('/create-professional-panel', {"advisor": advisors, "error_messages": error_messages})

                    panel_id = generate_unique_panel_id()
                    print("yahhhhhhhhhhaaaaa")
                    print("user id is here", user_id)


                    for _ in range(3):
                        if not panel_name:
                            panel_name, panel_topic = panel_name_generate(panelName)
                        if panel_name:
                            break

                    panel = Panel.objects.create(
                        user_id=user_id,
                        panel_name=panel_name,
                        panel_id=panel_id,
                        panel_topic=panel_topic,
                    )
                    panel.accountant_info.add(*accountants)

                    user_id = UserInfo.objects.get(id=user_id)

                    print("this is user object printing here:", user_id)

                    panel_chat = PanelChatLogs.objects.create(
                        panel_id=panel, user_id=user_id)

                    # Iterate over the chosen advisor IDs
                    for advisor_id in chosenCardsIds:


                        # creating greeting message with GPT-API start
                        advisor = AccountantInfo.objects.get(id=advisor_id)
                        user_name = request.session.get('user_name')

                        greetings_prompt = f"{advisor.context}. give me some greeting message and list of 2-3 point in which ways you can help me regarding this question {chosenCardQuestion[0]}. the user name is {user_name} and use your title as your name. IMPORTANT to give reply in maxmimum 60-70 words. DO not add best regards, Regards or extra words Like: 'Summary:', 'Advisor:' in message. Don't add '. Must ask question from user regarding to start further conversation."
                        message_list = [{"role": "system", "content": greetings_prompt}]

                        # Call to OpenAI API
                        completion = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo-16k",
                            messages=message_list
                        )

                        # Parsing the response
                        main_response = completion.choices[0].message['content']


                        # Find the corresponding response for the advisor
                        print("this is working ---------------------------")
                        # response = chosenCardMainData[chosenCardsIds.index(advisor_id)]
                        print("this is advisor id by haider: ", advisor_id)
                        accountant = AccountantInfo.objects.get(id=advisor_id)

                        panel_message_log = PanelMessageLogs.objects.create(
                            response_message=main_response,
                            prompt_message=chosenCardQuestion[1],
                            panel_chat_id=panel_chat,
                            advisor_id=accountant
                        )

                        print("this is log messages: ", panel_message_log)

                    return redirect(f'/chat-open/{panel_id}/')

        except Exception as e:
            # Handle exception case
            print("Error:", str(e))
            return JsonResponse({'error': 'Error occurred while processing data'}, status=500)




@csrf_exempt
def profile(request):
    user_id = request.session.get('user_id')

    user_info = UserInfo.objects.get(id=user_id)

    print("this is user info: ",user_info)

    return render(request, "profileSetting.html", {'user_info': user_info})



@check_user_login
def update_profile(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))

            # Retrieve data from the frontend's userData
            first_name = data.get('firstname', '')
            last_name = data.get('lastname', '')
            organization_name = data.get('organization_name', '')
            location = data.get('location', '')
            email = data.get('email', '')
            phone = data.get('phone', '')
            birthdate_str = data.get('birthdate', '')  # Get birthdate as a string

            if birthdate_str:
                try:
                    birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
                except ValueError:
                    # Handle invalid date format
                    # You may want to return an error to the user or handle it in another way
                    pass
            else:
                birthdate = None
            

            # Retrieve the current user's UserInfo instance
            user_id = request.session.get('user_id')

            user_info = UserInfo.objects.get(id=user_id)

            # Update fields based on the received data
            user_info.firstname = first_name
            user_info.lastname = last_name
            user_info.organization_name = organization_name
            user_info.location = location
            user_info.email = email
            user_info.phone = phone
            # user_info.birthdate = birthdate, user_info.birthdate

            # Save the updated user_info
            user_info.save()
            if birthdate:
                user_info.birthdate = birthdate.strftime('%Y-%m-%d')
            else:
                # Assuming user_info.birthdate is a datetime or date object,
                # and you want to convert it to a string using strftime
                if user_info.birthdate:
                    user_info.birthdate = user_info.birthdate.strftime('%Y-%m-%d')
                else:
                    user_info.birthdate = None  # or some default value or a string indicating that the birthdate is not available

            user_info.save()
            print("Profile updated ......sucessfuly")
            return JsonResponse({'status': 'success', 'message': 'Profile updated successfully'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except UserInfo.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User information not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    
@check_user_login
@csrf_exempt
def create_profession_advisor_panel(request):
    
    if request.method == 'POST':
        
        try:
            user_id = request.session.get('user_id')
            # Retrieve the list of card IDs from the request
            advisors_ids_str = request.POST.getlist('advisors_ids') # Retrieve all advisor IDs

            # Check if there is at least one element in the list and it's not an empty string
            if advisors_ids_str and advisors_ids_str[0]:
                # Split the string by commas and convert each part to an integer
                advisors_id = [int(id.strip()) for id in advisors_ids_str[0].split(',')]
            else:
                advisors_id = []

            #advisors_id_str = request.POST.get('advisors_id', '')
            #panel_name_user = request.POST.get('panel_name', '')
            #advisors_id = [int(id) for id in advisors_id_str.split(',') if id.isdigit()]

            # Print the received data in the terminal
            print(f"\n\nReceived card IDs: {advisors_id}")
            
            panel_id = generate_unique_panel_id()
            
            accountants = AccountantInfo.objects.filter(id__in=advisors_id)
            panel_name = panel_name_advisor(accountants)
            new_advisor = panel_advisor_create(accountants, user_id)
            
            advisors_id.append(new_advisor)
            
            accountants = AccountantInfo.objects.filter(id__in=advisors_id)
            if not accountants.exists():
                return redirect('/create-professional-panel')
            
            print("All accountants are here: ", accountants)
            
            

            accountants = sorted(accountants, key=lambda x: x.category_id.category != 'Panel')

            print("All accountants are here: ", accountants)
            
            print("All accountants are here: ", accountants)

            
            
            
            panel = Panel.objects.create(
                        user_id=user_id,
                        panel_name=panel_name,
                        panel_id=panel_id,
                        panel_topic="Testing Topic",
                    )
            panel.accountant_info.add(*accountants)

            user_id = UserInfo.objects.get(id=user_id)
            
            panel_chat = PanelChatLogs.objects.create(
                        panel_id=panel, user_id=user_id)
            
            print("____________ruining till here------------: ", accountants)
            
            # for advisor_id in advisors_id:


            #             # creating greeting message with GPT-API start
            #             advisor = AccountantInfo.objects.get(id=advisor_id)
            #             print("--------loop is working-----", advisor_id)
            #             user_name = request.session.get('user_name')
            #             print('---------user name is here-------', user_name)

            #             greetings_prompt = f"{advisor.context}. give me some greeting message and list of 2-3 point in which ways you can help me. the user name is {user_name} and use your title as your name. IMPORTANT to give reply in maxmimum 60-70 words. DO not add best regards, Regards or extra words Like: 'Summary:', 'Advisor:' in message. Don't add '. Must ask question from user regarding to start further conversation."
            #             message_list = [{"role": "system", "content": greetings_prompt}]

            #             # Call to OpenAI API
            #             completion = openai.ChatCompletion.create(
            #                 model="gpt-3.5-turbo-16k",
            #                 messages=message_list
            #             )

            #             # Parsing the response
            #             main_response = completion.choices[0].message['content']


            #             # Find the corresponding response for the advisor
            #             print("this is working ---------------------------")
            #             # response = chosenCardMainData[chosenCardsIds.index(advisor_id)]
            #             print("this is advisor id by haider: ", advisor_id)
            #             accountant = AccountantInfo.objects.get(id=advisor_id)

            #             panel_message_log = PanelMessageLogs.objects.create(
            #                 response_message=main_response,
            #                 prompt_message="",
            #                 panel_chat_id=panel_chat,
            #                 advisor_id=accountant
            #             )

            # Perform any further processing or return a response
            # response_data = {'status': 'success', 'message': 'Data received successfully'}
            return redirect(f'/chat-open/{panel_id}/')
            # response_data = {'status': 'success', 'message': '{panel_id}'}
            # return JsonResponse(response_data)

        except Exception as e:
            # Handle other errors
            error_message = f"Error: {str(e)}"
            return JsonResponse({'status': 'error', 'message': error_message}, status=400)

    else:
        # Handle non-POST requests
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    

def panel_name_advisor(advisors):
    print("this is advisors data coming in another function: ", advisors)
    
    context_all = []
    
    for advisor in advisors:
        context_all.append(advisor.context)
    
    print("this is collection of string: ", context_all)
    
    greetings_prompt = f"System: suggest me the unique name for panel for multiple advisors which contexts are in this list: {context_all}. Don't give extra words, only return name."
    message_list = [{"role": "system", "content": greetings_prompt}]

    # Call to OpenAI API
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_list
    )

    # Parsing the response
    name = completion.choices[0].message['content']
    
    return name


def panel_advisor_create(advisors, user_id):

    header_text_all = []
    
    for advisor in advisors:
        header_text_all.append(advisor.header_text)
        # Retrieve form data, including user ID
        
    header_text = "Panel Advisor"
    
    selected_header_texts = [AccountantInfo.header_text for AccountantInfo in advisors]
    
    

    user_details = "A professional experienced in {selected_header_texts}, wearing casual business attire, in a modern office setting"
    prompt = create_dalle_prompt(user_details=user_details)

    image_url = generate_image(prompt=prompt)

    if image_url:
        print(image_url)
        
        accountant_image = download_image(image_url)

    else:



        accountant_image = 'occupational_images/default.png'

    
    category_data = AccountantCategories.objects.filter(category='Panel').first()
    
    user_info_instance = UserInfo.objects.get(id=user_id)

    context = get_prompt_for_custom_advisor(selected_header_texts, header_text_all)
    
    tag_line_text = panel_tag_line(advisors)
    # advisor_name = panel_advisor_name(advisors)
    advisor_name = "PIIS"

    # Create and save the AccountantInfo object
    accountant_info = AccountantInfo(
        header_text=advisor_name,
        tagline_text=tag_line_text,
        description='description',
        context=context,
        question='',
        category_id=category_data,
        accountant_image=accountant_image,
        rating="5",
        user_id=user_info_instance  # Assuming user_id is a valid foreign key
    )

    accountant_info.save()

    return accountant_info.id


def panel_tag_line(advisors):
    print("this is advisors data coming in another function: ", advisors)
    context_all = []
    for advisor in advisors:
        context_all.append(advisor.context)
    
    print("this is collection of string: ", context_all)
    
    greetings_prompt = f"System: suggest me the unique tag line (one line) for panel for multiple advisors which contexts are in this list: {context_all}. Don't give extra words."
    message_list = [{"role": "system", "content": greetings_prompt}]

    # Call to OpenAI API
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_list
    )

    # Parsing the response
    name = completion.choices[0].message['content']
    
    return name

def panel_advisor_name(advisors):
    print("this is advisors data coming in another function: ", advisors)
    context_all = []
    for advisor in advisors:
        context_all.append(advisor.context)
    
    print("this is collection of string: ", context_all)

    greetings_prompt = f"System: suggest me the unique name for advisor which is combination of multiple advisors which contexts are in this list: {context_all}. Don't give extra words. Give me 1-2 words name"
    message_list = [{"role": "system", "content": greetings_prompt}]

    # Call to OpenAI API
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_list
    )

    # Parsing the response
    name = completion.choices[0].message['content']
    
    return name


@csrf_exempt
def card_delete_chat(request):
    try:
        data = json.loads(request.body)
        chat_log_id = data.get('id')
        chat_log = ChatLogs.objects.get(id=chat_log_id)
        chat_log.delete()
        return JsonResponse({"message": "Chat log deleted successfully"}, status=200)
    except ChatLogs.DoesNotExist:
        return JsonResponse({"error": "Chat log not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@csrf_exempt
def card_delete_panelchat(request):
    try:
        data = json.loads(request.body)
        chat_log_id = data.get('id')
        chat_log = Panel.objects.get(id=chat_log_id)
        chat_log.delete()
        return JsonResponse({"message": "Chat log deleted successfully"}, status=200)
    except ChatLogs.DoesNotExist:
        return JsonResponse({"error": "Chat log not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
# @csrf_exempt
# def favorite(request):
#     try:
#         data = json.loads(request.body)
#         star_status = data.get('star_status')
#         card_id = data.get('card_id')
#         user_id = request.session['user_id']
#         chat_log = Panel.objects.get(id=chat_log_id)
#         chat_log.delete()
#         return JsonResponse({"message": "Chat log deleted successfully"}, status=200)
#     except ChatLogs.DoesNotExist:
#         return JsonResponse({"error": "Chat log not found"}, status=404)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def favorite(request):
    if request.method == 'POST':
        accountant_id = request.POST.get('card_id')
        user_id = request.session['user_id']
        like_status = request.POST.get('star_status')

        # Get the user and accountant instances
        user = get_object_or_404(UserInfo, id=user_id)
        accountant = get_object_or_404(AccountantInfo, id=accountant_id)

        # Check if there is an existing FavoriteAdvisor entry
        favorite_entry = FavoriteAdvisor.objects.filter(user=user, advisor=accountant).first()

        if like_status == 'true':
            # If like_status is 'true', add to favorites
            if not favorite_entry:
                FavoriteAdvisor.objects.create(user=user, advisor=accountant)
                return JsonResponse({'message': 'Added to favorites'}, status=200)

        elif like_status == 'false':
            # If like_status is 'false', remove from favorites
            if favorite_entry:
                favorite_entry.delete()
                return JsonResponse({'message': 'Removed from favorites'},status=200)

    return JsonResponse({'message': 'Invalid request'}, status=400)



@check_user_login
def favorites(request):
    specific_user_id = request.session.get('user_id')

    user = UserInfo.objects.get(id=request.session.get('user_id'))
    
    # Get the ID of the "Custom" category
    cat_id_queryset = AccountantCategories.objects.filter(category='Custom')
    cat_id = cat_id_queryset.first().id if cat_id_queryset.exists() else None
    
    # Get the "Panel" category
    excluded_category = AccountantCategories.objects.get(category='Panel')
    
    print("Excluded Category ID:", excluded_category.id)

    # Get the IDs of favorite accountants
    favorite_advisor_ids = user.favorite_advisors.values_list('id', flat=True)

    # Fetch the corresponding AccountantInfo objects
    search_accountant_info = AccountantInfo.objects.filter(id__in=favorite_advisor_ids)

    search_try_saying_accountant_info = AccountantInfo.objects.filter(
        ~Q(category_id__id=cat_id) | (Q(category_id__id=cat_id) & Q(user_id__id=specific_user_id)),
        ~Q(category_id=excluded_category.id)
    ).order_by('-rating')

    print("Search Accountant Info:", search_accountant_info)
    print("Search Try Saying Accountant Info:", search_try_saying_accountant_info)
    
    search_categories = AccountantCategories.objects.exclude(category='Panel').order_by('category')

    print("Search Categories:", search_categories)

    uid = current_user(request)

    return render(request, 'home.html', {'user': user,
                                        'data': search_accountant_info,
                                        'categories': search_categories,
                                        'current_user': uid,
                                        'try_saying_data': search_try_saying_accountant_info})

def delete_advisor_from_panel(request):
    if request.method == 'POST':
        # Retrieve panel_id and advisor_id from the POST data
        panel_id = request.POST.get('pid')
        advisor_id = request.POST.get('aid')

        # Validate that both panel_id and advisor_id are provided
        if not panel_id or not advisor_id:
            return JsonResponse({'error': 'Panel ID and Advisor ID are required.'}, status=400)

        # Get the panel and advisor instances
        panel = get_object_or_404(Panel, id=panel_id)
        advisor = get_object_or_404(AccountantInfo, id=advisor_id)

        # Remove the advisor from the panel
        panel.accountant_info.remove(advisor)

        # Delete related objects if needed (adjust as per your requirements)
        PanelChatLogs.objects.filter(panel_id=panel, user_id=advisor.user_id).delete()
        PanelMessageLogs.objects.filter(advisor_id=advisor, panel_chat_id__panel_id=panel).delete()

        # Check if there are no remaining advisors in the panel
        remaining_advisors = panel.accountant_info.all()
        if not remaining_advisors.exists() or len(remaining_advisors) ==1:
            # If no remaining advisors, delete the panel
            panel.delete()
            return JsonResponse({'success': 'Advisor removed, and panel deleted successfully.'})
        else:
            return JsonResponse({'success': 'Advisor removed from panel successfully.'})
        

    return JsonResponse({'error': 'Invalid request method.'}, status=400)
from django.core.cache import cache

def clear_cache(request):
    # Clear the entire cache
    cache.clear()
    
    return HttpResponse("Cache cleared successfully.")



# api to fetch advisors
def all_advisors_api(request):
    if request.method == 'GET':
        advisors = AccountantInfo.objects.values()
        return JsonResponse(list(advisors), safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)


def add_advisor_panel(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            panel_id = data.get('panel_id')
            advisor_ids = data.get('advisor_ids', [])

            # Validate that both panel_id and advisor_ids are provided
            if not panel_id or not advisor_ids:
                return JsonResponse({'error': 'Panel ID and Advisor IDs are required.'}, status=400)

            # Get the panel instance
            panel = get_object_or_404(Panel, id=panel_id)

            # Get the advisor instances
            advisors = AccountantInfo.objects.filter(id__in=advisor_ids)

            # Add advisors to the panel (replace 'accountant_info' with the actual field name)
            panel.accountant_info.add(*advisors)

            return JsonResponse({'success': 'Advisors added to the panel successfully.'})
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def man_or_woman():
    return random.choice(['woman', 'man'])

# code to generate images start
def generate_image(prompt, size="1024x1024", n=1, quality="standard"):
    response = openai.Image.create(
        model="dall-e-3",
        prompt=prompt,
        n=n,
        size=size,
        quality=quality
    )
    return response['data'][0]['url']

def create_dalle_prompt(user_details):
    human=man_or_woman()
    base_prompt = "A professional profile photo of a {human} in a suit, perfect for an executive office profile, with an extremely soft and minimal detail appearance. The man is smiling gently, facing straight towards the camera with the camera angle directly centered. The image should have very soft studio lighting and a highly blurry background, styled as a corporate portrait headshot. The photo should be realistic but with the least possible detail, creating a very warm, approachable, yet professional look. The composition should be perfectly centered and symmetrical, providing a balanced and welcoming appearance."
    return base_prompt

def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        media_root = settings.MEDIA_ROOT
        images_folder = 'occupational_images/'

        # Ensure the destination folder exists
        destination_folder = os.path.join(media_root, images_folder)
        os.makedirs(destination_folder, exist_ok=True)

        # Generate a random 16-digit alphanumeric filename
        random_filename = secrets.token_hex(8)  # 16 characters, each character represents 4 bits

        file_path = os.path.join(destination_folder, random_filename + '.jpg')  # Assuming the image is in JPEG format

        with open(file_path, 'wb') as file:
            file.write(response.content)

        return os.path.join(images_folder, random_filename + '.jpg')

    except Exception as e:
        print(f"Failed to download image: {e}")
# code to generate images end
        
@check_user_login
def documentation(request):
    return render(request, 'documentation.html')
