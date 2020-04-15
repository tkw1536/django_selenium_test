from __future__ import annotations

from django import forms


class SampleForm(forms.Form):
    a = forms.CharField()
    b = forms.ChoiceField(choices=(("a", "a"), ("b", "b")))
    c = forms.CharField(required=True)
