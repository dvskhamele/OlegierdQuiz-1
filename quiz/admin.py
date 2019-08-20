from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ugettext_lazy as _

from .models import Quiz, Category, SubCategory, Progress, Question , PersonalizedQuiz , UQuestion ,User  #,TimeZone 
from multichoice.models import MCQuestion, Answer
from true_false.models import TF_Question
from essay.models import Essay_Question

from import_export.admin import ImportExportModelAdmin

import tablib
from import_export import resources
from .forms import CustomUserCreationForm , CustomUserChangeForm
from .resources import QuizResource ,QuizafterResource

from django.contrib.auth.admin import UserAdmin

class UserAdmin(UserAdmin):
 
    add_form = CustomUserCreationForm    
    form = CustomUserChangeForm
    model = User
    list_display = ["email","username", "timezone1"]
    list_filter = ["timezone1","username"]

    fieldsets = (
        (None, {'fields': ('timezone1', )}),
        # (('Personal info'), {'fields': ('first_name', 'last_name')}),
        # (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
        # 'groups', 'user_permissions')}),
        # (('Important dates'), {'fields': ('last_login', 'date_joined')}),
        )


    # add_fieldsets = (
    #     (None, {
    #     'classes': ('wide',),
    #     'fields': ('email', 'first_name', 'last_name', 'password1',
    #     'password2',)})
    #     )




class AnswerInline(admin.TabularInline): 
    model = Answer

class QuizAdminForm(forms.ModelForm):
    """
    below is from
    http://stackoverflow.com/questions/11657682/
    django-admin-interface-using-horizontal-filter-with-
    inline-manytomany-field
    """


    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all().select_subclasses(),
        required=False,
        label=_("Questions"),
        widget=FilteredSelectMultiple(
            verbose_name=_("Questions"),
            is_stacked=False))

    def __init__(self, *args, **kwargs):
        super(QuizAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['questions'].initial =\
                self.instance.question_set.all().select_subclasses()

    def save(self, commit=True):
        quiz = super(QuizAdminForm, self).save(commit=False)
        quiz.save()
        quiz.question_set.set(self.cleaned_data['questions'])
        self.save_m2m()
        return quiz


class QuizAdmin(ImportExportModelAdmin):
    form = QuizAdminForm

    list_display = ('title', 'category', )
    list_filter = ('category',)
    search_fields = ('description', 'category', )
    resource_class = QuizResource

class CategoryAdmin(ImportExportModelAdmin):
    search_fields = ('category', )


class SubCategoryAdmin(ImportExportModelAdmin):
    search_fields = ('sub_category', )
    list_display = ('sub_category', 'category',)
    list_filter = ('category',)


class MCQuestionAdmin(ImportExportModelAdmin):
    list_display = ('content', 'category', )
    list_filter = ('category',)
    fields = ('content', 'category', 'sub_category',
              'quiz', 'explanation', 'answer_order')

    search_fields = ('content', 'explanation')
    filter_horizontal = ('quiz',)

    inlines = [AnswerInline]
    resource_class = QuizafterResource

class ProgressAdmin(ImportExportModelAdmin):
    """
    to do:
            create a user section
    """
    search_fields = ('user', 'score', )


class TFQuestionAdmin(ImportExportModelAdmin):
    list_display = ('content', 'category', )
    list_filter = ('category',)
    fields = ('content', 'category', 'sub_category',
              'figure', 'quiz', 'explanation', 'correct',)

    search_fields = ('content', 'explanation')
    filter_horizontal = ('quiz',)


class EssayQuestionAdmin(ImportExportModelAdmin):
    list_display = ('content', 'category', )
    list_filter = ('category',)
    fields = ('content', 'category', 'sub_category', 'quiz', 'explanation', )
    search_fields = ('content', 'explanation')
    filter_horizontal = ('quiz',)


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(MCQuestion, MCQuestionAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(TF_Question, TFQuestionAdmin)
admin.site.register(Essay_Question, EssayQuestionAdmin)
admin.site.register(PersonalizedQuiz)
admin.site.register(UQuestion)
admin.site.register(Answer)
admin.site.register(User , UserAdmin)
# admin.site.register(TimeZone)