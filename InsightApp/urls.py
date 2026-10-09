# InsightApp/urls.py
from django.urls import path
from InsightApp import views

urlpatterns = [
    path("insights/", views.insights_view, name="insights"),
]
