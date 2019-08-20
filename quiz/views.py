import random
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, FormView
import datetime
from .forms import QuestionForm, EssayForm, PersonalizedQuizForm
from .models import *
from essay.models import Essay_Question
from django.views import View 
from rest_framework.decorators import api_view
from django.http import HttpResponse,  Http404
from multichoice.models import MCQuestion,Answer
from django.shortcuts import redirect
from pytz import timezone 
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

class TestingView(TemplateView):
    def get(self, request, quiz_slug, *args, **kwargs):
        uquestions = UQuestion.objects.filter(user=self.request.user,quiz__url=quiz_slug)
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days = 3)
        for uquestion in uquestions:
            uquestion.wrong_answer_date=yesterday
            uquestion.date_of_next_rep=datetime.date.today()
            uquestion.question_taken_date=yesterday
            uquestion.save()
        return render(request, 'progress.html')            

    

 
class QuizMarkerMixin(object):
    @method_decorator(login_required)
    @method_decorator(permission_required('quiz.view_sittings'))
    def dispatch(self, *args, **kwargs): 
        return super(QuizMarkerMixin, self).dispatch(*args, **kwargs)


class SittingFilterTitleMixin(object):
    def get_queryset(self):
        queryset = super(SittingFilterTitleMixin, self).get_queryset()
        quiz_filter = self.request.GET.get('quiz_filter')
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)
        return queryset
 
class QuizListView(ListView):
    model = Quiz

    def get_queryset(self):
        queryset = super(QuizListView, self).get_queryset()
        return queryset.filter(exam_mode=False)

class ExamListView(ListView):
    model = Quiz

    def get_queryset(self):
        queryset = super(ExamListView, self).get_queryset()
        return queryset.filter(exam_mode=True)


class QuizDetailView(DetailView):
    model = Quiz
    slug_field = 'url'
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        quiz=Quiz.objects.get(url=self.kwargs['slug'])
        mode=Quiz.objects.get(title=quiz)
        exam_modes=mode.exam_mode
        random_modes=mode.random_order
        try:
            p=PersonalizedQuiz.objects.get(quiz=quiz, user=request.user)
        except PersonalizedQuiz.DoesNotExist:
            PersonalizedQuiz.objects.create(quiz=quiz, user=request.user,max_questions=5,repeat_questions=25)

        
     


        self.object = self.get_object()

        if self.object.draft and not request.user.has_perm('quiz.change_quiz'):
            raise PermissionDenied

        context = self.get_context_data(object=self.object)
        if exam_modes == False:
            context["exam_mode"] = "OFF"
        else:
            context["exam_mode"] = "ON"
        if random_modes == False:
            context["random_mode"] = "OFF"
        else:
            context["random_mode"] = "ON"

        return self.render_to_response(context)

class CategoriesListView(ListView):
    model = Category


class ViewQuizListByCategory(ListView):
    model = Quiz
    template_name = 'view_quiz_category.html'
    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category,
            category=self.kwargs['category_name']
        )

        return super(ViewQuizListByCategory, self).\
            dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewQuizListByCategory, self)\
            .get_context_data(**kwargs)

        context['category'] = self.category
        return context
    
    def get_queryset(self):
        queryset = super(ViewQuizListByCategory, self).get_queryset()
        return queryset.filter(category=self.category, draft=False)

def progress_reports(request, *args, **kwargs):
    question_ids=[]
    question_corrects=[]
    attemp_questions=[]
    progress_report = []
    for quiz in Quiz.objects.filter(personalized_quizes__user=request.user):
        questions = Question.objects.filter(quiz=quiz)
        total_question=questions.count()
        if total_question == 0:
            continue
        progress_dict = {}
        uquestions = UQuestion.objects.filter(user=request.user,quiz=quiz)
        wrong_answer=uquestions.filter(today_wrong_answer=1).count()
        correct_answer1=uquestions.filter(correct_answer=1).count()
        correct_answer2=uquestions.filter(correct_answer=2).count()
        correct_answer3=uquestions.filter(correct_answer=3).count()
        correct_answer4=uquestions.filter(correct_answer=4).count()
        correct_answer5=uquestions.filter(correct_answer=5).count()
        correct_answer1=abs(correct_answer1-wrong_answer)
        
        correct_answers2=0
        correct_answers3=0
        correct_answers4=0
        correct_answers5=0
        if correct_answer2 > 0:
            correct_answers2=uquestions.filter(correct_answer=2,today_wrong_answer=1).count()

        if correct_answer3 > 0:
            correct_answers3=uquestions.filter(correct_answer=3,today_wrong_answer=1).count()

        if correct_answer4 > 0:
            correct_answers4=uquestions.filter(correct_answer=4,today_wrong_answer=1).count()

        # if correct_answer5 > 0:
        #     correct_answers5=uquestions.filter(correct_answer=5,today_wrong_answer=1).count()

        correct_answer2=correct_answer2-correct_answers2
        correct_answer3=correct_answer3-correct_answers3
        correct_answer4=correct_answer4-correct_answers4
        # correct_answer5=correct_answer5-correct_answers5       
        try:
            progres1=(50 * correct_answer1 /total_question)
            progres2=(25 * correct_answer2 /total_question)
            progres3=(12.5 * correct_answer3 /total_question)
            progres4=(7.5 * correct_answer4 /total_question)
            # progres5=(5 * correct_answer5 /total_question)
            progress_percentage=progres1+progres2+progres3+progres4
            progress_dict["quiz"] = quiz.title
            progress_dict["quiz_report"] = str(round(min(progress_percentage,100),2))

            progress_report.append(progress_dict)

        except PersonalizedQuiz.DoesNotExist:
            return render(request, 'quiz/firstattemptprogress.html')

    return progress_report


class QuizUserProgressView(TemplateView):
    template_name = 'progress.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(QuizUserProgressView, self)\
            .dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = super(QuizUserProgressView, self).get_context_data(**kwargs)
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        context['cat_scores'] = progress.list_all_cat_scores
        context['exams'] = progress.show_exams()
        

        progress_report=progress_reports(self.request)
        context={'progress_report':progress_report}
        return render(request, self.template_name, context)        
class QuizMarkingList(QuizMarkerMixin, SittingFilterTitleMixin, ListView):
    model = Sitting

    def get_queryset(self):
        queryset = super(QuizMarkingList, self).get_queryset()\
                                               .filter(complete=True)

        user_filter = self.request.GET.get('user_filter')
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)

        return queryset 




class QuizMarkingDetail(QuizMarkerMixin, DetailView):
    model = Sitting

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()

        q_to_toggle = request.POST.get('qid', None) 
        if q_to_toggle:
            q = Question.objects.get_subclass(id=int(q_to_toggle))
            if int(q_to_toggle) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(q)
            else:
                sitting.add_incorrect_question(q)

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
        context['questions'] =\
            context['sitting'].get_questions(with_answers=True)

        return context


class QuizTake(FormView):
    form_class = QuestionForm 
    template_name = 'previous_question.html'
    previous_template_name = 'previous_question.html'
    result_template_name = 'result.html'
    single_complete_template_name = 'single_complete.html'
    templates_name = 'progress.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, url=self.kwargs['quiz_name'])

        if self.quiz.draft and not request.user.has_perm('quiz.change_quiz'):
            raise PermissionDenied

        try:
            self.logged_in_user = self.request.user.is_authenticated()
        except TypeError:
            self.logged_in_user = self.request.user.is_authenticated

        if self.logged_in_user:
            try:
                self.sitting = Sitting.objects.user_sitting(request.user,
                                                        self.quiz)
            except PersonalizedQuiz.DoesNotExist:
                return redirect('/quiz/quiz_index/')

            # try:
                # date=datetime.date.today()
                # date=str(date) 
                # date=datetime.datetime.strptime(date, '%Y-%m-%d')
                # question_att_date=datetime.datetime.strptime(second_attempt_day, '%Y-%m-%d')
                # if question_att_date == date:
                #     corection=peronalized_max_questions.correction
            except NameError:
                #return redirect(request, 'quiz/complete_attempt_questions.html')
                content ="Congratulations, you have taken all the Questions already. Please come back tomorrow to repeat!."
                return render(self.request, 'quiz/complete_attempt_questions.html',{'content':content})
        else:
            self.sitting = self.anon_load_sitting()

        if self.sitting is False:
            return render(QuizTake, self.single_complete_template_name)

        return super(QuizTake, self).dispatch(request, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        if self.logged_in_user:
            try:
                if self.sitting.get_first_question() != None:
                    self.question = self.sitting.get_first_question() 

                    self.progress = self.sitting.progress()
                else:
                    return redirect('/quiz/quiz_index/') 
            except Question.DoesNotExist:
                self.sitting.delete()
                return redirect('/quiz/quiz_index/')
        else:
            self.question = self.anon_next_question()
            self.progress = self.anon_sitting_progress()

        if self.question.__class__ is Essay_Question:
            form_class = EssayForm
        else:
            form_class = self.form_class

        return form_class(**self.get_form_kwargs())

    def get_form_kwargs(self):
        kwargs = super(QuizTake, self).get_form_kwargs()
        return dict(kwargs, question=self.question)

    def form_valid(self, form):
        if self.logged_in_user:
            self.form_valid_user(form)
            if self.sitting.get_first_question() is False:
                return self.final_result_user()
        else:
            self.form_valid_anon(form)
            if not self.request.session[self.quiz.anon_q_list()]:
                return self.final_result_anon()

        self.request.POST = {}

        return super(QuizTake, self).get(self, self.request)

    
    def get_context_data(self, **kwargs):
        context = super(QuizTake, self).get_context_data(**kwargs)
        mode=Quiz.objects.get(title=self.quiz)
        mode=mode.exam_mode
        peronalized_max_questions = PersonalizedQuiz.objects.get(quiz=self.quiz, user=self.request.user)
        if mode == False:
            #peronalized_max_questions = PersonalizedQuiz.objects.get(quiz=self.quiz, user=self.request.user)
            modify = UQuestion.objects.get(quiz=self.quiz, user=self.request.user,questions=self.question)
            new_questions=modify.attempt_question
            second_attempt_day=modify.question_taken_date
            next_rep_date=modify.date_of_next_rep
            wrong_answer=modify.wrong_answer_date
            if new_questions == 0:
                new_question=peronalized_max_questions.total_new_question
                new_questi=peronalized_max_questions.question_attemp
                context["new_question"] = new_question
                if new_questi == 0:
                    new_questi=new_questi+1
                    peronalized_max_questions.question_attemp=new_questi
                    peronalized_max_questions.save()
                else:
                    new_questi=new_questi
                context["new_questi"] = new_questi
                
                if new_question == "1":
                    context["question_info"] = "New Question"
                else:
                    context["question_info"] = "New Questions"
            
            else:
                fmt = "%Y-%m-%d"
                fmt1 = "%Y-%m-%d %H:%M:%S"
                now = datetime.datetime.now() 
                date=now.strftime(fmt)
                now1 = datetime.datetime.now() 
                date1=now1.strftime(fmt1)
                date1=datetime.datetime.strptime(date1, "%Y-%m-%d %H:%M:%S")
                rep=second_attempt_day[0:10]
                timesss=next_rep_date[0:19]
                wrong_answers=wrong_answer[0:19]
                timesss=datetime.datetime.strptime(timesss, "%Y-%m-%d %H:%M:%S")
                wrong_answers=datetime.datetime.strptime(wrong_answers, "%Y-%m-%d %H:%M:%S")
                question_att_date=rep
                
                #if timesss < date1:
                #    if modify.correct_answer == 0:
                if new_questions > 0:
                        #if modify.today_wrong_answer == 1:
                        # if wrong_answers == timesss:
                        #     if modify.today_wrong_answer == 1:
                        #         #corection=peronalized_max_questions.correction
                                #peronalized_max_questions.question_repe=0
                                #peronalized_max_questions.total_repeat=corection
                                #peronalized_max_questions.rember_questions=0
                               
                                #peronalized_max_questions.save()

                        if timesss < date1:
                            if peronalized_max_questions.tempory_questions == 1 :
                                peronalized_max_questions.question_repe=0
                                corection=peronalized_max_questions.correction
                                peronalized_max_questions.tempory_questions=corection
                                peronalized_max_questions.save()

                        if wrong_answers == timesss:
                            if timesss >= date1:
                                peronalized_max_questions.tempory_questions=1
                                peronalized_max_questions.save()
                                corection=peronalized_max_questions.correction
                                context["corection"] = corection
                                if corection == 1:
                                    context["question_info"] = "Correction"
                                    context["question_info1"] = "Question"
                                else:
                                    context["question_info"] = "Corrections"
                                    context["question_info1"] = "Questions"
               
                            else:
                                new_questi=peronalized_max_questions.question_repe+1
                                context["new_questi"] = new_questi 
                                corection=peronalized_max_questions.tempory_questions
                                context["new_question"] = corection
                                if corection == "1":
                                    context["question_info"] = "Repetation"
                                else: 
                                    context["question_info"] = "Repetations"
                        else:
                 
                            new_questi=peronalized_max_questions.question_repe+1
                            context["new_questi"] = new_questi
                            repeat_question=peronalized_max_questions.total_repeat
                            context["new_question"] = repeat_question
                            if repeat_question == "1":
                                context["question_info"] = "21Repetation"
                            else: 
                                context["question_info"] = "21Repetations"
        else:
            new_question=peronalized_max_questions.total_new_question
            new_questi=peronalized_max_questions.question_attemp
            context["new_question"] = new_question
            context["new_questi"] = new_questi
            if new_question == "1":
                context["question_info"] = "New Question"
            else:
                context["question_info"] = "New Questions"              

        context["remove_question"] = 0
        #context["undo_question"] =0
        
        if "question_undo" in self.request.POST:
            undo=self.request.POST['question_undo']
            if undo == "1":
                modify.correct_answer=modify.correct_answer-10
                modify.date_of_next_rep=datetime.date.today() 
                modify.save()
                context['question'] = self.question
                context['quiz'] = self.quiz
                if hasattr(self, 'previous'):
                    context['previous'] = self.previous
                if hasattr(self, 'progress'):
                    context['progress'] = self.progress
                if peronalized_max_questions.rember == "1":
                    context["rember_que"] = 1
                else:
                    context["remove_question"] = 1
                if self.request.POST :
                    value=self.request.POST['question_undo']
                    if value != 0:
                        context["to_display_question"] = 1
                    elif self.previous:
                        context["to_display_question"] = 0
                    else:
                        context["to_display_question"] = 0
                return context 



        mode=Quiz.objects.get(title=self.quiz)
        mode=mode.exam_mode
        if mode == False:
            forget_forever=modify.correct_answer
            if forget_forever >=2:
                context["remove_question"] = 1

        if peronalized_max_questions.rember == "1":
            context["remove_question"] = 0
            if forget_forever >=2:
                context["rember_que"] = 1
            if peronalized_max_questions.rember == "1":
                if "check" in self.request.POST:
                    checke=self.request.POST['check']
                    if str(checke) == "1":
                        modify.correct_answer=modify.correct_answer+10
                        modify.date_of_next_rep=datetime.date.today() + datetime.timedelta(days=1025)
                        modify.save()
                        context["undo_question"] = 1
                        context["rember_que"] = 0
                        context['question'] = self.question
                        context['quiz'] = self.quiz
                        if hasattr(self, 'previous'):
                            context['previous'] = self.previous
                        if hasattr(self, 'progress'):
                            context['progress'] = self.progress
                        if 'check' in self.request.POST:
                                value=self.request.POST['check']
                                if value != 0:
                                    context["to_display_question"] = 1
                                elif self.previous:
                                    context["to_display_question"] = 0
                                else:
                                    context["to_display_question"] = 0
                        return context
    


        if peronalized_max_questions.rember == "0":
            if "checked" in self.request.POST:
                unchecked=self.request.POST['checked']
                
                if unchecked == "1":
                    modify.correct_answer=modify.correct_answer+10
                    modify.date_of_next_rep=datetime.date.today() + datetime.timedelta(days=1025)
                    modify.save()
                    context["undo_question"] = 1
                    context["remove_question"] = 0
                    
                    context['question'] = self.question
                    context['quiz'] = self.quiz
                    if hasattr(self, 'previous'):
                        context['previous'] = self.previous
                    if hasattr(self, 'progress'):
                        context['progress'] = self.progress
                    if self.request.POST :
                        value=self.request.POST['checked']
                        if value != 0:
                            context["to_display_question"] = 1
                        elif self.previous:
                            context["to_display_question"] = 0
                        else:
                            context["to_display_question"] = 0

                    if "Rember" in self.request.POST:
                        rember = self.request.POST['Rember']
                        peronalized_max_questions.rember=rember
                        context["undo_question"] = 1
                        # context["remove_question"] = 0
                        peronalized_max_questions.save()
                    return context 

        context['question'] = self.question
        context['quiz'] = self.quiz
        
    
        if hasattr(self, 'previous'):
            questions=PersonalizedQuiz.objects.get(quiz=self.quiz, user=self.request.user)
            questions.question_repe=questions.question_repe+1
            questions.save()
            context['previous'] = self.previous
            
            #return render(se0lf.request, self.previous_template_name, context=context['previous'])
        
        if hasattr(self, 'progress'):
            context['progress'] = self.progress
            if "hidde_questions" in self.request.POST:
            # if self.request.POST :
                value=self.request.POST['hidde_questions']
                if value != 1:
                    context["to_display_question"] = 0
                elif self.previous:
                    context["to_display_question"] = 1
                else:
                    context["to_display_question"] = 1
        return context

   



    def form_valid_user(self, form):
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        guess = form.cleaned_data['answers']
        is_correct = self.question.check_if_correct(guess)

        




        if is_correct is True:
            self.sitting.add_to_score(1)
            progress.update_score(self.question, 1, 1)
        else:
            self.sitting.add_incorrect_question(self.question)
            progress.update_score(self.question, 0, 1)

        if self.quiz.answers_at_end is not True:

            self.previous = {'previous_answer': guess,
                             'previous_outcome': is_correct,
                             'previous_question': self.question,
                             'answers': self.question.get_answers(),
                             'question_type': {self.question
                                               .__class__.__name__: True}}
            
        else:
            self.previous = {}

        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()
 
    
    def final_result_user(self):
        mode=Quiz.objects.get(title=self.quiz) 
        mode=mode.exam_mode
        results = {
            'quiz': self.quiz,
            'score': self.sitting.get_current_score,
            'max_score': self.sitting.get_max_score,
            'percent': self.sitting.get_percent_correct,
            'sitting': self.sitting,
            'previous': self.previous,
        }

        self.sitting.mark_quiz_complete()

        if self.quiz.answers_at_end:
            results['questions'] =\
                self.sitting.get_questions(with_answers=True)
            results['incorrect_questions'] =\
                self.sitting.get_incorrect_questions

        if self.quiz.exam_paper is False:
            self.sitting.delete()
        if mode == True:
            
            subject = 'Thank you for registering to our site'
            #context= results
            context = "You answered "+" "+ str(self.sitting.get_current_score) +" "+"questions correctly out of"+" "+str(self.sitting.get_max_score)+" "+"giving you"+" "+str(self.sitting.get_percent_correct)+" "+"percent correct"
            print("context",context)
            context=str(context)
            message =  context 
            email_from = settings.EMAIL_HOST_USER
            recipient_list = ['prashantnajan8965@gmail.com',]
            
            tz=User
            tz1=tz.email
            print("email_id",tz1)
            
            send_mail( subject, message, email_from, recipient_list )
            print("results",results)
            return render(self.request, self.result_template_name, results)
        else:
            progress_report=progress_reports(self.request)
            context={'progress_report':progress_report}
            return render(self.request, self.templates_name,context)
            

    def anon_load_sitting(self):
        if self.quiz.single_attempt is True:
            return False

        if self.quiz.anon_q_list() in self.request.session:
            return self.request.session[self.quiz.anon_q_list()]
        else:
            return self.new_anon_quiz_session()

    def new_anon_quiz_session(self):
        """
        Sets the session variables when starting a quiz for the first time
        as a non signed-in user
        """
        self.request.session.set_expiry(259200)  # expires after 3 days
        questions = self.quiz.get_questions()
        question_list = [question.id for question in questions]

        if self.quiz.random_order is True:
            random.shuffle(question_list)


        if self.quiz.max_questions and (self.quiz.max_questions
                                        < len(question_list)):
            peronalized_max_questions = PersonalizedQuiz.objects.get(quiz=self.quiz, user=request.user).max_questions
            question_list = question_list[:peronalized_max_questions]

        # session score for anon users
        self.request.session[self.quiz.anon_score_id()] = 0

        # session list of questions
        self.request.session[self.quiz.anon_q_list()] = question_list

        # session list of question order and incorrect questions
        self.request.session[self.quiz.anon_q_data()] = dict(
            incorrect_questions=[],
            order=question_list,
        )

        return self.request.session[self.quiz.anon_q_list()]

    
    

    def anon_next_question(self):
        next_question_id = self.request.session[self.quiz.anon_q_list()][0]
        return Question.objects.get_subclass(id=next_question_id)

    def anon_sitting_progress(self):
        total = len(self.request.session[self.quiz.anon_q_data()]['order'])
        answered = total - len(self.request.session[self.quiz.anon_q_list()])
        return (answered, total)

    def form_valid_anon(self, form):
        guess = form.cleaned_data['answers']
        is_correct = self.question.check_if_correct(guess)

        if is_correct:
            self.request.session[self.quiz.anon_score_id()] += 1
            anon_session_score(self.request.session, 1, 1)
        else:
            anon_session_score(self.request.session, 0, 1)
            self.request\
                .session[self.quiz.anon_q_data()]['incorrect_questions']\
                .append(self.question.id)

        self.previous = {}
        if self.quiz.answers_at_end is not True:
            self.previous = {'previous_answer': guess,
                             'previous_outcome': is_correct,
                             'previous_question': self.question,
                             'answers': self.question.get_answers(),
                             'question_type': {self.question
                                               .__class__.__name__: True}}

        self.request.session[self.quiz.anon_q_list()] =\
            self.request.session[self.quiz.anon_q_list()][1:]

    def final_result_anon(self):
        score = self.request.session[self.quiz.anon_score_id()]
        q_order = self.request.session[self.quiz.anon_q_data()]['order']
        max_score = len(q_order)
        percent = int(round((float(score) / max_score) * 100))
        session, session_possible = anon_session_score(self.request.session)
        if score is 0:
            score = "0"

        results = {
            'score': score,
            'max_score': max_score,
            'percent': percent,
            'session': session,
            'possible': session_possible
        }

        del self.request.session[self.quiz.anon_q_list()]

        if self.quiz.answers_at_end:
            results['questions'] = sorted(
                self.quiz.question_set.filter(id__in=q_order)
                                      .select_subclasses(),
                key=lambda q: q_order.index(q.id))

            results['incorrect_questions'] = (
                self.request
                    .session[self.quiz.anon_q_data()]['incorrect_questions'])

        else:
            results['previous'] = self.previous

        del self.request.session[self.quiz.anon_q_data()]

        return render(self.request, 'result.html', results)

def anon_session_score(session, to_add=0, possible=0):
    """
    Returns the session score for non-signed in users.
    If number passed in then add this to the running total and
    return session score.

    examples:
        anon_session_score(1, 1) will add 1 out of a possible 1
        anon_session_score(0, 2) will add 0 out of a possible 2
        x, y = anon_session_score() will return the session score
                                    without modification

    Left this as an individual function for unit testing
    """
    if "session_score" not in session:
        session["session_score"], session["session_score_possible"] = 0, 0

    if possible > 0:
        session["session_score"] += to_add
        session["session_score_possible"] += possible 

    return session["session_score"], session["session_score_possible"]


class quiz1(DetailView):
    model = Quiz
    slug_field = 'url'

    def post(self, request, *args, **kwargs):
            form = PersonalizedQuizForm(request.POST)
            quiz=Quiz.objects.get(url=self.kwargs['slug'])
            pq=PersonalizedQuiz.objects.get(quiz=quiz, user=request.user)
            max_questions=request.POST['question']
            pq.max_questions=max_questions
            pq.save()
            return render(request, 'quiz/quiz_question.html', {'quiz':quiz,'max_questions':max_questions})

    def get(self, request, *args, **kwargs):
        quiz=Quiz.objects.get(url=self.kwargs['slug'])
        pq=PersonalizedQuiz.objects.get(quiz=quiz, user=request.user)
        max_questions=pq.max_questions
        return render(request, 'quiz/quiz_question.html', {'quiz':quiz,'max_questions':max_questions})        

global repeat_question
class quizrep(TemplateView):
    model = Quiz
    slug_field = 'url'
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = PersonalizedQuizForm(request.POST)
            quiz=Quiz.objects.get(url=self.kwargs['slug'])
            pq=PersonalizedQuiz.objects.get(quiz=quiz, user=request.user)
            repeat_questions=request.POST['repeat_questions']
            pq.repeat_questions=repeat_questions
            pq.save()
        if pq.repeat_questions == "25":
            repeat_questions="Low"
        if pq.repeat_questions == "50":
            repeat_questions="Medium"
        if pq.repeat_questions == "75":
            repeat_questions="High"
        return render(request, 'quiz/quiz_repeat_questions.html', {'quiz':quiz,'repeat_questions':repeat_questions}) 

    def get(self, request, *args, **kwargs):
        quiz=Quiz.objects.get(url=self.kwargs['slug'])
        pq=PersonalizedQuiz.objects.get(quiz=quiz, user=request.user)
        repeat_questions=pq.repeat_questions
        if pq.repeat_questions == "25":
            repeat_questions="Low"
        if pq.repeat_questions == "50":
            repeat_questions="Medium"
        if pq.repeat_questions == "75":
            repeat_questions="High"
        return render(request, 'quiz/quiz_repeat_questions.html', {'quiz':quiz,'repeat_questions':repeat_questions}) 


