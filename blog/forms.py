from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post                    # 어떤 Model의 입력 Form인지 지정
        fields = ['title','content']    # 사용자가 수정하도록 허용할 field