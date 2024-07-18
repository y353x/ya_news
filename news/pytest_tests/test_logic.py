# Анонимный пользователь не может отправить комментарий.
# Авторизованный пользователь может отправить комментарий.
# Если комментарий содержит запрещённые слова, он не будет опубликован,
# а форма вернёт ошибку.
# Авторизованный пользователь может редактировать или удалять свои комментарии.
# Авторизованный пользователь не может редактировать или удалять
# чужие комментарии.
import pytest
from django.urls import reverse
from http import HTTPStatus
from pytest_django.asserts import assertRedirects, assertFormError
from news.forms import BAD_WORDS, WARNING
from news.models import Comment
from .conftest import COMMENT_TEXT, NEW_COMMENT_TEXT

pytestmark = pytest.mark.django_db


def test_anonymous_user_cant_create_comment(client, news, form_data):
    """Анонимный пользователь не может отправить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_can_create_comment(
    not_author_client, not_author, news, form_data
):
    """Авторизованный пользователь может отправить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    response = not_author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text, COMMENT_TEXT
    assert comment.news, news
    assert comment.author, not_author


def test_user_cant_use_bad_words(not_author_client, news_id_for_args):
    """
    Если комментарий содержит запрещённые слова, он не будет опубликован,
    а форма вернёт ошибку.
    """
    url = reverse('news:detail', args=(news_id_for_args))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = not_author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(comment_id_for_args,
                                   author_client, news_id_for_args):
    """Авторизованный пользователь может удалять свои комментарии."""
    delete_url = reverse('news:delete', args=(comment_id_for_args))
    news_url = reverse('news:detail', args=(news_id_for_args))
    url_to_comments = news_url + '#comments'
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_cant_delete_comment_of_another_user(comment_id_for_args,
                                                  not_author_client,
                                                  news_id_for_args):
    """Авторизованный пользователь не может удалять
    чужие комментарии.
    """
    delete_url = reverse('news:delete', args=(comment_id_for_args))
    response = not_author_client.delete(delete_url)
    # Проверяем, что вернулась 404 ошибка.
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Убедимся, что комментарий по-прежнему на месте.
    comments_count = Comment.objects.count()
    assert comments_count == 1


def test_author_can_edit_comment(comment_id_for_args, comment,
                                 author_client, news_id_for_args,
                                 another_form_data):
    """Авторизованный пользователь может редактировать свои комментарии."""
    edit_url = reverse('news:edit', args=(comment_id_for_args))
    news_url = reverse('news:detail', args=(news_id_for_args))
    url_to_comments = news_url + '#comments'
    response = author_client.post(edit_url, data=another_form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT_TEXT


def test_user_cant_edit_comment_of_another_user(
        not_author_client, another_form_data, comment_id_for_args, comment):
    """Авторизованный пользователь не может редактировать
    чужие комментарии.
    """
    edit_url = reverse('news:edit', args=(comment_id_for_args))
    response = not_author_client.post(edit_url, data=another_form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text, COMMENT_TEXT
