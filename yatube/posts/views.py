from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

from .models import Group, Post, Comment, Follow, User
from .forms import PostForm, CommentForm

TEN_POSTS = 10
TWENTY_SEC = 20


def pagination(request, posts):
    paginator = Paginator(posts, TEN_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(TWENTY_SEC, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('group', 'author')
    page_obj = pagination(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = pagination(request, posts)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    page_obj = pagination(request, posts)
    count_posts = author.posts.count()
    if request.user.is_authenticated and request.user != author:
        following = Follow.objects.select_related(
            'user', 'author'
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'count_posts': count_posts,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post_id=post.id)
    author = post.author
    count_posts = author.posts.count()
    context = {
        'post': post,
        'author': author,
        'count_posts': count_posts,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=edit_post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user).select_related('author')
    page_obj = pagination(request, posts)
    content = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', content)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    follower = Follow.objects.filter(
        user=request.user, author__username=username)
    if follower.exists():
        follower.delete()
    return redirect('posts:profile', username=username)
