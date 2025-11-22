#!/usr/bin/env python
"""
Script de prueba para verificar que el envío de emails funciona correctamente.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secretsanta_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    print("=" * 60)
    print("TEST DE ENVÍO DE EMAIL")
    print("=" * 60)
    print(f"\nConfiguración actual:")
    print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"  EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NO CONFIGURADO'}")
    print("\n" + "=" * 60)
    
    # Email de prueba
    subject = "🎅 Test - Amigo Invisible"
    message = """
Hola,

Este es un email de prueba del sistema de Amigo Invisible.

Si recibes este mensaje, significa que el SMTP está configurado correctamente.

¡Saludos!
    """
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [settings.EMAIL_HOST_USER]  # Enviar a ti mismo
    
    print(f"\nEnviando email de prueba...")
    print(f"  De: {from_email}")
    print(f"  Para: {recipient_list}")
    print(f"  Asunto: {subject}")
    print("\nEnviando...\n")
    
    try:
        result = send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        print("=" * 60)
        print("✅ EMAIL ENVIADO CORRECTAMENTE")
        print("=" * 60)
        print(f"\nResultado: {result} email(s) enviado(s)")
        print(f"\nRevisa tu bandeja de entrada en: {recipient_list[0]}")
        print("Si no lo ves, revisa también la carpeta de SPAM.\n")
        return True
        
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR AL ENVIAR EMAIL")
        print("=" * 60)
        print(f"\nError: {type(e).__name__}")
        print(f"Mensaje: {str(e)}\n")
        
        # Diagnóstico adicional
        print("Posibles causas:")
        print("  1. Contraseña de aplicación incorrecta")
        print("  2. Verificación en 2 pasos no activada en Gmail")
        print("  3. Acceso de aplicaciones menos seguras bloqueado")
        print("  4. Firewall bloqueando el puerto 587")
        print("\nPara Gmail, asegúrate de:")
        print("  - Tener verificación en 2 pasos activada")
        print("  - Usar una 'Contraseña de aplicación' (no tu contraseña normal)")
        print("  - Generar la contraseña en: https://myaccount.google.com/apppasswords\n")
        return False

if __name__ == "__main__":
    test_email()
