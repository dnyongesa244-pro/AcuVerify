from django.conf import settings

def profile_picture(request):
    """Provide `profile_pic_url` and `profile_initials` for templates.

    Looks up a Staff or Students record by email (matching the logged-in user)
    and returns the image URL if present. Falls back to initials.
    """
    user = getattr(request, 'user', None)
    result = {'profile_pic_url': None, 'profile_initials': None}
    if not user or not user.is_authenticated:
        return result

    # Compute initials from full name or username
    full_name = getattr(user, 'get_full_name', None)
    try:
        name = user.get_full_name() if callable(user.get_full_name) else ''
    except Exception:
        name = ''
    if not name:
        name = getattr(user, 'username', '')

    initials = ''.join([p[0] for p in name.split() if p])[:2].upper() if name else ''
    result['profile_initials'] = initials or (user.username[:2].upper() if getattr(user, 'username', None) else '')

    # Lazy import models to avoid startup cycles
    try:
        from .models import Staff, Students
        # Try Staff first
        staff = Staff.objects.filter(email__iexact=getattr(user, 'email', '')).first()
        if staff and getattr(staff, 'profile_pic', None):
            try:
                result['profile_pic_url'] = staff.profile_pic.url
                return result
            except Exception:
                result['profile_pic_url'] = None

        student = Students.objects.filter(email__iexact=getattr(user, 'email', '')).first()
        if student and getattr(student, 'profile_pic', None):
            try:
                result['profile_pic_url'] = student.profile_pic.url
                return result
            except Exception:
                result['profile_pic_url'] = None
    except Exception:
        # Models may not be available yet
        pass

    return result
