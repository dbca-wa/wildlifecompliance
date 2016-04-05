from django.conf.urls import patterns, url
from django.contrib.auth import views as auth_views

from ledger.accounts import views

urlpatterns = patterns('accounts',
    url(r'^$', views.home, name='home'),
    url(r'^done/$', views.done, name='done'),
    url(r'^validation-sent/$', views.validation_sent, name='validation_sent'),
    url(r'^token-login/(?P<token>[^/]+)/$', views.token_login, name='token_login'),
    url(r'^logout/', auth_views.logout, {'next_page': 'accounts:home'}, name='logout'),
)
