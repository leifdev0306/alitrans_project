from django.shortcuts import render, redirect
from django.contrib import messages
from emails.models import Email, Destinatario


def dashboard(request):
    total_correos = Email.objects.count()
    enviados = Email.objects.filter(estado='enviado').count()
    programados = Email.objects.filter(estado='programado').count()
    total_destinatarios = Destinatario.objects.filter(activo=True).count()
    ultimos = Email.objects.all()[:5]

    context = {
        'total_correos': total_correos,
        'enviados': enviados,
        'programados': programados,
        'total_destinatarios': total_destinatarios,
        'ultimos': ultimos,
    }
    return render(request, 'frontend/dashboard.html', context)


def lista_correos(request):
    correos = Email.objects.all()
    return render(request, 'frontend/lista_correos.html', {'correos': correos})


def crear_correo(request):
    if request.method == 'POST':
        asunto = request.POST.get('asunto')
        cuerpo = request.POST.get('cuerpo')
        destinatarios = request.POST.get('destinatarios', '')
        if asunto and cuerpo:
            Email.objects.create(
                asunto=asunto,
                cuerpo=cuerpo,
                destinatarios=destinatarios,
            )
            messages.success(request, 'Correo creado exitosamente.')
            return redirect('frontend:lista_correos')
    return render(request, 'frontend/crear_correo.html')


def lista_destinatarios(request):
    destinatarios = Destinatario.objects.all()
    return render(request, 'frontend/lista_destinatarios.html', {'destinatarios': destinatarios})