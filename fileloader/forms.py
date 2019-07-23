from django import forms
from quiz.models import *


CURRENCIES = (("CHF", "CHF"), ("USD","USD"), ("EUR","EUR"),("SGD", "SGD"), ("PLN","PLN"),)
YEARS = ((2018,2018), (2017,2017), (2016,2016),)
MODES = (("drift as input", "drift as input"), ("drift from eiopa curve","drift from eiopa curve"),)
IRSCENARIOS = (("BE", "Base"), ("UP","Shock Up"), ("DOWN","Shock Down"),)
WHICHRATES = (("EIOPA","EIOPA"), ("CUSTOM","CUSTOM"),)

class UploadFileForm(forms.Form):
    file = forms.FileField()


class SetUpESG(forms.Form):
    currency = forms.MultipleChoiceField(label='Choose currencies (one or more):', choices=CURRENCIES, widget=forms.CheckboxSelectMultiple()) #widget=forms.SelectMultiple, choices=CURRENCIES)
    year = forms.ChoiceField(label='Choose year (one only):',widget=forms.RadioSelect, choices=YEARS)
    number_of_scenarios = forms.IntegerField(label='Number of scenarios:', min_value= 1, max_value=1000)
    vector_length = forms.IntegerField(label='Length of vector:', min_value= 1, max_value=1000)
    sig = forms.FloatField(label='Volatility Sigma',min_value=0, max_value=0.5)
    IRscenarios = forms.MultipleChoiceField(label='Choose scenarios (one or more):', choices=IRSCENARIOS, widget=forms.CheckboxSelectMultiple())

class SetUpVasicek(forms.Form):

    number_of_scenarios = forms.IntegerField(label='Number of scenarios:', min_value= 1, max_value=1000, initial = 31)
    vector_length = forms.IntegerField(label='Length of vector:', min_value= 1, max_value=1200, initial = 40)
    start_rate = forms.FloatField(label='start rate',min_value=-1, max_value=1, initial = 0)
    alpha = forms.FloatField(label='Alpha Parameter',min_value=-1, max_value=1, initial = 0.02)
    beta = forms.FloatField(label='Beta Parameter',min_value=-1, max_value=1, initial = 0.03)
    sig = forms.FloatField(label='Volatility Sigma',min_value=-1, max_value=1, initial = 0.05)
    IRscenarios = forms.MultipleChoiceField(label='Choose scenarios (one or more):', choices=IRSCENARIOS, widget=forms.CheckboxSelectMultiple())

class CalibVasicek(forms.Form):

    number_of_scenarios = forms.IntegerField(label='Number of scenarios:', min_value= 1, max_value=1000, initial = 31)
    vector_length = forms.IntegerField(label='Length of vector:', min_value= 1, max_value=1200, initial = 40)
    IRscenarios = forms.MultipleChoiceField(label='Choose scenarios (one or more):', choices=IRSCENARIOS, widget=forms.CheckboxSelectMultiple()) #, initial = ("BE", "Base"))
    rates_to_calibrate = forms.ChoiceField(label='Choose if you want to use EIOPA or CUSTOM rates to calibrate:',widget=forms.Select, choices=WHICHRATES)
    curr = forms.ChoiceField(label='If EIOPA, please choose currency',widget=forms.Select, choices=CURRENCIES, required = False)
    year = forms.ChoiceField(label='If EIOPA, please choose year',widget=forms.Select, choices=YEARS, required = False)
    file = forms.FileField(label='If CUSTOM chosen, please upload a file with rates', required = False)




# class questionsForm(forms.Form): 
#     max_questions = forms.IntegerField(label='Number Of Questions', min_value=1,max_value=10)
#     print("max_questions",max_questions)
#     class Meta:
#         model=PersonalizedQuiz
#         fields = ('max_questions')

# class quiz1Form(forms.Form):
#     max_questions = forms.IntegerField(label='Number Of Questions', min_value=1,max_value=10)
#     class Meta:
#         model=PersonalizedQuiz
#         fields = ('max_questions')

# # class quiz2Form(forms.Form):
# #     question = forms.IntegerField(label='Number Of Questions', min_value=1,max_value=10)
# #     class Meta:
# #         model=PersionlizeQuiz
# #         fields = ('question')

# class quizrepForm(forms.Form):
#     repeat_questions = forms.IntegerField(label='Number Of Questions', min_value=1,max_value=10)
#     class Meta:
#         model=PersonalizedQuiz
#         fields = ('repeat_questions')