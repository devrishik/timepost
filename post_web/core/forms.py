# -*- coding: utf-8 -*-
from django import forms

from .models import User


class UserForm(forms.ModelForm):

    class Meta:
        # Set this form to use the User model.
        model = User

        # Constrain the UserForm to just these fields.
        fields = ("first_name", "last_name")


class InstagramUserForm(forms.Form):
    username = forms.CharField(label='UserName',
                         widget=forms.TextInput(
                             attrs={'placeholder': 'UserName'}),
                         required=True)


class InstagramUserIDForm(forms.Form):
    pk = forms.CharField(label='Id',
                         widget=forms.TextInput(
                             attrs={'placeholder': 'UserId'}),
                         required=True)