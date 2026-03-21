from django.urls import path
from . import views

app_name = 'institutions'

urlpatterns = [
    path('', views.InstitutionListView.as_view(), name='institution_list'),
]
