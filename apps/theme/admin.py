from django.contrib import admin
from apps.theme.models import Theme, UserTheme


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'primary_color', 'secondary_color', 'accent_color', 'is_default')
    list_editable = ('is_default', )
    search_fields = ('name',)


@admin.register(UserTheme)
class UserThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'theme')
    list_filter = ('theme',)
    search_fields = ('user__username',)
