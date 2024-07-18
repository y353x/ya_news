# Количество новостей на главной странице — не более 10.
# Новости отсортированы от самой свежей к самой старой.
#      Свежие новости в начале списка.
# Комментарии на странице отдельной новости отсортированы
#      в хронологическом порядке: старые в начале списка, новые — в конце.
# Анонимному пользователю недоступна форма для отправки комментария
#      на странице отдельной новости, а авторизованному доступна.
import pytest
from django.conf import settings
from django.urls import reverse
from news.forms import CommentForm

pytestmark = pytest.mark.django_db


def test_news_count(news_on_page, client):
    """Количество новостей на главной странице — не более 10."""
    # news_on_page для создания 10 новостей.
    HOME_URL = reverse('news:home')
    response = client.get(HOME_URL)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(news_on_page, client):
    """Новости отсортированы от самой свежей к самой старой."""
    HOME_URL = reverse('news:home')
    response = client.get(HOME_URL)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


# Или объединить 2 теста, но не будет независимости

# def test_news_count_and_order(news_on_page, client):
#     # news_on_page для создания 10 новостей.
#     HOME_URL = reverse('news:home')
#     response = client.get(HOME_URL)
#     object_list = response.context['object_list']
#     news_count = object_list.count()
#     # assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE
#     all_dates = [news.date for news in object_list]
#     sorted_dates = sorted(all_dates, reverse=True)
#     # assert all_dates == sorted_dates
#     pairs = ((news_count, settings.NEWS_COUNT_ON_HOME_PAGE),
#              (all_dates, sorted_dates))
#     for arg_1, arg_2 in pairs:
#         assert arg_1 == arg_2


def test_comments_order(comment, client, news):
    """
    Комментарии на странице отдельной новости отсортированы
    в хронологическом порядке: старые в начале списка, новые — в конце.
    """
    detail_url = reverse('news:detail', args=(news.id,))
    response = client.get(detail_url)
    assert 'news' in response.context
    # Получаем объект новости.
    news = response.context['news']
    # Получаем все комментарии к новости.
    all_comments = news.comment_set.all()
    # Собираем временные метки.
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    # Проверяем, что временные метки отсортированы правильно.
    assert all_timestamps == sorted_timestamps


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('client'), False),
        (pytest.lazy_fixture('author_client'), True)
    ),
)
def test_availability_form(parametrized_client, expected_status, news):
    """
    Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости, а авторизованному доступна.
    """
    detail_url = reverse('news:detail', args=(news.id,))
    response = parametrized_client.get(detail_url)
    assert ('form' in response.context) is expected_status
    if expected_status:
        assert isinstance(response.context['form'], CommentForm)
