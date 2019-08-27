from django.contrib import admin
from django.urls import path
from django.conf import settings 
from django.conf.urls.static import static
from django.conf.urls import include

urlpatterns = [
    path('', include('fileloader.urls')), #path('fileloader/', include('fileloader.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('quiz/', include('quiz.urls')),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)