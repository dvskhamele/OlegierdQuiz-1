from django import forms
from django.forms.widgets import RadioSelect, Textarea
import random
from .models import PersonalizedQuiz,UQuestion


from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = UserChangeForm.Meta.fields







class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)        
        choice_list = [x for x in question.get_answers_list()]
        random.shuffle(choice_list)
        self.fields["answers"] = forms.ChoiceField(choices=choice_list,
                                                   widget=RadioSelect)
        #print("get_answers_list()",get_answers_list())

class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={'style': 'width:100%'}))
        print("answers1",answers)



class PersonalizedQuizForm(forms.ModelForm):
    max_questions = forms.IntegerField(label='max_questions', min_value=1,max_value=1000)
    repeat_questions = forms.IntegerField(label='repeat_questions', min_value=1,max_value=1000)
    class Meta:
        model= PersonalizedQuiz
        fields= ["max_questions", "repeat_questions"]


class UQuestionForm(forms.ModelForm):
    questions_id = forms.IntegerField(label='questions_id', min_value=1,max_value=1000)
    attemp_question = forms.IntegerField(label='attemp_question', min_value=1,max_value=1000)
    correct_answer = forms.IntegerField(label='correct_answer', min_value=1,max_value=1000)
    class Meta:
        model= UQuestion
        fields= ["questions_id", "attemp_question","correct_answer"]