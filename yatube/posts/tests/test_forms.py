import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='GroupTest',
            slug='SlugTest',
            description='DescriptionTest',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='TextTestFixtures',
            group=cls.group,
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        '''Тестирование создания формы и проверка, что она появляется в БД'''
        Post.objects.all().delete()
        form_fields = {
            'text': 'TestTextCreate',
            'group': self.group.id,
            'image': self.uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_fields,
            follow=True
        )

        self.assertEqual(Post.objects.count(), 1)
        created_post = Post.objects.first()

        self.assertEqual(created_post.text, form_fields['text'])
        self.assertEqual(created_post.group.id, form_fields['group'])
        self.assertEqual(created_post.author, self.author)
        self.assertEqual(created_post.image, 'posts/small.gif')

    def test_edit_post(self):
        '''При редактировании поста он меняется в БД'''
        test_data = {'text': 'EditText',
                     'group': self.group.id}
        self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ),
            data=test_data,
            follow=True
        )
        post_after_edit = Post.objects.get(id=self.post.pk)
        self.assertEqual(post_after_edit.text, test_data['text'])
        self.assertEqual(post_after_edit.author, self.post.author)
        self.assertEqual(post_after_edit.group.id, test_data['group'])

    def test_create_comment(self):
        """
        Тест добавления комментария
        """
        Comment.objects.all().delete()
        form = {
            'text': 'CommentTest',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 1)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}
                                     )
                             )
        comments_after_add = Comment.objects.get(post=self.post.id)
        self.assertEqual(
            comments_after_add.text, form['text']
        )

    def test_create_comment_anon(self):
        """
        Тестирование, что анонимный пользователь
        не сможет добавить комментарий
        """
        Comment.objects.all().delete()
        form = {
            'text': 'CommentTestAnon',
        }
        response = self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts'
            f'/{self.post.id}/comment/'
        )
