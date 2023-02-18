from django.test import TestCase

from posts.models import Group, Post, User, POST_SYMBOLS


class PostModelTest(TestCase):
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

    def test_models_have_correct_object_names(self):
        """Проверка корректного поведения  __str__ у моделей."""
        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_post_symbols(self):
        """ Проверка первых пятнадцати символов поста"""
        post = self.post
        text = post.text[:POST_SYMBOLS]
        self.assertEqual(text, str(post))
