

from django.conf.urls import url


from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^participate/$', views.participate, name='participate'),
    url(r'^check_fp/$', views.check_fp, name='check_fp'),
    url(r'^canvas/$', views.canvas, name='canvas'),
    url(r'^update_canvas/$', views.update_canvas, name='update_canvas'),
    url(r'^authenticate/$', views.authenticate, name='authenticate'),
    url(r'^check_authentication/$', views.check_authentication, name='check_authentication')
]

