from django.urls import reverse

def get_redirect_for_user(user):
    """
    Returns the dashboard URL name based on the user's role.
    """
    if hasattr(user, "profile"):
        if user.profile.role == "ADMIN":
            return reverse("admin_dashboard")
        elif user.profile.role == "STAFF":
            return reverse("home")   # or staff_dashboard if you add one
    return reverse("login")