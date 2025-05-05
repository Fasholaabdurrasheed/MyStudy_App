from django import forms
from .models import Material, Course, Message, CourseQuestion, PastQuestionFile


class MaterialUploadForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all())
    file = forms.FileField()  # <-- single file field
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea, required=False)

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...'}),
        }


class BulkQuestionUploadForm(forms.Form):
    file = forms.FileField(help_text="upload .csv or .xlsx file")


class CourseQuestionForm(forms.ModelForm):
    class Meta:
        model = CourseQuestion
        fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']


class PastQuestionUploadForm(forms.ModelForm):
    class Meta:
        model = PastQuestionFile
        fields = ['title', 'course', 'year', 'file']
