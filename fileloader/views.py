from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from .forms import *
from django.http import HttpResponse,  Http404
from .functions import *
import os
from django.conf import settings
from django.contrib.auth import logout
 
def index(request):
    return render(request, 'fileloader/index.html')

def esg_choose_task(request):
    return render(request, 'fileloader/esg_choose_task.html')

def generateonly(request):
    return render(request, 'fileloader/generateonly.html')

def calibrateandgenerate(request):
    return render(request, 'fileloader/calibrateandgenerate.html')

def testesgs(request):
    return render(request, 'fileloader/testesgs.html')

def selectmodel(request):
    return render(request, 'fileloader/selectmodel.html')

def onefactormodel(request):
    return render(request, 'fileloader/onefactormodel.html')

@login_required
def vasicekmodel(request):
    if request.method == 'POST':
        form = SetUpVasicek(request.POST)
        if form.is_valid():

            nosc = int(request.POST.get('number_of_scenarios'))
            vector_length = int(request.POST.get('vector_length'))
            start_rate= float(request.POST.get('start_rate'))
            alpha= float(request.POST.get('alpha'))
            sig= float(request.POST.get('sig'))
            IRscs = filter(lambda t: t[0] in form.cleaned_data['IRscenarios'], form.fields['IRscenarios'].choices)
            generate_only_vasicek(nosc, vector_length, start_rate,alpha, alpha,  sig, IRscs)
            return render(request, 'fileloader/esg_ready.html')
    else:
        form = SetUpVasicek()
    return render(request, 'fileloader/vasicekmodel.html', {'form': form})

@login_required
def calib_vasicekmodel(request):
    if request.method == 'POST':
        form = CalibVasicek(request.POST, request.FILES)
        if form.is_valid() :
            nosc = int(request.POST.get('number_of_scenarios'))
            vector_length = int(request.POST.get('vector_length'))
            IRscs = filter(lambda t: t[0] in form.cleaned_data['IRscenarios'], form.fields['IRscenarios'].choices)
            rates_to_calibrate = str(request.POST.get('rates_to_calibrate'))
            if rates_to_calibrate  == "EIOPA":
                curr = str(request.POST.get('curr'))
                year = int(request.POST.get('year'))
                customrates = ""
            else:
                curr = "XX"
                year = 9999
                customrates = request.FILES['file']

            calib_and_generate_vasicek(nosc, vector_length,year, curr, rates_to_calibrate, customrates, IRscs)
            return render(request, 'fileloader/esg_ready.html')

    else:
        form = CalibVasicek()
    return render(request, 'fileloader/vasicekmodel.html', {'form': form})

def cirmodel(request):
    return render(request, 'fileloader/cirmodel.html')

def hwmodel(request):
    return render(request, 'fileloader/hwmodel.html')

def lmmplusmodel(request):
    return render(request, 'fileloader/lmmplusmodel.html')

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                calc_actuarial(request.FILES['file'])
                return render(request, 'fileloader/file_uploaded.html')
            except:
                return render(request, 'fileloader/error.html')
    else:
        form = UploadFileForm()
    return render(request, 'fileloader/upload.html', {'form': form})

@login_required
def esg_setup(request):
    if request.method == 'POST':
        form = SetUpESG(request.POST)
        if form.is_valid():
            # cur, yr , no_sc
            #curr= request.POST.get('currency')
            curr = filter(lambda t: t[0] in form.cleaned_data['currency'], form.fields['currency'].choices)
            year= int(request.POST.get('year'))
            nosc = int(request.POST.get('number_of_scenarios'))
            sig= float(request.POST.get('sig'))
            IRscs = filter(lambda t: t[0] in form.cleaned_data['IRscenarios'], form.fields['IRscenarios'].choices)
            try:
                prepare_esg(curr, year, nosc, sig, IRscs)
                return render(request, 'fileloader/esg_ready.html')
            except:
                return render(request, 'fileloader/error_esg.html')
    else:
        form = SetUpESG()
    return render(request, 'fileloader/esg_setup.html', {'form': form})

@login_required
def download_file(request):
    path = 'results.xlsx'
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def download_sample(request):
    path = 'sample.xlsx'
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def esg_ready(request):
    path = 'zipped_output.zip'
    fold_path = os.path.join(settings.MEDIA_ROOT, "esgs")
    file_path = os.path.join(fold_path, path)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/zip")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
def error_handler(request):
    return render(request, 'fileloader/error.html')

@login_required
def error_esg(request):
    return render(request, 'fileloader/error_esg.html')


@login_required
def pagelogout(request):
    logout(request)

    return render(request, 'fileloader/index.html')

