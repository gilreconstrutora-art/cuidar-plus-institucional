from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ResidentViewSet, TaskViewSet, MedicationViewSet, AlertViewSet, AuditViewSet, HealthView, ReportView, FamilySummaryView

router = DefaultRouter()
router.register("residents", ResidentViewSet, basename="resident")
router.register("tasks", TaskViewSet, basename="task")
router.register("medications", MedicationViewSet, basename="medication")
router.register("alerts", AlertViewSet, basename="alert")
router.register("audit", AuditViewSet, basename="audit")
urlpatterns = [path("health/", HealthView.as_view()), path("reports/summary/", ReportView.as_view()), path("family/<uuid:token>/summary/", FamilySummaryView.as_view()), path("", include(router.urls))]
