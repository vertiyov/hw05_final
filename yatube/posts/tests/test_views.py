import shutil
import tempfile
from math import ceil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='GroupTest',
            slug='SlugTest',
            description='DescriptionTest',
        )
        cls.other_group_for_test = Group.objects.create(
            title='GroupTest2',
            slug='SlugTest2',
            description='DescriptionTest2',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='TextTest',
            group=cls.group,
            image=cls.uploaded
        )

        cls.COUNT_POSTS_FOR_TEST = 3

        posts = []

        for post in range(cls.COUNT_POSTS_FOR_TEST):
            posts.append(Post(
                text='TextTest',
                author=cls.author,
                group=cls.group,
                image=cls.uploaded
            ))
        Post.objects.bulk_create(posts)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_uses_correct_context(self):
        """Index, group_posts проверка контекста
         и что новый пост выводится на страницу"""
        url_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author.username})
        ]

        for url in url_list:
            response = self.guest_client.get(url)
            object = response.context['page_obj'].object_list[0]
            with self.subTest(value=response):
                self.assertEqual(object.text, self.post.text)
                self.assertEqual(
                    object.author.username, self.author.username)
                self.assertEqual(object.group.title, self.group.title)

    def test_post_not_on_wrong_position(self):
        """Пост не появляется на странице чужой группы """
        response = self.guest_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.other_group_for_test.slug}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_page_get_correct_object(self):
        """
        Проверка, что на страницу профиля
        передаем объект автора, на страницу
        с постами группы передаем объект группы
        """
        object_list = [
            (reverse('posts:profile',
                     kwargs={'username': self.author.username}),
             'author',
             self.author,
             ),
            (reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}),
             'group',
             self.group,
             ),
        ]
        for url, context_name, expected_object in object_list:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context[context_name],
                                 expected_object)

    def test_post_detail_uses_correct_context(self):
        """Post_detail проверка контекста."""

        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
        )

        self.assertEqual(response.context['post'].text,
                         self.post.text, )
        self.assertEqual(response.context['post'].author.username,
                         self.author.username, )
        self.assertEqual(
            response.context['post'].group.title, self.group.title)
        self.assertEqual(
            response.context['post'].image, self.post.image)

    def test_form_passed(self):
        """Проверяем, что формы в post_create и post_edit корректны"""
        url_list = [
            (reverse('posts:post_create'), False),
            (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.id}), True),
        ]
        self.authorized_client.force_login(self.author)

        for url, is_edit in url_list:
            response = self.authorized_client.get(url)
            self.assertIsInstance(response.context['form'], PostForm)
            if is_edit:
                self.assertEqual(response.context['form'].instance, self.post)

    def test_paginator(self):
        """Проверка паджинатора"""
        COUNT_POSTS_IN_DB = self.COUNT_POSTS_FOR_TEST + 1
        COUNT_PAGE = ceil(COUNT_POSTS_IN_DB / settings.COUNT_POSTS)
        LAST_PAGE_POST_COUNT = (
            COUNT_POSTS_IN_DB - (COUNT_PAGE - 1) * settings.COUNT_POSTS
        )

        if COUNT_PAGE > 1:
            post_count_first_page = settings.COUNT_POSTS
            posts_count_last_page = LAST_PAGE_POST_COUNT
        else:
            post_count_first_page = LAST_PAGE_POST_COUNT
            posts_count_last_page = LAST_PAGE_POST_COUNT

        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         post_count_first_page)

        response = self.client.get(
            reverse('posts:index') + f"?page={COUNT_PAGE}")
        self.assertEqual(len(response.context['page_obj']),
                         posts_count_last_page)

    def test_follow_and_unfollow_user(self):
        '''Проверка возможности подписаться и отписаться'''
        Follow.objects.all().delete()
        follow_object = Follow.objects.create(
            user=self.user, author=self.author
        )
        self.assertIn(follow_object, Follow.objects.all())
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', args=[self.author]),
            follow=True)
        self.assertNotIn(follow_object, Follow.objects.all())

    def test_new_post_for_follower_true(self):
        '''
        Проверка наличия нового поста у подписчика
        и отсутсвие поста у НЕ подписчика
        '''
        Follow.objects.create(
            user=self.user, author=self.author
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(self.post, response.context['page_obj'])

        Follow.objects.all().delete()
        response_after_unfollowing = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(
            self.post, response_after_unfollowing.context['page_obj']
        )

    def test_cache(self):
        """Тестирование кэша главной страницыы"""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        posts = response.content
        Post.objects.all().delete()
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(posts, response.content)
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(posts, response.content)
