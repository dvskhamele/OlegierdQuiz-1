from __future__ import unicode_literals
import re
import json
import random
from datetime import timedelta 
from django.db import models
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import (
    MaxValueValidator, validate_comma_separated_integer_list,
)
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings
from django.contrib.auth.models import AbstractUser
import pytz 

from timezone_field import TimeZoneField

from model_utils.managers import InheritanceManager 
 
import random 
import datetime

from django.template.defaultfilters import slugify

class CategoryManager(models.Manager):

    def new_category(self, category):
        new_category = self.create(category=re.sub('\s+', '-', category)
                                   .lower())

        new_category.save() 
        return new_category

# class TimeZone(models.Model):
#     timezone = models.CharField(
    
#         max_length=250, blank=True, null=True)
#     def __str__(self):
#         return self.timezone

class User(AbstractUser):
    timezone1 = TimeZoneField(default='Europe/London')
    # timezone1 = models.ForeignKey(
    #     TimeZone, null=True, blank=True, on_delete=models.CASCADE,default=1)

    def __str__(self):
        return self.username



@python_2_unicode_compatible
class Category(models.Model):

    category = models.CharField(
        verbose_name=_("Category"),
        max_length=250, blank=True,
        unique=True, null=True)

    # objects = CategoryManager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.category

    def save(self, *args, **kwargs):
        self.category = str.capitalize(self.category)
        super(Category, self).save(*args, **kwargs)


@python_2_unicode_compatible
class SubCategory(models.Model):
 
    sub_category = models.CharField(
        verbose_name=_("Sub-Category"),
        max_length=250, blank=True, null=True)

    category = models.ForeignKey(
        Category, null=True, blank=True,
        verbose_name=_("Category"), on_delete=models.CASCADE)

    objects = CategoryManager()

    class Meta:
        verbose_name = _("Sub-Category") 
        verbose_name_plural = _("Sub-Categories")

    def __str__(self):
        return self.sub_category + " (" + self.category.category + ")"
    

@python_2_unicode_compatible
class Quiz(models.Model):

    title = models.CharField( 
        verbose_name=_("Title"),
        max_length=60, blank=False)

    description = models.TextField(
        verbose_name=_("Description"),
        blank=True, help_text=_("a description of the quiz"))

    url = models.SlugField(
        max_length=60, blank=False,
        help_text=_("a user friendly url"),
        verbose_name=_("user friendly url"))

    category = models.ForeignKey(
        Category, null=True, blank=True,
        verbose_name=_("Category"), on_delete=models.CASCADE)
    
    random_order = models.BooleanField(
        blank=False, default=False,
        verbose_name=_("Random Order"), 
        help_text=_("Display the questions in "
                    "a random order or as they "
                    "are set?"))

    max_questions = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("Max Questions"),
        help_text=_("Number of questions to be answered on each attempt."))

    answers_at_end = models.BooleanField(
        blank=False, default=False,
        help_text=_("Correct answer is NOT shown after question."
                    " Answers displayed at the end."),
        verbose_name=_("Answers at end"))

    exam_mode = models.BooleanField(
        blank=False, default=False,
        help_text=_("Exam result show."
                    "Progress Report show."),
        verbose_name=_("Exam mode"))

    e_learning = models.BooleanField(
        blank=False, default=False,
        help_text=_("E Learning ."),
        verbose_name=_("e_learning"))

    single_attempt = models.BooleanField(
        blank=False, default=False,
        help_text=_("If yes, only one attempt by"
                    " a user will be permitted."
                    " Non users cannot sit this exam."),
        verbose_name=_("Single Attempt"))

    pass_mark = models.SmallIntegerField(
        blank=True, default=0,
        verbose_name=_("Pass Mark"),
        help_text=_("Percentage required to pass exam."),
        validators=[MaxValueValidator(100)])

    success_text = models.TextField(
        blank=True, help_text=_("Displayed if user passes."),
        verbose_name=_("Success Text"))

    fail_text = models.TextField(
        verbose_name=_("Fail Text"),
        blank=True, help_text=_("Displayed if user fails."))

    draft = models.BooleanField(
        blank=True, default=False,
        verbose_name=_("Draft"),
        help_text=_("If yes, the quiz is not displayed"
                    " in the quiz list and can only be"
                    " taken by users who can edit"
                    " quizzes."))

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.url == "" :
            self.url = slugify(self.title)
        self.url = re.sub('\s+', '-', self.url).lower()

        self.url = ''.join(letter for letter in self.url if
                           letter.isalnum() or letter == '-')

        if self.single_attempt is True:
            self.exam_paper = True

        if self.pass_mark > 100:
            raise ValidationError('%s is above 100' % self.pass_mark)

        super(Quiz, self).save(force_insert, force_update, *args, **kwargs)

    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.question_set.all().select_subclasses()

    @property
    def get_max_score(self):
        return self.get_questions().count()

    def anon_score_id(self):
        return str(self.id) + "_score"

    def anon_q_list(self):
        return str(self.id) + "_q_list"

    def anon_q_data(self):
        return str(self.id) + "_data"


class ProgressManager(models.Manager):

    def new_progress(self, user):
        new_progress = self.create(user=user,
                                   score="")
        new_progress.save()
        return new_progress


class Image(models.Model):
    image = models.ImageField(upload_to='user_images')


class PersonalizedQuiz(models.Model):
    user = models.ForeignKey(User, related_name="personalized_user", verbose_name=_("User"), on_delete=models.CASCADE ,blank=True,null=True)
    quiz = models.ForeignKey(Quiz, related_name="personalized_quizes",verbose_name=_("Quiz"), on_delete=models.CASCADE,blank=True,null=True )
    max_questions = models.CharField(max_length=1024,verbose_name=_("max_questionss"),blank=True,null=True)
    repeat_questions = models.CharField(max_length=1024,verbose_name=_("repeat_questions"),blank=True,null=True)
    previous_question_list = models.CharField(max_length=1024,verbose_name=_("Previous Question List"),
        blank=True,null=True)
    rember = models.CharField(max_length=24,default=0,verbose_name=_("rember"),blank=True,null=True)
    total_new_question = models.CharField(max_length=24,default=0,verbose_name=_("total_new_question"),blank=True,null=True)
    total_repeat = models.CharField(max_length=24,default=0,verbose_name=_("total_repeat"),blank=True,null=True)
    question_attemp = models.IntegerField(default=0,verbose_name=_("question_attemp"),blank=True,null=True)
    question_repe = models.IntegerField(default=0,verbose_name=_("question_repe"),blank=True,null=True)
    correction = models.IntegerField(default=0,verbose_name=_("correction"),blank=True,null=True)
    rember_questions = models.IntegerField(default=0,verbose_name=_("rember_questions"),blank=True,null=True)
    tempory_questions= models.IntegerField(default=0,verbose_name=_("tempory_questions"),blank=True,null=True)
    session_time = models.CharField(max_length=1024,verbose_name=_("session_time"),blank=True,null=True)
    timers = models.IntegerField(default=90,verbose_name=_("timers"),blank=True,null=True)
    session = models.IntegerField(default=0,verbose_name=_("session"),blank=True,null=True)


class Progress(models.Model):
    """
    Progress is used to track an individual signed in users score on different
    quiz's and categories

    Data stored in csv using the format:
        category, score, possible, category, score, possible, ...
    """
    user = models.OneToOneField(User, verbose_name=_("User"), on_delete=models.CASCADE)

    score = models.CharField(max_length=1024,
                             verbose_name=_("Score"),
                             validators=[validate_comma_separated_integer_list])

    objects = ProgressManager()

    class Meta:
        verbose_name = _("User Progress")
        verbose_name_plural = _("User progress records")

    @property
    def list_all_cat_scores(self):
        """
        Returns a dict in which the key is the category name and the item is
        a list of three integers.

        The first is the number of questions correct,
        the second is the possible best score,
        the third is the percentage correct.

        The dict will have one key for every category that you have defined
        """
        score_before = self.score
        output = {}

        for cat in Category.objects.all():
            to_find = re.escape(cat.category) + r",(\d+),(\d+),"
            #  group 1 is score, group 2 is highest possible

            match = re.search(to_find, self.score, re.IGNORECASE)

            if match:
                score = int(match.group(1))
                possible = int(match.group(2))

                try:
                    percent = int(round((float(score) / float(possible))
                                        * 100))
                except:
                    percent = 0

                output[cat.category] = [score, possible, percent]

            else:  # if category has not been added yet, add it.
                self.score += cat.category + ",0,0,"
                output[cat.category] = [0, 0]

        if len(self.score) > len(score_before):
            # If a new category has been added, save changes.
            self.save()

        return output

    def update_score(self, question, score_to_add=0, possible_to_add=0):
        """
        Pass in question object, amount to increase score
        and max possible.

        Does not return anything.
        """
        category_test = Category.objects.filter(category=question.category)\
                                        .exists()

        if any([item is False for item in [category_test,
                                           score_to_add,
                                           possible_to_add,
                                           isinstance(score_to_add, int),
                                           isinstance(possible_to_add, int)]]):
            return _("error"), _("category does not exist or invalid score")

        to_find = re.escape(str(question.category)) +\
            r",(?P<score>\d+),(?P<possible>\d+),"

        match = re.search(to_find, self.score, re.IGNORECASE)

        if match:
            updated_score = int(match.group('score')) + abs(score_to_add)
            updated_possible = int(match.group('possible')) +\
                abs(possible_to_add)

            new_score = ",".join(
                [
                    str(question.category),
                    str(updated_score),
                    str(updated_possible), ""
                ])

            # swap old score for the new one
            self.score = self.score.replace(match.group(), new_score)
            self.save()

        else:
            #  if not present but existing, add with the points passed in
            self.score += ",".join(
                [
                    str(question.category),
                    str(score_to_add),
                    str(possible_to_add),
                    ""
                ])
            self.save()

    def show_exams(self):
        """
        Finds the previous quizzes marked as 'exam papers'.
        Returns a queryset of complete exams.
        """
        return Sitting.objects.filter(user=self.user, complete=True)



class UQuestion(models.Model):
    user = models.ForeignKey(User, related_name="user_questions", verbose_name=_("User"), on_delete=models.CASCADE ,blank=True,null=True)
    quiz = models.ForeignKey(Quiz, related_name="user_questions",verbose_name=_("Quiz1"), on_delete=models.CASCADE,blank=True,null=True )
    questions = models.ForeignKey('Question', related_name="user_questions",verbose_name=_("Questio"), on_delete=models.CASCADE,blank=True,null=True )
    attempt_question = models.IntegerField(verbose_name=_("attemp_questions"),blank=True,null=True)
    correct_answer = models.IntegerField(verbose_name=_("correct_answer"),
        blank=True,null=True)
    wrong_answer_date = models.CharField(max_length=1024,verbose_name=_("wrong_answer_date"),
        blank=True,null=True)
    date_of_next_rep = models.CharField(max_length=1024,verbose_name=_("date time fields"),
        blank=True,null=True)
    question_taken_date = models.CharField(max_length=1024,verbose_name=_("attemp question time"),blank=True,null=True)
    today_wrong_answer = models.IntegerField(verbose_name=_("today_wrong_answer"),
        blank=True,null=True)
    class Meta:
        verbose_name = _("User Question")
        verbose_name_plural = _("User question records")

class SittingManager(models.Manager):

    def new_sitting(self, user, quiz):

        pq = PersonalizedQuiz.objects.get(quiz=quiz, user=user)
        request_user=user
        peronalized_max_questions = int(pq.max_questions)
        repeated_questions = int(pq.repeat_questions)
        numbers_to_repeat = round(repeated_questions * peronalized_max_questions / 100 + 0.1) 

        previous_question_list = pq.previous_question_list

        if previous_question_list == None:
            previous_question_list = str(["0"])

        previous_question_list = previous_question_list.replace('[',"").replace("'","").replace(']',"").split(', ')

        if len(previous_question_list) > numbers_to_repeat:
            random_previous_questions = random.sample(previous_question_list, 
            k=numbers_to_repeat)
        else:
            random_previous_questions = previous_question_list
        questions_to_exclude = list(set(previous_question_list) - set(random_previous_questions))
        if quiz.random_order is True:
            question_set = quiz.question_set.exclude(id__in=questions_to_exclude) \
                                            .select_subclasses() \
                                            .order_by('?')
        else:
            question_set = quiz.question_set.exclude(id__in=questions_to_exclude) \
                                            .select_subclasses()

        question_set = [item.id for item in question_set]
        repeat_question=pq.repeat_questions
        max_question = pq.max_questions
        pq.rember=0
        mode=quiz.exam_mode
        if mode == False:
            pq.question_attemp=0
        else:
            pq.question_attemp=1
        pq.question_repe=0
        pq.rember_questions=1
        pq.save()
        max_question=int(max_question)

        random_order=quiz.random_order
        
        que_attemps=[]
        question_repeate=[]
        check_question=[]

        for q in UQuestion.objects.filter(quiz=quiz, user=user):
            question_id = q.questions.id
            question_correct = q.correct_answer
            question_rep_date = q.date_of_next_rep
            fmt = "%Y-%m-%d %H:%M:%S"
            now = datetime.datetime.now()  
            date=now.strftime(fmt)
            if question_rep_date == None:
                question_rep_date = date
            if question_correct == 0 and q.attempt_question >= 1:
                que_attemps.append(question_id)
            if question_correct > 0 and question_correct < 5:
                check_question.append(question_id)
                if question_rep_date <= date:
                    if not question_id in  question_repeate:
                        question_repeate.append(question_id)

        session_slides=[]
        session_slides_f=[]
        session_value=pq.session
        if quiz.e_learning == True and quiz.exam_mode == False:
            for i in Question.objects.filter(quiz=quiz,session_slide=session_value,is_slide=True):
                session_slides.append(i.id)
            for j in Question.objects.filter(quiz=quiz,is_slide=False):
                session_slides_f.append(j.id)
            session_slides_f=session_slides_f[0:max_question]

            fmt2 = "%z"
            tz = user
            tz1=tz.timezone1
            
            tz2 = pytz.timezone(str(tz1))
            user_time = datetime.datetime.now(tz2)
            user=user_time.strftime(fmt2)
            user_hour1=user[1]
            user_hour2=user[2]
            if user_hour1 != "0":
                hours=user[1:3]
            else:
                hours=user[2]
            user_time=user[3:5]
            minute=user[3]
            if minute != "0":
                minutes=user[3:5]
            else:
                minutes=user[4]
            value=user[0:1]
            value=str(value)
            fmt = "%Y-%m-%d %H:%M:%S"
            if value == "-":
                time=timedelta(hours=int(hours),minutes=int(minutes))
                time=time+timedelta(minutes=10)
                datess=datetime.date.today() 
                datess=str(datess)
                time=str(time)
                user_date=datess+" "+time 
                user_date_time=datetime.datetime.strptime(user_date , fmt)      
                pq.session_time=user_date_time
                pq.save()

            if value == "+":
                time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                time=time+timedelta(minutes=10)
                datess=datetime.date.today() 
                datess=str(datess)
                time=str(time)
                user_date=datess+" "+time 
                user_date_time=datetime.datetime.strptime(user_date , fmt)
                pq.session_time=user_date_time
                pq.save()

            if value == " ":
                now = datetime.datetime.now()
                date_time1=now.strftime(fmt)
                user_date_time=datetime.datetime.strptime(date_time1, fmt)
                pq.session_time=user_date_time
                pq.save()

            if random_order == True:
                random.shuffle(session_slides_f)


            if len(session_slides) > 0: #repeat_question:
                print("session_slides",session_slides)
                print("session_slides_f",session_slides_f)
                E_question_set=session_slides+session_slides_f
                print("repeat E_question_set",E_question_set)
                question_set = E_question_set
            else:
                E_question_set=session_slides_f
                print("not repeat E_question_set",E_question_set)               
                question_set = E_question_set
                        
        else:
            new_questionss=max_question
            tempory_questions_set=question_set
            if random_order == True:
                random.shuffle(tempory_questions_set)
                question_setss=tempory_questions_set[0:new_questionss]
            else:
                pq.tempory_questions=pq.tempory_questions+max_question
                pq.save()
                temp_questions=pq.tempory_questions
                tempory_question=pq.tempory_questions-max_question
                if len(tempory_questions_set) <= temp_questions:
                    pq.tempory_questions=max_question
                    pq.save()
                    question_setss=tempory_questions_set[0:max_question]
                else:
                    question_setss=tempory_questions_set[tempory_question:temp_questions]
                    

            if modes == False and modess == False:
                question_set=(list(set(question_set) - set(check_question)))
                new_questions=max_question
                question_sets=question_set[0:new_questions]
                question_repeat=len(question_repeate)          
                fmt2 = "%z"

                tz1=user.timezone1
                tz2 = pytz.timezone(str(tz1))

                user_time = datetime.datetime.now(tz2)
                user_strf=user_time.strftime(fmt2)
                if user_strf[1] != "0":
                    hours=user_strf[1:3]
                else:
                    hours=user_strf[2]
                if user_strf[3] != "0":
                    minutes=user_strf[3:5]
                else:
                    minutes=user_strf[4]
                value=str(user_strf[0:1])
                fmt = "%Y-%m-%d %H:%M:%S"

                if value == "-":
                    time=timedelta(hours=int(hours),minutes=int(minutes))+timedelta(minutes=10)
                    pq.session_time=datetime.datetime.strptime(str(datetime.date.today())+" "+str(time), fmt)
                    pq.save()

                elif value == "+":
                    time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))+timedelta(minutes=10)
                    pq.session_time=datetime.datetime.strptime(str(datetime.date.today())+" "+str(time)  , fmt)
                    pq.save()

                elif value == " ":
                    now = datetime.datetime.now()
                    pq.session_time=datetime.datetime.strptime(now.strftime(fmt), fmt)
                    pq.save()
                
                if random_order == True:
                    random.shuffle(question_sets)

                if len(que_attemps) > 0:
                    pq.total_new_question=new_questions
                    pq.tempory_questions=len(que_attemps)
                    pq.save()
                    new_questions=new_questions+1
                    question_sets=question_set[1:new_questions]
                    question_set=que_attemps+question_sets
                    question_set=(list(set(question_set))) #- set(que_attemps)))        

                elif len(question_set) < new_questions:
                    remaing_questions=question_set
                    pq.total_new_question=len(remaing_questions)
                    pq.total_repeat=question_repeat
                    pq.save()
                    question_set=question_repeate+question_sets

                elif len(question_repeate) > 0: 
                        
                    pq.total_new_question=new_questions
                    pq.total_repeat=question_repeat
                    pq.save()
                    question_set=question_repeate+question_sets

                else:
                    
                    pq.total_new_question=max_question
                    pq.save()
                    question_set=question_sets
                                        
            else:
                pq.total_new_question=max_question
                pq.save()   
                question_set=question_setss


        mode=Quiz.objects.get(title=quiz)
        if mode.e_learning == True and mode.exam_mode == False:
            session_count=pq.session
            pq.session=session_count+1
            pq.save()

                
        if len(question_set) == 0:
            raise ImpropervlyConfigured('Question set of the quiz is empty. '
                                       'Please configure questions properly')



        if peronalized_max_questions < len(question_set):
            question_set = question_set
        questions = ",".join(map(str, question_set)) + ","
        new_sitting = self.create(user=request_user,
                                  quiz=quiz,
                                  question_order=questions,
                                  question_list=questions,
                                  incorrect_questions="",
                                  current_score=0,
                                  complete=False,
                                  user_answers='{}')
        return new_sitting

    
            

    def user_sitting(self, user, quiz):
        if quiz.single_attempt is True and self.filter(user=user,
                                                       quiz=quiz,
                                                       complete=True)\
                                               .exists():
            return False

        try:
            sitting = self.get(user=user, quiz=quiz, complete=False)
            if Question.objects.count() == 0:
                sitting.delete()
                sitting = self.new_sitting(user, quiz)
        except Sitting.DoesNotExist:
            sitting = self.new_sitting(user, quiz)
        except Sitting.MultipleObjectsReturned:
            sitting = self.filter(user=user, quiz=quiz, complete=False)[0]
        return sitting


class Sitting(models.Model):
    """
    Used to store the progress of logged in users sitting a quiz.
    Replaces the session system used by anon users.

    Question_order is a list of integer pks of all the questions in the
    quiz, in order.

    Question_list is a list of integers which represent id's of
    the unanswered questions in csv format.

    Incorrect_questions is a list in the same format.

    Sitting deleted when quiz finished unless quiz.exam_paper is true.

    User_answers is a json object in which the question PK is stored
    with the answer the user gave.
    """

    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)

    quiz = models.ForeignKey(Quiz, verbose_name=_("Quiz"), on_delete=models.CASCADE)

    question_order = models.CharField(
        max_length=1024,
        verbose_name=_("Question Order"),
        validators=[validate_comma_separated_integer_list])

    question_list = models.CharField(
        max_length=1024,
        verbose_name=_("Question List"),
        validators=[validate_comma_separated_integer_list])
    incorrect_questions = models.CharField(
        max_length=1024,
        blank=True,
        verbose_name=_("Incorrect questions"),
        validators=[validate_comma_separated_integer_list])

    current_score = models.IntegerField(verbose_name=_("Current Score"))

    complete = models.BooleanField(default=False, blank=False,
                                   verbose_name=_("Complete"))

    user_answers = models.TextField(blank=True, default='{}',
                                    verbose_name=_("User Answers"))

    start = models.DateTimeField(auto_now_add=True,
                                 verbose_name=_("Start"))

    end = models.DateTimeField(null=True, blank=True, verbose_name=_("End"))

    objects = SittingManager()

    class Meta:
        permissions = (("view_sittings", _("Can see completed exams.")),)


    def get_first_question(self):
        """
        Returns the next question.
        If no question is found, returns False
        Does NOT remove the question from the front of the list.
        """
        if not self.question_list:
            return False
        quiz = self.quiz
        try:
            pre_q=PersonalizedQuiz.objects.get(quiz=quiz, user=self.user)
        except PersonalizedQuiz.DoesNotExist:
            pre_q=PersonalizedQuiz.objects.create(quiz=quiz, user=self.user)
        
        if mode.e_learning == True and mode.exam_mode == False:# and is_slides == True:
            self.save()


        if mode.exam_mode == False:
            times=pre_q.session_time
            times=datetime.datetime.strptime(times, "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            date_times=now.strftime("%Y-%m-%d %H:%M:%S")
            date_times=datetime.datetime.strptime(date_times, "%Y-%m-%d %H:%M:%S")
            if date_times >= times:
                self.complete = True
                self.end = datetime.datetime.now()
                self.save()
        first, _ = self.question_list.split(',', 1)
        question_id = int(first)
        questions = Question.objects.filter(quiz=quiz)
        questions_count = questions.count()
        user_questions=UQuestion.objects.filter(quiz=quiz, user=self.user)
        user_questions_count = user_questions.count()

        q = Question.objects.get(id=question_id)
        try:
                uq=UQuestion.objects.get(quiz=quiz, user=self.user,questions=q)
        except UQuestion.DoesNotExist:
                
                mode=Quiz.objects.get(title=quiz)
                mode=mode.exam_mode
                if mode == False:
                    fmt = "%Y-%m-%d %H:%M:%S"
                    now = datetime.datetime.now()
                    date_time=now.strftime(fmt)
                    yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                    uq=UQuestion.objects.create(quiz=self.quiz, user=self.user,questions=q,
                        attempt_question=0,correct_answer=0,date_of_next_rep=date_time,question_taken_date=date_time,
                        wrong_answer_date=yesterday,today_wrong_answer=0)
                    pre_qu=PersonalizedQuiz.objects.get(quiz=self.quiz, user=self.user)
                    pre_qu.question_attemp=pre_qu.question_attemp+1
                    pre_qu.save()
                                                            
        return Question.objects.get_subclass(id=question_id)

        

    def remove_first_question(self):
        if not self.question_list:    
            print("not self question list")
            return
        try:
            pre_q=PersonalizedQuiz.objects.get(quiz=self.quiz, user=self.user)
        except PersonalizedQuiz.DoesNotExist:
            pre_q=PersonalizedQuiz.objects.create(quiz=self.quiz, user=self.user)
        
        quiz=Quiz.objects.get(title=self.quiz)
        mode=quiz.exam_mode
        if mode == False:
            times=pre_q.session_time
            times=datetime.datetime.strptime(times, "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            date_times=now.strftime("%Y-%m-%d %H:%M:%S")
            date_times=datetime.datetime.strptime(date_times, "%Y-%m-%d %H:%M:%S")
            
            que_id = self.question_list.split(",")[0]
            
            
            att_que = UQuestion.objects.get(quiz=self.quiz, user=self.user,questions=que_id)
            att_que.attempt_question = att_que.attempt_question + 1
            fmt = "%Y-%m-%d %H:%M:%S"
            now = datetime.datetime.now()
            date_time=now.strftime(fmt)
            att_que.question_taken_date = date_time
            att_que.save()

            if pre_q.previous_question_list ==  None:
                previous_question_list = []
                previous_question_list.append(que_id)
                pre_q.previous_question_list = previous_question_list
                
            else:
                previous_question_list = pre_q.previous_question_list
                previous_question_list = previous_question_list.replace('[',"").replace("'","").replace(']',"").split(', ')
                previous_question_list.append(que_id)
                pre_q.previous_question_list = list(set(previous_question_list))
            pre_q.save()
            
            

        else:
            pre_qu=PersonalizedQuiz.objects.get(quiz=self.quiz, user=self.user)
            pre_qu.question_attemp=pre_qu.question_attemp+1
            pre_qu.save()
        
        mode=Quiz.objects.get(title=self.quiz)
        mode=mode.exam_mode
        if mode == False:
            times=pre_q.session_time
            times=datetime.datetime.strptime(times, "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            date_times=now.strftime("%Y-%m-%d %H:%M:%S")
            date_times=datetime.datetime.strptime(date_times, "%Y-%m-%d %H:%M:%S")
            if date_times >= times:
                self.complete = True
                self.end = datetime.datetime.now()
                self.save()
                
        
        _, others = self.question_list.split(',', 1) 
        mode=Quiz.objects.get(title=self.quiz)
        modes=mode.exam_mode
        if modes == False:
            att_que = UQuestion.objects.get(quiz=self.quiz, user=self.user, questions__id=_)
            rep_question = att_que.date_of_next_rep
            rep=rep_question[0:10]
            attemp_q=att_que.question_taken_date
            attemp_question=attemp_q[0:10]
            fmt1= "%Y-%m-%d"
            question_att=datetime.datetime.strptime(attemp_question, fmt1)
            question_rep_date=datetime.datetime.strptime(rep, fmt1)
            
            if question_rep_date <= question_att:
                
                if len(others) == 0:
                    others=_+","
                elif others[len(others)-1] == ",":
                    others=others+ _ +","
                self.question_list = others
                corrections=self.question_list.count(",")
                pre_q.correction=corrections
        
                self.save()
                pre_q.save()
                que_ids = self.question_list.split(",")[0]
                

            else:
                self.question_list = others
                self.save()   
                corrections=self.question_list.count(",")
                pre_q.correction=corrections
                pre_q.save()
                que_ids = self.question_list.split(",")[0]

        if modes == True:
            self.question_list = others
            que_ids = self.question_list.split(",")[0]
            self.save()


    def add_to_score(self, points):
        self.current_score += int(points)
        self.save()

    @property
    def get_current_score(self):
        return self.current_score

    def _question_ids(self):

        return [int(n) for n in self.question_order.split(',') if n]

    @property
    def get_percent_correct(self):
        dividend = float(self.current_score)
        divisor = len(self._question_ids())
        if divisor < 1:
            return 0            # prevent divide by zero error

        if dividend > divisor:
            return 100

        correct = int(round((dividend / divisor) * 100))

        if correct >= 1:
            return correct
        else:
            return 0

    def mark_quiz_complete(self):
        self.complete = True
        self.end = now()
        self.save()

    def add_incorrect_question(self, question):
        """
        Adds uid of incorrect question to the list.
        The question object must be passed in.
        """
        if len(self.incorrect_questions) > 0:
            self.incorrect_questions += ','
        self.incorrect_questions += str(question.id) + ","
        if self.complete:
            self.add_to_score(-1)
        self.save()

    @property
    def get_incorrect_questions(self):
        """
        Returns a list of non empty integers, representing the pk of
        questions
        """
        return [int(q) for q in self.incorrect_questions.split(',') if q]

    def remove_incorrect_question(self, question):
        current = self.get_incorrect_questions
        current.remove(question.id)
        self.incorrect_questions = ','.join(map(str, current))
        self.add_to_score(1)
        self.save()

    @property
    def check_if_passed(self):
        return self.get_percent_correct >= self.quiz.pass_mark

    @property
    def result_message(self):
        if self.check_if_passed:
            return self.quiz.success_text
        else:
            return self.quiz.fail_text

    def add_user_answer(self, question, guess):
        from multichoice.models import Answer

        current = json.loads(self.user_answers)
        
        mode=Quiz.objects.get(title=self.quiz)
        modes=mode.e_learning
        modess=mode.exam_mode
        if modes == True and modess == False: 
            current[question.id] = guess
            self.user_answers = json.dumps(current)
            self.save()
            answer_id=Answer.objects.get(id=current[question.id])
            check_answer=answer_id.correct
        else:
            current[question.id] = guess
            self.user_answers = json.dumps(current)
            self.save()
            answer_id=Answer.objects.get(id=current[question.id])
            check_answer=answer_id.correct
        
        mode=Quiz.objects.get(title=self.quiz)
        mode=mode.exam_mode
        if mode == False:
            add_answer_id = UQuestion.objects.get(quiz=self.quiz, user=self.user,questions=question.id)
            if check_answer == False:
                fmt2 = "%z"
                tz1=self.user.timezone1
                tz2 = pytz.timezone(str(tz1))
                user_time = datetime.datetime.now(tz2)
                user_strf=user_time.strftime(fmt2)
                user_hour1=user_strf[1]
                user_hour2=user_strf[2]
                if user_hour1 != "0":
                    hours=user_strf[1:3]
                else:
                    hours=user_strf[2]
                minute=user_strf[3]
                if minute != "0":
                    minutes=user_strf[3:5]
                else:
                    minutes=user_strf[4]
                value=user_strf[0:1]
                value=str(value)
                if value == "-":
                    fmt5 = "%Y-%m-%d %H:%M:%S"
                    time=timedelta(hours=int(hours),minutes=int(minutes))
                    datess=datetime.date.today() 
                    datess=str(datess)
                    time=str(time)
                    user_date=datess+" "+time 
                    user_date_time=datetime.datetime.strptime(user_date , fmt5)
                    add_answer_id.date_of_next_rep=user_date_time
                    
                if value == "+":
                    fmt5 = "%Y-%m-%d %H:%M:%S"
                    time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                    datess=datetime.date.today() 
                    datess=str(datess)
                    time=str(time)
                    user_date=datess+" "+time 
                    user_date_time=datetime.datetime.strptime(user_date , fmt5)
                    add_answer_id.date_of_next_rep=user_date_time
                if value == " ":
                    fmt1= "%Y-%m-%d %H:%M:%S"
                    now = datetime.datetime.now()
                    date_time1=now.strftime(fmt1)
                    user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                add_answer_id.wrong_answer_date = user_date_time
                add_answer_id.question_taken_date= user_date_time
                add_answer_id.today_wrong_answer =1


            if check_answer == True:
                fmt = "%Y-%m-%d %H:%M:%S"
                now = datetime.datetime.now()
                wrong_answer=now.strftime(fmt)
                wrong_answer_table=add_answer_id.wrong_answer_date
                if wrong_answer_table < wrong_answer:
                    add_answer_id.today_wrong_answer = 0            

                qusetion_rep=PersonalizedQuiz.objects.get(quiz=self.quiz, user=self.user)
                qusetion_rep=qusetion_rep.repeat_questions

                fmt2 = "%z"
                tz = self.user
                tz1=tz.timezone1
                tz2 = pytz.timezone(str(tz1))
                user_time = datetime.datetime.now(tz2)
                user=user_time.strftime(fmt2)
                user_hour1=user[1]
                user_hour2=user[2]
                if user_hour1 != "0":
                    hours=user[1:3]
                else:
                    hours=user[2]
                user_time=user[3:5]
                minute=user[3]
                if minute != "0":
                    minutes=user[3:5]
                else:
                    minutes=user[4]
                value=user[0:1]
                value=str(value)
                add_answer_id.correct_answer = add_answer_id.correct_answer + 1
                if add_answer_id.correct_answer == 1:
                    if qusetion_rep == "25":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=2) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                            
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday



                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=2) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=2)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                    elif qusetion_rep == "50":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=3) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=3) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=3)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                    elif qusetion_rep == "75":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=4) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=4) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=4)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                if add_answer_id.correct_answer == 2:
                    if qusetion_rep == "25":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=5) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=5) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=5)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                    elif qusetion_rep == "50":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=7) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=7) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=7)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                    elif qusetion_rep == "75":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=10) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=10) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=10)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                if add_answer_id.correct_answer == 3:
                    if qusetion_rep == "25":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=14) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=14) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=14)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                    elif qusetion_rep == "50":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=21) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=21) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=21)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday


                    elif qusetion_rep == "75":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=30) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=30) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                        
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=30)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time

                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                if add_answer_id.correct_answer == 4:
                    if qusetion_rep == "25":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=30) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=30) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=30)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday


                    elif qusetion_rep == "50":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=60) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=60) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=60)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                    elif qusetion_rep == "75":
                        if value == "-":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=90) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                        if value == "+":
                            fmt5 = "%Y-%m-%d %H:%M:%S"
                            time=timedelta(hours=24)-timedelta(hours=int(hours),minutes=int(minutes))
                            datess=datetime.date.today() + datetime.timedelta(days=90) 
                            datess=str(datess)
                            time=str(time)
                            user_date=datess+" "+time 
                            user_date_time=datetime.datetime.strptime(user_date , fmt5)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday
                            
                        if value == " ":
                            fmt1= "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now() + datetime.timedelta(days=90)
                            date_time1=now.strftime(fmt1)
                            user_date_time=datetime.datetime.strptime(date_time1, fmt1)
                            add_answer_id.date_of_next_rep=user_date_time
                            fmt = "%Y-%m-%d %H:%M:%S"
                            now = datetime.datetime.now()
                            date_time=now.strftime(fmt)
                            yesterday = datetime.datetime.now() - datetime.timedelta(days = 500)
                            add_answer_id.wrong_answer_date = yesterday

                if add_answer_id.correct_answer > 4:
                    if value == "-":
                        time = datetime.datetime.now() - timedelta(hours=int(hours),minutes=int(minutes))
                        add_answer_id.date_of_next_rep = time + datetime.timedelta(days=365)
                    if value == "+":
                        time = datetime.datetime.now() + timedelta(hours=int(hours),minutes=int(minutes))
                        add_answer_id.date_of_next_rep = time + datetime.timedelta(days=365)

            add_answer_id.save() 
        
    def get_questions(self, with_answers=False):
        question_ids = self._question_ids()
        questions = sorted(
            self.quiz.question_set.filter(id__in=question_ids)
                                  .select_subclasses(),
            key=lambda q: question_ids.index(q.id))

        if with_answers:
            user_answers = json.loads(self.user_answers)
            for question in questions:
                question.user_answer = user_answers[str(question.id)]
        return questions

    @property
    def questions_with_user_answers(self):
        return {

            q: q.user_answer for q in self.get_questions(with_answers=True)

        }

    @property
    def get_max_score(self):
        return len(self._question_ids())

    def progress(self):
        """
        Returns the number of questions answered so far and the total number of
        questions.
        """
        mode=Quiz.objects.get(title=self.quiz)
        modes=mode.e_learning
        modess=mode.exam_mode
        if modes == True and modess == False:
            answered = 8
        else:
            answered = len(json.loads(self.user_answers))
        
        total = self.get_max_score
        return answered, total






@python_2_unicode_compatible
class Question(models.Model):
    """
    Base class for all question types.
    Shared properties placed here.
    """

    quiz = models.ManyToManyField(Quiz,
                                  verbose_name=_("Quiz"),
                                  blank=True)

    category = models.ForeignKey(Category,
                                 verbose_name=_("Category"),
                                 blank=True,
                                 null=True,
                                 on_delete=models.CASCADE)

    sub_category = models.ForeignKey(SubCategory,
                                     verbose_name=_("Sub-Category"),
                                     blank=True,
                                     null=True,
                                     on_delete=models.CASCADE)

    figure = models.ImageField(upload_to='uploads/%Y/%m/%d',
                               blank=True,
                               null=True,
                               verbose_name=_("Figure"))

    session_slide = models.IntegerField(default=0,verbose_name=_("session_slide"),blank=True,null=True)

    is_slide = models.BooleanField(default=False, blank=False,verbose_name=_("is_slide"))


    content = models.CharField(max_length=1000,
                               blank=False,null=True,
                               help_text=_("Enter the question text that "
                                           "you want displayed"),
                               verbose_name=_('Question'))

    explanation = models.TextField(max_length=2000,
                                   blank=True,null=True,
                                   help_text=_("Explanation to be shown "
                                               "after the question has "
                                               "been answered."),
                                   verbose_name=_('Explanation'))

    objects = InheritanceManager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['category']

    def __str__(self):
        return '%s %s %s %s' % (self.content, self.explanation, self.sub_category, self.category)



