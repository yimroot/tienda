from django.contrib.auth.decorators import user_passes_test

def check_admin(user):
    return user.is_authenticated and (user.rol == 'admin' or user.is_superuser)

def check_bodeguero(user):
    return user.is_authenticated and (user.rol == 'bodeguero' or user.rol == 'admin' or user.is_superuser)

def solo_admin(view_func):
    return user_passes_test(check_admin, login_url='home')(view_func)

def solo_bodeguero(view_func):
    return user_passes_test(check_bodeguero, login_url='home')(view_func)