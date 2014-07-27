# -*- coding: utf-8 -*-
# Import the AbstractUser model
import operator
from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django_extensions.db.models import TimeStampedModel

# Import the basic Django ORM models library
from django.db import models

from django.utils.translation import ugettext_lazy as _

from .utils import compute_timepost_day

# Subclass AbstractUser
class User(AbstractUser):

	timestamp = models.CharField(_('Recent Timestamp'), max_length=20, 
					blank=True, null=True, editable=False)
	uid = models.CharField(max_length=255, null=True, blank=True, unique=True)

	def __unicode__(self):
		return self.username

	@property
	def timestamp_datetime(self):
		if self.timestamp:
			return datetime.utcfromtimestamp(float(self.timestamp))
		return -1

	def day_time_dict(self):
		return compute_timepost_day(self)

	def day_timepost(self):
		time_dict = self.day_time_dict()
		return max(time_dict.iteritems(), key=operator.itemgetter(1))[0]


class Follow(TimeStampedModel):

    """Relation between user and his follower"""
    user = models.ForeignKey(User, related_name='user')
    follower = models.ForeignKey(User, related_name='follower')

    class Meta:
        get_latest_by = 'created'

    def __unicode__(self):
        return "{follower} follows {user}".format(
            follower=self.follower, user=self.user)


class Recent(TimeStampedModel):

	"""
	Store the async call for getting recent model
	"""
	user = models.ForeignKey(User, related_name='recent_timestamp')
	success = models.BooleanField(default=False)
