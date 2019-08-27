from django.urls import path
from django.conf.urls import url
from . import views
from .views import *
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import logout
from django.conf.urls.static import static
  
urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^upload_file$', upload_file, name='upload_file'),
    url(r'^download_file$', download_file, name='download_file'),
    url(r'^download_sample$', download_sample, name='download_sample'),
    url(r'^error_handler$', error_handler, name='error_handler'), 
    url(r'^pagelogout/$', pagelogout,  name='pagelogout'), 
    url(r'^esg_setup/$', esg_setup,  name='esg_setup'),
    url(r'^esg_ready/$', esg_ready,  name='esg_ready'),
    url(r'^error_esg$', error_esg, name='error_esg'),
    url(r'^esg_choose_task$', esg_choose_task, name='esg_choose_task'),
    url(r'^generateonly$', generateonly, name='generateonly'),
    url(r'^calibrateandgenerate$', calibrateandgenerate, name='calibrateandgenerate'),
    url(r'^testesgs$', testesgs, name='testesgs'),
    url(r'^selectmodel$', selectmodel, name='selectmodel'),
    url(r'^onefactormodel$', onefactormodel, name='onefactormodel'),
    url(r'^vasicekmodel$', vasicekmodel, name='vasicekmodel'),
    url(r'^cirmodel$', cirmodel, name='cirmodel'),
    url(r'^hwmodel$', hwmodel, name='hwmodel'),
    url(r'^lmmplusmodel$', lmmplusmodel, name='lmmplusmodel'),
    url(r'^calib_vasicekmodel$', calib_vasicekmodel, name='calib_vasicekmodel'),

]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
