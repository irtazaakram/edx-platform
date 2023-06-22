"""
Handlers for notifications
"""
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from openedx_events.learning.signals import COURSE_UNENROLLMENT_COMPLETED

from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference


log = logging.getLogger(__name__)


@receiver(post_save, sender='student.CourseEnrollment')
def course_enrollment_post_save(sender, instance, created, **kwargs):
    """
    Watches for post_save signal for creates on the CourseEnrollment table.
    Generate a CourseNotificationPreference if new Enrollment is created
    """
    if created and ENABLE_NOTIFICATIONS.is_enabled(instance.course_id):
        try:
            CourseNotificationPreference.objects.create(user=instance.user, course_id=instance.course_id)
        except IntegrityError:
            log.info(f'CourseNotificationPreference already exists for user {instance.user} '
                     f'and course {instance.course_id}')


@receiver(COURSE_UNENROLLMENT_COMPLETED)
def on_user_course_unenrollment(enrollment, **kwargs):
    """
    Removes user notification preference when user un-enrolls from the course
    """
    try:
        user_id = enrollment.user.id
        course_key = enrollment.course.course_key
        preference = CourseNotificationPreference.objects.get(user__id=user_id, course_id=course_key)
        preference.delete()
    except ObjectDoesNotExist:
        log.info(f'Notification Preference doesnot exist for {enrollment.user.pii.username} in {course_key}')
