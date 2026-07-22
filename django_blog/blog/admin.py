from django.contrib import admin
from .models import Post

# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')  # 목록 화면에 제목과 작성일을 컬럼으로 표시
    search_fields = ('title', 'content')    # 제목과 본문을 대상으로 검색 상자 제공