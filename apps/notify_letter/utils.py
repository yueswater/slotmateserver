import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def _send_email_core(recipient_email, subject, context, template_name):
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"SMTP_ERROR: {str(e)}")
        return False


def send_notification_email(
    recipient_email, subject, context, template_name="emails/appointment_confirmed.html"
):
    return _send_email_core(recipient_email, subject, context, template_name)


def send_confirmation_email(recipient_email, context):
    subject = f"[SlotMate] Appointment Confirmed - {context.get('date')}"
    return _send_email_core(
        recipient_email,
        subject,
        context,
        template_name="emails/appointment_confirmed.html",
    )


def send_rejection_email(recipient_email, context):
    subject = f"[SlotMate] Appointment Status Update - {context.get('date')}"
    return _send_email_core(
        recipient_email,
        subject,
        context,
        template_name="emails/appointment_rejected.html",
    )


def send_password_reset_email(recipient_email, context):
    subject = "[SlotMate] Password Reset Request"
    return _send_email_core(
        recipient_email=recipient_email,
        subject=subject,
        context=context,
        template_name="emails/password_reset.html",
    )

def send_password_reset_confirmation_email(recipient_email, context):
    subject = "[SlotMate] Password Reset Successful"
    return _send_email_core(
        recipient_email=recipient_email,
        subject=subject,
        context=context,
        template_name="emails/password_reset_confirmation.html",
    )