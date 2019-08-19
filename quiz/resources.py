from import_export import resources
from .models import Quiz, Category ,SubCategory,Question
from multichoice.models import Answer ,MCQuestion
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from import_export.widgets import ManyToManyWidget
class QuizResource(resources.ModelResource):
    

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        dataset.headers = ('modelField1', 'modelField2', ...)
        dataset = dataset[:6]
        for data in dataset:
            lst = list(data)

             
            data = tuple(lst)
            self.using_transactions = True
        del dataset

    
    class Meta:
        model = Answer 
        fields = ('id',) 

class QuizafterResource(resources.ModelResource):
    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        for data in dataset:
            lst = list(data)
            quiz = Quiz.objects.filter(title=str(lst[1]))
            if len(quiz) == 0:
                quiz = Quiz.objects.create(title=str(lst[1]))
            else:
                quiz=quiz.first()
        
            q1 = Question.objects.filter(category__category=str.capitalize(lst[2]),sub_category__sub_category=str.capitalize(lst[3]),content=(lst[5]))
            q1=q1.first()
            
            q1.quiz.add(quiz)
            q1.save()


            q1=MCQuestion.objects.filter(category__category=str.capitalize(lst[2]),sub_category__sub_category=str.capitalize(lst[3]),content=(lst[5])).first()
            for number in range(7,len(lst)):

                answers = Answer.objects.filter(content=lst[number],question=q1)
                if lst[number] in ["", " ", "  "] :
                    continue
                elif len(answers) == 0:
                    if lst[number] == lst[7]:
                        answer = Answer.objects.create(content=lst[number],question=q1, correct=True)
                    else:
                        answer = Answer.objects.create(content=lst[number],question=q1)
                elif len(answers) == 1:
                    answer= Answer.objects.get(content=lst[number],
                        question=q1)
                elif len(answers) > 1:
                    answer= Answer.objects.filter(content=lst[number],question=q1).first()


    category = fields.Field(column_name='category',attribute='category',widget=ForeignKeyWidget(Category,'category'))
    sub_category = fields.Field(column_name='sub_category',attribute='sub_category',widget=ForeignKeyWidget(SubCategory,'sub_category'))

    class Meta:
        model = MCQuestion
      
        skip_unchanged = True
        report_skipped = False
        fields = ('id','quiz','category','sub_category','content','explanation')
        export_order = ('id','quiz', 'category', 'sub_category', 'content','explanation')




















