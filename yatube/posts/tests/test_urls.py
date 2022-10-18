from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='GroupTest',
            slug='SlugTest',
            description='DescriptionTest',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='TextTest',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_adress_use_correct_name(self):
        """
        Тест который проверяет соответствие
        фактических адресов страниц с их именами
        """
        names_and_address = [
            (reverse('posts:index'), '/'),
            (reverse('posts:group_posts',
                     kwargs={'slug': self.group.slug}),
             f'/group/{self.group.slug}/'),
            (reverse('posts:profile',
                     kwargs={'username': self.user.username}),
             f'/profile/{self.user.username}/'),
            (reverse('posts:post_detail', kwargs={
                'post_id': self.post.pk
            }), f'/posts/{self.post.pk}/'),
            (reverse('posts:post_create'), '/create/'),
            (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.pk}),
             f'/posts/{self.post.pk}/edit/'),
        ]
        for name, address in names_and_address:
            self.assertEqual(name, address)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        self.authorized_client.force_login(self.author)
        templates_url_names = [
            ('posts/index.html', reverse('posts:index')),
            ('posts/group_list.html',
             reverse('posts:group_posts', kwargs={'slug': self.group.slug})),
            ('posts/profile.html',
             reverse('posts:profile',
                     kwargs={'username': self.user.username})),
            ('posts/post_detail.html',
             reverse('posts:post_detail',
                     kwargs={'post_id': self.post.pk})),
            ('posts/create_post.html', reverse('posts:post_create')),
            ('posts/create_post.html',
             reverse('posts:post_edit',
                     kwargs={'post_id': self.post.pk})),
            ('posts/follow.html', reverse('posts:follow_index')),
        ]
        for template, address in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_at_desired_locations(self):
        """Проверка доступности страниц."""
        urls_names = [
            (reverse('posts:index'), HTTPStatus.OK, False),
            (reverse('posts:group_posts',
                     kwargs={'slug': self.group.slug}), HTTPStatus.OK, False),
            (reverse('posts:profile',
                     kwargs={'username': self.user.username}),
             HTTPStatus.OK, False),
            (reverse('posts:post_detail', kwargs={
                'post_id': self.post.pk
            }), HTTPStatus.OK, False),
            ('/address-non-exists-page/', HTTPStatus.NOT_FOUND, False),
            (reverse('posts:post_create'), HTTPStatus.OK, True),
            (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.pk}), HTTPStatus.OK, True),
            (reverse('posts:follow_index'), HTTPStatus.OK, True),
        ]

        self.authorized_client.force_login(self.author)

        for address, expected_status, need_auth in urls_names:
            with self.subTest(address=address):
                if need_auth:
                    response = self.authorized_client.get(address)
                else:
                    response = self.guest_client.get(address)
                self.assertEqual(response.status_code, expected_status)

    def test_post_edit_url_not_author_redirect(self):
        """
        Страница по адресу /posts/post_id/edit/
        перенаправит авторизованного пользователя, но НЕ АВТОРА
        поста на страницу поста.
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.pk})
        )

    def test_redirect_url(self):
        """
        Проверка работоспособности перенаправления
        со страницы, к которой нет доступа у клиента
        """
        url_redirect = [
            (reverse('posts:post_create'),
             f"{reverse('users:login')}?next={reverse('posts:post_create')}"),

            (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.pk}),
             f"{reverse('users:login')}"
             f"?next="
             f"{reverse('posts:post_edit', kwargs={'post_id': self.post.pk})}")
        ]

        for url, expected in url_redirect:
            response = self.guest_client.get(url)
            with self.subTest(value=response):
                self.assertRedirects(response, expected)
