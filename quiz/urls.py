from django.conf.urls.static import static
from django.conf import settings

# from . import views
# from .views import completequestions

try:
    from django.conf.urls import url 
except ImportError:
    from django.urls import re_path as url

#from django.core.urlresolvers import reverse_lazy
from django.urls import reverse_lazy
from django.views.generic import RedirectView

from .views import QuizListView, CategoriesListView, \
    ViewQuizListByCategory, QuizUserProgressView, QuizMarkingList, \
    QuizMarkingDetail, QuizDetailView, QuizTake, quiz1,quizrep  

urlpatterns = [

    url(r'^quiz_index/$', 
        view=QuizListView.as_view(),
        name='quiz_index'), 
 
    url(r'^category/$',
        view=CategoriesListView.as_view(), 
        name='quiz_category_list_all'),

    url(r'^category/(?P<category_name>[\w|\W-]+)/$',
        view=ViewQuizListByCategory.as_view(),
        name='quiz_category_list_matching'),

    url(r'^progress/$', 
        view=QuizUserProgressView.as_view(),
        name='quiz_progress'),

    url(r'^marking/$',
        view=QuizMarkingList.as_view(),
        name='quiz_marking'),

    url(r'^marking/(?P<pk>[\d.]+)/$',
        view=QuizMarkingDetail.as_view(),  
        name='quiz_marking_detail'),

    #  passes variable 'quiz_name' to quiz_take view
    url(r'^(?P<slug>[\w-]+)/$',
        view=QuizDetailView.as_view(),
        name='quiz_start_page'),

    url(r'^(?P<quiz_name>[\w-]+)/take/$',
        view=QuizTake.as_view(),
        name='quiz_question'),

    url(r'^(?P<slug>[\w-]+)/quiz_select/$', quiz1.as_view() , name='quiz_select'),
    url(r'^(?P<slug>[\w-]+)/quiz_question_repeat/$', quizrep.as_view() , name='quiz_question_repeat'),
    
    url(r'$', RedirectView.as_view(url=reverse_lazy('quiz_index'), permanent=False)),

]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
