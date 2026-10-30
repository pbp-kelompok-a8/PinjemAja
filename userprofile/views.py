import json
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .decorators import rate_limit
from .forms import RegisterForm, ProfileForm, UserEmailForm
from .models import Profile

def _wilayah(request, key, old):
    v = request.POST.get(key, '').strip()
    return old if (not v or v.startswith(('Pilih', 'Memuat'))) else v[:100]

def _error_items(form):
    items = []
    for name, errors in form.errors.items():
        label = 'Form' if name == '__all__' else str(form[name].label)
        items.append({
            'title': label,
            'message': ' '.join(str(e) for e in list(errors)[:2]),
            'type': 'error',
        })
    return items


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Akun berhasil dibuat. Selamat datang!')
            return redirect('userprofile:my_profile')
    else:
        form = RegisterForm()
    return render(request, 'userprofile/register.html', {'form': form})

@require_POST
def register_htmx(request):
    form = RegisterForm(request.POST)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Akun berhasil dibuat. Selamat datang!')
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse('userprofile:my_profile')
        return response

    response = render(request, 'userprofile/partials/register_form.html', {'form': form})
    response['HX-Trigger'] = json.dumps({
        'showToasts': {'items': _error_items(form)}
    })
    return response

@rate_limit('login', limit=5, period=300)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Berhasil masuk.')
            return redirect('landing_page')
    else:
        form = AuthenticationForm()
    return render(request, 'userprofile/login.html', {'form': form})

@rate_limit('login', limit=5, period=300)
@require_POST
def login_htmx(request):
    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, 'Berhasil masuk.')
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse('landing_page')
        return response

    response = render(request, 'userprofile/partials/login_form.html', {'form': form})
    response['HX-Trigger'] = json.dumps({
        'showToast': {'title': 'Gagal login', 'message': 'Username atau password salah.', 'type': 'error'}
    })
    return response

def logout_view(request):
    logout(request)
    return redirect('landing_page')

@login_required
def my_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'userprofile/my_profile.html', {'profile': profile, 'active_menu': 'profil'})

@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    old_avatar = profile.avatar.name if profile.avatar else None
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        email_form = (
            UserEmailForm(request.POST, instance=request.user)
            if 'email' in request.POST
            else None
        )
        form_ok = form.is_valid()
        email_ok = email_form.is_valid() if email_form else True

        if form_ok and email_ok:
            if email_form:
                email_form.save()

            profile = form.save(commit=False)
            profile.province = _wilayah(request, 'province', profile.province)
            profile.city = _wilayah(request, 'city', profile.city)
            profile.district = _wilayah(request, 'district', profile.district)
            profile.subdistrict = _wilayah(request, 'subdistrict', profile.subdistrict)
            profile.street_address = request.POST.get('street_address', '').strip()[:300]
            profile.save()
            if old_avatar and 'avatar' in request.FILES and old_avatar != profile.avatar.name:
                profile.avatar.storage.delete(old_avatar)
            messages.success(request, 'Profil berhasil disimpan.')
            return redirect('userprofile:my_profile')

        if email_form and not email_ok:
            email_errors = email_form.errors.get('email')
            if email_errors:
                form.add_error(None, email_errors[0])

    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        'userprofile/edit_profile.html',
        {
            'form': form,
            'profile': profile,
            'active_menu': 'profil',
        },
    )

@require_POST
@login_required
def edit_profile_htmx(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    old_avatar = profile.avatar.name if profile.avatar else None
    form = ProfileForm(request.POST, request.FILES, instance=profile)
    email_form = UserEmailForm(request.POST, instance=request.user) if 'email' in request.POST else None

    form_ok = form.is_valid()
    email_ok = email_form.is_valid() if email_form else True

    if form_ok and email_ok:
        if email_form:
            email_form.save()
        profile = form.save(commit=False)

        profile.province = _wilayah(request, 'province', profile.province)
        profile.city = _wilayah(request, 'city', profile.city)
        profile.district = _wilayah(request, 'district', profile.district)
        profile.subdistrict = _wilayah(request, 'subdistrict', profile.subdistrict)
        profile.street_address = request.POST.get('street_address', '').strip()[:300]

        profile.save()
        if old_avatar and 'avatar' in request.FILES and old_avatar != profile.avatar.name:
            profile.avatar.storage.delete(old_avatar)
        messages.success(request, 'Profil berhasil disimpan.')

        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse(
            'userprofile:my_profile'
        )
        return response
    if not email_ok:
        form.add_error(None, email_form.errors['email'][0])

    response = render(
        request,
        'userprofile/partials/edit_profile_form.html',
        {'form': form, 'profile': profile}
    )
    response['HX-Trigger'] = json.dumps({
        'showToast': {
            'title': 'Gagal menyimpan',
            'message': 'Periksa kembali data yang kamu masukkan.',
            'type': 'error'
        }
    })
    return response

@login_required
def public_profile(request, user_id):
    profile = get_object_or_404(Profile, user__id=user_id)
    return render(request, 'userprofile/public_profile.html', {'profile': profile})

@login_required
@require_POST
def delete_avatar(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if profile.avatar:
        profile.avatar.delete(save=False)
        profile.avatar = None
        profile.save()
        message, toast_type = 'Foto profil berhasil dihapus.', 'success'
    else:
        message, toast_type = 'Belum ada foto profil untuk dihapus.', 'normal'

    form = ProfileForm(instance=profile)
    response = render(request, 'userprofile/partials/edit_profile_form.html', {
        'form': form, 'profile': profile
    })
    response['HX-Trigger'] = json.dumps({
        'showToast': {'title': 'Foto Profil', 'message': message, 'type': toast_type}
    })
    return response

@login_required
@require_POST
def hard_delete_account(request):
    user = request.user
    if not user.check_password(request.POST.get('password', '')):
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({'showToast': {
            'title': 'Gagal', 'message': 'Password salah.', 'type': 'error'}})
        return response

    profile = Profile.objects.filter(user=user).first()
    if profile and profile.avatar:
        profile.avatar.delete(save=False)

    logout(request)
    user.delete()
    messages.success(request, 'Akun dihapus permanen.')
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('landing_page')
    return response