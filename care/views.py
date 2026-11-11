from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from .models import Alert, AuditEvent, CareTask, Medication, Resident, FamilyAccess
from .serializers import ResidentSerializer, CareTaskSerializer, MedicationSerializer, AdministrationSerializer, AlertSerializer, AuditSerializer, SessionSerializer, FamilyAccessSerializer
from .services import profile_for, open_resident_session, complete_task, record_administration, audit

def home(request):
    return render(request, "home.html")

def caregiver(request):
    return render(request, "caregiver.html")

def presentation(request):
    return render(request, "presentation.html")

def manager_login(request):
    if request.user.is_authenticated:
        return redirect("manager_dashboard")
    error = None
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username", ""), password=request.POST.get("password", ""))
        if user and user.is_active:
            try:
                if user.staffprofile.role not in {"ADMIN", "COORD", "NURSE"}:
                    error = "Esta conta não possui acesso gerencial."
                else:
                    login(request, user); return redirect("manager_dashboard")
            except Exception:
                error = "Usuário sem vínculo institucional."
        else:
            error = "Usuário ou senha inválidos."
    return render(request, "login.html", {"error": error})

def manager_logout(request):
    logout(request)
    return redirect("manager_login")

@login_required(login_url="manager_login")
def manager_dashboard(request):
    try:
        if request.user.staffprofile.role not in {"ADMIN", "COORD", "NURSE"}:
            return render(request, "login.html", {"error": "Esta conta não possui acesso gerencial."}, status=403)
    except Exception:
        return render(request, "login.html", {"error": "Usuário sem vínculo institucional."}, status=403)
    institution = request.user.staffprofile.institution
    summary = {
        "residents_active": Resident.objects.filter(institution=institution, status="ACTIVE").count(),
        "tasks_pending": CareTask.objects.filter(plan__resident__institution=institution, status="PENDING").count(),
        "alerts_open": Alert.objects.filter(resident__institution=institution).exclude(status="CLOSED").count(),
        "audit_total": AuditEvent.objects.filter(institution=institution).count(),
    }
    return render(request, "home.html", {"manager": request.user, "summary": summary})

class InstitutionScopedMixin:
    def profile(self):
        return profile_for(self.request.user)

    def require_roles(self, *roles):
        profile = self.profile()
        if profile.role not in roles:
            raise PermissionDenied("Esta operação exige uma função institucional autorizada.")
        return profile

class ResidentViewSet(InstitutionScopedMixin, viewsets.ModelViewSet):
    serializer_class = ResidentSerializer
    def get_queryset(self):
        return Resident.objects.filter(institution=self.profile().institution).order_by("name")
    def perform_create(self, serializer):
        profile = self.require_roles("ADMIN", "COORD")
        obj = serializer.save(institution=profile.institution)
        audit(profile, "RESIDENT_CREATE", obj, after=ResidentSerializer(obj).data)
    def perform_update(self, serializer):
        profile = self.require_roles("ADMIN", "COORD")
        before = ResidentSerializer(self.get_object()).data
        obj = serializer.save()
        audit(profile, "RESIDENT_UPDATE", obj, before=before, after=ResidentSerializer(obj).data)
    def perform_destroy(self, instance):
        profile = self.require_roles("ADMIN", "COORD")
        audit(profile, "RESIDENT_DELETE", instance, before=ResidentSerializer(instance).data)
        instance.delete()
    @action(detail=True, methods=["post"])
    def session(self, request, pk=None):
        resident = self.get_object()
        device_id = request.data.get("device_id", "unknown")
        emergency = bool(request.data.get("emergency", False))
        if not isinstance(device_id, str) or not device_id.strip():
            return Response({"device_id": ["Identificador do dispositivo é obrigatório."]}, status=400)
        obj = open_resident_session(self.profile(), resident, device_id.strip(), emergency)
        return Response(SessionSerializer(obj).data, status=status.HTTP_201_CREATED)

class TaskViewSet(InstitutionScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CareTaskSerializer
    def get_queryset(self):
        return CareTask.objects.filter(plan__resident__institution=self.profile().institution).select_related("plan", "plan__resident").order_by("scheduled_at")
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        self.require_roles("ADMIN", "COORD", "NURSE", "CAREGIVER")
        task = self.get_object()
        task = complete_task(self.profile(), task, request.data.get("status", "DONE"), request.data.get("note", ""))
        return Response(CareTaskSerializer(task).data)

class MedicationViewSet(InstitutionScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = MedicationSerializer
    def get_queryset(self):
        return Medication.objects.filter(resident__institution=self.profile().institution).order_by("resident__name", "name")
    @action(detail=True, methods=["post"])
    def administer(self, request, pk=None):
        self.require_roles("ADMIN", "COORD", "NURSE", "CAREGIVER")
        medication = self.get_object()
        serializer = AdministrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        obj, created = record_administration(self.profile(), medication, serializer.validated_data)
        return Response(AdministrationSerializer(obj).data, status=201 if created else 200)

class AlertViewSet(InstitutionScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertSerializer
    def get_queryset(self):
        return Alert.objects.filter(resident__institution=self.profile().institution).order_by("-created_at")
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        alert = self.get_object(); alert.status = "CLOSED"; alert.closed_at = timezone.now(); alert.acknowledged_by = self.profile(); alert.save()
        audit(self.profile(), "ALERT_CLOSE", alert.resident, after={"alert_id": alert.id})
        return Response(AlertSerializer(alert).data)

class AuditViewSet(InstitutionScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditSerializer
    def get_queryset(self):
        return AuditEvent.objects.filter(institution=self.profile().institution).order_by("-occurred_at")

class ReportView(InstitutionScopedMixin, APIView):
    def get(self, request):
        profile = self.require_roles("ADMIN", "COORD", "NURSE")
        residents = Resident.objects.filter(institution=profile.institution)
        alerts = Alert.objects.filter(resident__institution=profile.institution)
        tasks = CareTask.objects.filter(plan__resident__institution=profile.institution)
        return Response({"institution": profile.institution.name, "generated_at": timezone.now(), "residents": {"active": residents.filter(status="ACTIVE").count(), "total": residents.count()}, "tasks": {"pending": tasks.filter(status="PENDING").count(), "completed": tasks.filter(status="DONE").count(), "exceptions": tasks.filter(status__in=["MISSED", "REFUSED", "EXCEPTION"]).count()}, "alerts": {"open": alerts.exclude(status="CLOSED").count(), "critical_open": alerts.filter(status="OPEN", severity="CRITICAL").count()}})

class FamilySummaryView(APIView):
    permission_classes = []
    def get(self, request, token):
        access = FamilyAccess.objects.select_related("resident").filter(access_token=token, active=True).first()
        if not access or (access.expires_at and access.expires_at <= timezone.now()):
            return Response({"detail": "Acesso familiar inválido ou expirado."}, status=404)
        resident = access.resident
        data = {"resident": {"name": resident.name, "room": resident.room, "bed": resident.bed}, "contact": access.contact_name, "updated_at": resident.updated_at}
        if access.permissions.get("care_summary", True):
            data["care_summary"] = {"recent_tasks": list(CareTask.objects.filter(plan__resident=resident).order_by("-scheduled_at").values("name", "status", "completed_at")[:20]), "open_alerts": Alert.objects.filter(resident=resident, status="OPEN").count()}
        return Response(data)

class HealthView(APIView):
    permission_classes = []
    def get(self, request):
        return Response({"service": "cuidar+", "status": "ok", "time": timezone.now()})
