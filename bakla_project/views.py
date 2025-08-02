# bakla_project/views.py
from django.shortcuts import render
from django.views.decorators.http import require_POST


def handler404_view(request, exception):
    """
    404 Page Not Found (Sayfa Bulunamadı) hatası için özel view.
    """
    # HTTP durum kodunu doğru ayarlamak önemlidir.
    return render(request, 'errors/404.html', status=404)

def handler403_view(request, exception):
    """
    403 Forbidden (Erişim Engellendi) hatası için özel view.
    """
    return render(request, 'errors/403.html', status=403)

def handler500_view(request):
    """
    500 Server Error (Sunucu Hatası) için özel view.
    """
    return render(request, 'errors/500.html', status=500)

def about_view(request):
    """ 'Hakkında' sayfasını render eder. """
    return render(request, 'pages/about.html')
