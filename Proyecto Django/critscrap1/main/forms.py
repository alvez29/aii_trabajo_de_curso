'''
Created on 13 ene. 2021

@author: Alvaro
'''
from django import forms

class FormularioUnaEntrada(forms.Form):
    entrada = forms.CharField(label="Busqueda", widget=forms.TextInput, required=True)

