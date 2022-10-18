from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_str(self):
        """Проверяем, что у моделей Post и Group корректно работает __str__."""
        field_str = [
            (self.post, self.post.text[:self.post.LENGHT_STR_TEXT]),
            (self.group, self.group.title),
        ]
        for field, expected_value in field_str:
            with self.subTest(value=field):
                self.assertEqual(expected_value, str(field))

    def test_verbose_name(self):
        field_verboses = (
            ('text', 'Текст', self.post),
            ('title', 'Название группы', self.group),
            ('slug', 'URL', self.group),
            ('description', 'Описаине', self.group)
        )
        for field, expected_value, model in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    model._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        field_help_text = [
            ('text', 'Что вы хотите рассказать?', self.post),
            ('title', 'Введите название группы', self.group),
            ('slug', 'Придумайте название ссылки', self.group),
            ('description', 'Напишите описание к группе', self.group)
        ]
        for field, expected_value, model in field_help_text:
            with self.subTest(field=field):
                self.assertEqual(model._meta.get_field(field).help_text,
                                 expected_value)
