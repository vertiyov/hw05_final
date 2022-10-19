from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

User = get_user_model()


def paginate_posts(page_number, posts):
    paginator = Paginator(posts, settings.COUNT_POSTS)
    return paginator.get_page(page_number)


def index(request):
    posts = Post.objects.select_related(
        'author', 'group')
    page_number = request.GET.get('page')
    context = {
        'page_obj': paginate_posts(page_number, posts),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related(
        'author', )
    page_number = request.GET.get('page')
    context = {
        'page_obj': paginate_posts(page_number, posts),
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    is_following = Follow.objects.select_related(
        'author').exists()
    following = False
    if author != request.user and is_following:
        following = True
    posts = author.posts.select_related(
        'group', )
    page_number = request.GET.get('page')
    context = {
        'page_obj': paginate_posts(page_number, posts),
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related(
        'author', 'group', ), pk=post_id)
    comment = Comment.objects.filter(post=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comment,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    context = {
        'form': form,
    }
    if form.is_valid():
        post = form.save()
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post.objects.select_related(
        'author', ), pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'is_edit': True,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_number = request.GET.get('page')
    context = {
        'page_obj': paginate_posts(page_number, posts),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("posts:profile", username=username)
