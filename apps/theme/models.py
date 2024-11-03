from django.contrib.auth import get_user_model

User = get_user_model()

from django.db import models


class Theme(models.Model):
    name = models.CharField(max_length=50)

    # Primary and Secondary colors
    primary_color = models.CharField(max_length=7, help_text="Hex color code (e.g., #2196F3)")
    secondary_color = models.CharField(max_length=7, help_text="Hex color code (e.g., #FF5722)")

    # Additional Material Design Colors
    accent_color = models.CharField(
        max_length=7, blank=True, help_text="Hex color code for accent color (e.g., #FFC107)"
    )
    background_color = models.CharField(
        max_length=7, blank=True, help_text="Hex color code for background color (e.g., #FFFFFF)"
    )
    error_color = models.CharField(
        max_length=7, blank=True, help_text="Hex color code for error color (e.g., #F44336)"
    )
    surface_color = models.CharField(
        max_length=7, blank=True, help_text="Hex color code for surface color (e.g., #FFFFFF)"
    )
    on_primary_color = models.CharField(
        max_length=7, blank=True, help_text="Hex color code for text on primary color (e.g., #FFFFFF)"
    )
    on_secondary_color = models.CharField(
        max_length=7, blank=True, help_text="Hex color code for text on secondary color (e.g., #000000)"
    )

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other themes to not default
            Theme.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UserTheme(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user}'s theme"
