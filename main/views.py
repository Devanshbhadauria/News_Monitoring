from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import feedparser
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from dateutil.parser import parse
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse

from .forms import SignupForm, LoginForm, SourceForm, StoryForm
from .models import Subscribe, Company, Source, Story


def fetch(url):
    feed_data = feedparser.parse(url)
    data = []
    for item in feed_data.entries:
        story = {
            'title': item.title[:100],
            'pub_date': item.published,
            'description': item.summary[:150],
            'url': item.link,
        }
        data.append(story)

    return data


def stories_from_source(a, user):
    stories = fetch(a.url)
    client = a.client
    for story_data in stories:
        existing_story = Story.objects.filter(url=story_data.get('url', '')).exists()
        if not existing_story:
            Story.objects.create(
                title=story_data['title'],
                pub_date=parse(story_data['pub_date']),
                body_text=story_data['description'],
                url=story_data['url'],
                source=a,
                client=client,
                created_by=user,

            )


def index(request):
    return render(request, "index.html")


@transaction.atomic
def signup(request):
    companies = Company.objects.values_list('name', flat=True)
    companies = list(companies)

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']
            client_name = request.POST['client']

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'signup.html', {'form': form})

            if password != confirm_password:
                messages.error(request, 'The passwords do not match.')
                return render(request, 'signup.html', {'form': form})

            user = form.save(commit=False)
            user.set_password(password)
            user.save()
            client = Company.objects.get(name=client_name)
            a = Subscribe.objects.create(
                user=user,
                client=client
            )
            login(request, user)
            sources = Source.objects.filter(client=a.client)
            if sources.exists():
                return redirect(reverse('story'))
            else:
                return redirect(reverse('add_source'))
        else:
            return render(request, 'signup.html', {'form': form})
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form, 'companies': companies})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                client = Company.objects.get(subscribe__user=user)
                sources = client.sources.all()
                if sources.exists():
                    return redirect(reverse('story'))
                else:
                    return redirect(reverse('add_source'))
        else:
            error_message = "Invalid username or Password"
            return render(request, 'login.html', {'form': form, 'error_message': error_message})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def source(request):
    if request.user.is_authenticated:
        client = request.user.subscribe.client
        sources = Source.objects.filter(client=client).annotate(num_stories=Count('story'))
        query = request.GET.get('q')
        if query:
            sources = sources.filter(Q(name__icontains=query) | Q(url__icontains=query))
        return render(request, 'source.html', {'sources': sources, 'query': query})
    else:
        return redirect('login')


def fetch_stories(request, source_id):
    client = request.user.subscribe.client
    user = request.user
    source = Source.objects.get(id=source_id)
    feed = feedparser.parse(source.url)
    new_stories_count = 0
    for entry in feed.entries:
        existing_story = Story.objects.filter(url=entry.get('link', ''), source=source).first()
        if existing_story is None:
            obj = Story.objects.create(
                title=entry.get('title', ''),
                body_text=entry.get('description', ''),
                source=source,
                pub_date=parse(entry['published']),
                url=entry['link'],
                client=client,
                created_by=source.created_by,
            )
            new_stories_count += 1
    redirect_url = reverse('story')
    if source_id:
        redirect_url += f'?source_id={source_id}'
    if new_stories_count:
        if '?' in redirect_url:
            redirect_url += f'&new_stories_count={new_stories_count}'
        else:
            redirect_url += f'?new_stories_count={new_stories_count}'
    return redirect(redirect_url)


def logout_view(request):
    logout(request)
    return redirect(reverse('login'))


@login_required
def story(request):
    source_id = request.GET.get('source_id')
    client = request.user.subscribe.client
    sources = Source.objects.filter(client=client)
    new_stories_count = request.GET.get('new_stories_count')
    sources = sources.prefetch_related('story_set')

    if source_id:
        source = sources.filter(id=source_id).first()
        if not source:
            return redirect('source')
        stories = source.story_set.order_by('-pub_date')
        source_name = source.name
    else:
        source_name = "All Sources"
        stories = Story.objects.filter(source__in=sources).order_by('-pub_date')

    query = request.GET.get('q')
    if query:
        stories = stories.filter(Q(title__icontains=query) | Q(body_text__icontains=query))

    return render(request, 'story.html', {
        'source_name': source_name, 'stories': stories, 'query': query,
                                          'new_stories_count': new_stories_count
        })


def add_or_edit_story(request):
    story_id = request.GET.get('story_id')
    if story_id:
        story = get_object_or_404(Story, id=story_id)
        if request.method == 'POST':
            form = StoryForm(request.POST, instance=story)
            if form.is_valid():
                form.instance.updated_by = request.user
                form.instance.updated_on = timezone.now()
                form.save()
                return redirect('story')
        else:
            form = StoryForm(instance=story)
    else:
        if request.method == 'POST':
            form = StoryForm(request.POST)
            if form.is_valid():
                story = form.save(commit=False)
                story.created_by = request.user
                story.client = request.user.subscribe.client
                story.save()
                form.save_m2m()

                new_company_name = request.POST.get('new_company_name')
                if new_company_name:
                    new_company = Company.objects.create(name=new_company_name)
                    story.companies.add(new_company)

                return redirect('story')
        else:
            form = StoryForm()

    return render(request, 'add_edit_story.html', {'form': form})


def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if request.method == 'POST':
        story.delete()
        return redirect(reverse('story'))
    else:
        return render(request, 'delete_story.html', {'story': story})


def delete(request, source_id):
    source = get_object_or_404(Source, id=source_id)
    if request.method == 'POST':
        source.delete()
        return redirect(reverse('source'))
    else:
        return render(request, 'delete.html', {'source': source})


def add_or_edit_source(request):
    source_id = request.GET.get('source_id')
    if source_id:
        source = get_object_or_404(Source, pk=source_id)
        editing = True
    else:
        source = None
        editing = False

    if request.method == 'POST':
        form = SourceForm(request.POST, instance=source)
        if form.is_valid():
            source = form.save(commit=False)
            source.client = request.user.subscribe.client
            if editing:
                source.updated_by = request.user
                source.updated_on = timezone.now()
            else:
                source.created_by = request.user
            source.save()
            stories_from_source(source, request.user)
            return redirect('source')
    else:
        form = SourceForm(instance=source)

    return render(request, 'add_edit_source.html', {'form': form})


def delete(request, source_id):
    source = get_object_or_404(Source, id=source_id)
    if request.method == 'POST':
        source.delete()
        return redirect(reverse('source'))
    else:
        return render(request, 'delete.html', {'source': source})


def save_new_company(request):
    if request.method == 'POST':
        company_name = request.POST.get('company_name')
        new_company = Company.objects.create(name=company_name)
        return JsonResponse({'company_id': new_company.id})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
