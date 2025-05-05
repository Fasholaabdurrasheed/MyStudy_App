from django import forms
from exams.models import Message
from django.contrib.auth.models import User

class MessageForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Message
        fields = ['content', 'receiver']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4, 'placeholder': 'Type your message...'}),
        }