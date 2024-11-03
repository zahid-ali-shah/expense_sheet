from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.theme.models import Theme, UserTheme


def get_user_theme(request):
    """Get the current user's theme or default theme"""
    if request.user.is_authenticated:
        user_theme = UserTheme.objects.filter(user=request.user).first()
        if user_theme and user_theme.theme:
            theme = user_theme.theme
        else:
            theme = Theme.objects.filter(is_default=True).first()
    else:
        theme = Theme.objects.filter(is_default=True).first()

    if theme:
        return JsonResponse({
            'name': theme.name,
            'primary_color': theme.primary_color,
            'secondary_color': theme.secondary_color
        })
    return JsonResponse({
        'name': 'default',
        'primary_color': '#2196F3',
        'secondary_color': '#FF5722'
    })


@require_http_methods(["POST"])
def set_user_theme(request, theme_id):
    """Set theme for authenticated users"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        theme = Theme.objects.get(id=theme_id)
        user_theme, created = UserTheme.objects.get_or_create(user=request.user)
        user_theme.theme = theme
        user_theme.save()

        # Invalidate the cached theme
        cache.delete(f"user_theme_{request.user.id}")

        return JsonResponse({'status': 'success'})
    except Theme.DoesNotExist:
        return JsonResponse({'error': 'Theme not found'}, status=404)
