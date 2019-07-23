from django.conf import settings

from pyliferisk import Actuarial , Axn, annuity, Ax, AExn, nEx
import pandas as pd

import os
import os.path as path
import numbers
import time
import sys
import math
import numpy as np
import pandas as pd
import scipy.stats
import csv
from datetime import date, timedelta, datetime
import calendar
import matplotlib.pyplot as plt
import warnings
import shutil

warnings.simplefilter(action='ignore', category=FutureWarning)

ROOT= settings.MEDIA_ROOT + "//esgs"

scenD   = {"BE"   : "RFR_spot_no_VA",
            "UP"   : "Spot_NO_VA_shock_UP",
            "DOWN" : "Spot_NO_VA_shock_DOWN"}

curr_adv  = {"EUR": "Euro",
            "CHF": "Switzerland",
            "PLN": "Poland",
            "SGD": "Singapore",
            "USD": "United States"}

currD  = {"Euro":"EUR",
        "Switzerland":"CHF",
        "Poland": "PLN",
        "Singapore": "SGD" ,
        "United States":"USD"}


printlog = open( ROOT +"//output//"+ 'printlog.txt', 'w')


def handle_uploaded_file(f):
    with open( settings.MEDIA_ROOT + 'dummy.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def create_esgs(cur, yr , no_sc):
    with open( settings.MEDIA_ROOT + "//" +  'dummy.txt', 'w') as destination:
        destination.write("{}\n".format(cur))
        destination.write("{}\n".format(yr))
        destination.write("{}\n".format(no_sc))

def calc_actuarial(fname):
    dfp = pd.read_excel(fname, sheetname="pol")
    dft = pd.read_excel(fname, sheetname="tbl")

    lc = len(dfp)
    lst = []

    for r in range(0, lc):
        idx = dfp.at[r, "id"]
        x = dfp.at[r, "x"]
        n = dfp.at[r, "n"]
        m = dfp.at[r, "m"]
        int_rate  = dfp.at[r, "int_rate"]
        what  = dfp.at[r, "what"]
        mort_tbl  = dfp.at[r, "mort_tbl"]

        mylist = dft[mort_tbl].tolist()
        mylist[0] = int(mylist[0])

        tbl = tuple(mylist)

        mt = Actuarial (nt=tbl , i =int_rate)

        if what == "annuity":
            result = annuity(mt,x,n,0,m)
        elif what == "Axn":
            result = Axn(mt,x,n)
        elif what == "Ax":
            result = Ax(mt,x)
        elif what == "AExn":
            result = AExn(mt,x,n)
        elif what == "nEx":
            result = nEx(mt,x,n)
        else:
            result = "Unknow function in column E"

        lst.append(result)

    dfp.loc[:,"Result"] = 0
    dfp["Result"] = lst
    dfp.set_index('id', inplace = True , drop = True)

    dfp.to_excel(settings.MEDIA_ROOT + "//" + 'results.xlsx')

    return None





def prepare_esg(cur, yr, no_sc, sig, IR_scens):
    try:
        shutil.rmtree( ROOT+"//output//")
        os.mkdir(ROOT+"//output//")
    except:
        os.mkdir(ROOT+"//output//")


    run0   = 1
    cRun   = "RUN_"
    cMonth = "Month"
    cpOK   = 0.7

    swapR_pd = {}

    relCs = []
    i = 0
    for x in cur:
            relCs.append( curr_adv[ x[0] ])

    with open( settings.MEDIA_ROOT + "//" 'dupa.txt', 'w') as destination:
        for x in relCs:
            destination.write(x)
            destination.write("\n")


    #irScens =  ["BE"] #["BE","UP","DOWN"]
    irScens = []
    for x in IR_scens:
        irScens.append( x[0] )


    curr_used = [currD[x] for x in relCs]
    curr_used_fwr = ["FWR " + s for s in curr_used]

    SWP_Cs = [currD[co] for co in relCs]
    FWR_Cs = ["FWR "+curr for curr in SWP_Cs]


    #Konfiguration
    Y           = yr
    M           = 12
    NofY        = 150 # len(swapR_BE) # 150
    daysInYear  = 252
    randomseed  = "generate&optimize" # alternative is value: eg. 665255393 or -665255393 or dictionary
    excelOut    = False




    for i,io in [["//input","//output"]]:
        if not os.path.exists(ROOT+io):
            os.makedirs(ROOT+io)

    eiopaSWRfn_temp = os.path.join(ROOT+"//input","EIOPA_RFR_{0:%Y%m%d}_Term_Structures.xlsx")
    stochSWRfn_temp = os.path.join(ROOT+"//output","STOCH_RFR_{0:%Y%m%d}_Forward_rates.xlsx")

    closingDate  = date(Y,M,calendar.monthrange(Y,M)[1])
    eiopaSWRfn   = eiopaSWRfn_temp.format(closingDate)
    stochSWRfn   = stochSWRfn_temp.format(closingDate)

    for scen in irScens:
        swapR_pd[scen]=pd.read_excel(eiopaSWRfn,sheetname=scenD[scen],skiprows=1,index_col=None)[8:].set_index("Main menu")
        swapR_pd[scen].index.name="Year"
        swapR_pd[scen]=swapR_pd[scen][relCs]
        swapR_pd[scen].rename(columns=currD,inplace=True)
        swapR_pd[scen]=swapR_pd[scen].join(pd.DataFrame(columns=FWR_Cs))

        # Create Forward Rates:
        swapR_pd[scen][FWR_Cs]=(
            (1+swapR_pd[scen][SWP_Cs].values)**(np.array([swapR_pd[scen].index.tolist()]).transpose())/
            (1+np.append(np.array([len(FWR_Cs)*[0]]),swapR_pd[scen][SWP_Cs].values,axis=0))[:-1]**((np.array([swapR_pd[scen].index.tolist()])-1).transpose())
             -1
        )

    seeds=pd.DataFrame(columns=["Random Seed","Applied"])
    seeds.index.name="SCEN:Currency"

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    if excelOut:
        writer = pd.ExcelWriter(stochSWRfn, engine='xlsxwriter')

    for i,scen in enumerate(irScens):
        for j,curr in enumerate(FWR_Cs):
            repeat = True
            irep = 0
            while repeat:

                if (isinstance(randomseed,(str)) and (randomseed.lower().find("gen") == 0 or randomseed.lower().find("rand") == 0)
                    and ( (randomseed.lower().find("@start")>-1 and i+j==0) or randomseed.lower().find("@start")<0)
                   ):
                    rseed=np.random.randint(2**31-1)
                    # Set random seed
                    np.random.seed(rseed)
                    sseed = "Randomly generated seed {:}".format("at start only" if randomseed.lower().find("@start")>-1 else "individually")
                    sapp  = "{:}".format("START" if randomseed.lower().find("@start")>-1 else "OWN")

                elif isinstance(randomseed,dict):
                    rseed=randomseed[scen+":"+curr[4:]]
                    # Set random seed
                    np.random.seed(rseed)
                    sseed = "Seed set from input dict table to "+str(rseed)
                    sapp  = "OWN"
                elif isinstance(randomseed,pd.DataFrame):
                    if randomseed.loc[scen+":"+curr[4:],"Applied"]=="OWN" or (randomseed.loc[scen+":"+curr[4:],"Applied"]=="START" and i+j ==0):
                        rseed=randomseed.loc[scen+":"+curr[4:],"Random Seed"]
                        # Set random seed
                        np.random.seed(rseed)
                        sseed = "Seed set from input frame table to "+str(rseed)
                    else:
                        rseed = "NO (RE)SETTNG"
                        sseed = "NO seed (re)setting"
                    sapp  = randomseed.loc[scen+":"+curr[4:],"Applied"]
                elif isinstance(randomseed,int) and randomseed > 0 and i+j==0:
                    rseed=randomseed
                    # Set random seed
                    np.random.seed(rseed)
                    sseed = "Seed set at start to "+str(randomseed)
                    sapp  = "START"
                elif isinstance(randomseed,int) and randomseed < 0:
                    rseed=-randomseed
                    # Set random seed
                    np.random.seed(rseed)
                    sseed = "Seed individually reset to "+str(-randomseed)
                    sapp  = "OWN"
                else:
                    rseed = "NO (RE)SETTNG"
                    sseed = "NO seed (re)setting"
                    sapp  = "START"

                # set central monthly drift
                deltaRF_Y   = np.log(1.0+swapR_pd[scen][curr].values.astype(np.float_)) # here stil Annual -> Dayli
                if NofY != len(swapR_pd[scen]):
                    NofY = len(swapR_pd[scen])


                deltaRF_M   = deltaRF_Y/12.0
                daysInMonth = daysInYear/12
                sig_D       = sig / daysInYear**(1./2.)
                sig_M       = sig / 12.0**(1./2.)

                # Generate monthly Normal random Vectors
                randomV_M   = np.random.normal(0,sig_M,(12*NofY,no_sc))

                # Generate monthly random log returns
                logR_M      = np.exp(np.array([12*[mu] for mu in deltaRF_M]).reshape(12*len(deltaRF_M),1) - sig_M**2/2.0 + randomV_M)-1
                fwRates_M_t = np.mean(logR_M, axis=1)
                fwRates_M   = np.exp(np.array([12*[mu] for mu in deltaRF_M]).reshape(12*len(deltaRF_M),1))-1

                # Statistical tests
                stochFwSet=((1+logR_M)/(1+fwRates_M)-1).flatten()
                pr4 = 2*(1 - scipy.stats.norm.cdf(np.sqrt(len(stochFwSet))*abs(np.mean(stochFwSet))/np.std(stochFwSet)))
                scolor = "steelblue" if pr4 < cpOK else "seagreen"

                plt.title("Mean stoch. forward rate (logR int, month dt) ",fontsize=12)
                plt.plot(np.array(range(NofY*12)),fwRates_M_t.transpose(),color=scolor)
                plt.plot(np.array(range(NofY*12)),fwRates_M.flatten(),color="orange")
                temp_name= ROOT+"//output//Mean stoch forward rate_"+ scen + "_"+ curr + ".png"
                plt.savefig(temp_name)

                plt.title("Stoch fwr distribution (disc, logR int, month dx)",fontsize=12)
                plt.hist(stochFwSet,bins=50,color=scolor)
                temp_name= ROOT+"//output//Stoch fwr distribution (disc, logR int, month dx)" + scen + "_"+ curr + ".png"
                plt.savefig(temp_name)

                if pr4 < cpOK and isinstance(randomseed,(str)) and randomseed.lower().find("&opt") > -1:
                    irep+=1
                else:
                    seeds.loc[scen+":"+curr[4:],"Random Seed"] = rseed
                    seeds.loc[scen+":"+curr[4:],"Applied"]     = sapp
                    repeat=False

            tmpRates = pd.DataFrame(columns=[cRun+str(run0+run) for run in range(no_sc)],index=range(1,12*NofY+1))
            tmpRates.index.name=cMonth
            tmpRates.loc[tmpRates.index,:]=logR_M


            if excelOut:
                tmpRates.to_excel(writer, sheet_name=scen+" for "+curr,float_format='%.14f')

            csvOut =  stochSWRfn.replace(".xlsx","-"+scen+"_"+curr+".csv")

            tmpRates.to_csv(csvOut, sep=';' , float_format='%.14f')

            #transform in FAC
            f = open(os.path.join(ROOT+"//output","Stochastic_ForwardRates"+(("_"+scen) if scen != "BE" else "")+"_"+curr.replace("FWR ","")+".FAC"), 'w')
            f.write('{:}\n'.format(no_sc)) #write number of columns in the first row -> prophet format
            tmpRates.insert(0,"Month",np.arange(1,len(tmpRates)+1))
            tmpRates.insert(0,"!","*")
            tmpRates.to_csv(f, sep=',', index=False, quoting=csv.QUOTE_NONE,float_format='%.14f')#, mode='a'), index=None
            f.close()

        #save deterministic Forward Rates als FAC
        f = open(os.path.join(ROOT+"//output","ForwardRates"+(("_"+scen) if scen != "BE" else "")+".FAC"), 'w')
        FWR=pd.DataFrame(swapR_pd[scen][curr_used_fwr])
        FWR.columns=curr_used
        f.write('{:}\n'.format(no_sc))  #write a number of columns in the first row -> prophet format
        FWR.insert(0,"Year",np.arange(1,len(FWR)+1))
        FWR.insert(0,"!","*")
        FWR.to_csv(f, sep=',', index=False, quoting=csv.QUOTE_NONE,float_format='%.14f')#, mode='a'), index=None
        f.close()

        #save deterministic Swap Rates as FAC
        f = open(os.path.join(ROOT+"//output","SwapRates"+(("_"+scen) if scen != "BE" else "")+".FAC"), 'w')
        SWR=pd.DataFrame(swapR_pd[scen][curr_used])
        SWR.columns=curr_used
        f.write('{:}\n'.format(no_sc)) #write a number of columns in the first row -> prophet format
        SWR.insert(0,"Year",np.arange(1,len(SWR)+1))
        SWR.insert(0,"!","*")
        SWR.to_csv(f, sep=',', index=False, quoting=csv.QUOTE_NONE,float_format='%.14f')#, mode='a'), index=None
        f.close()

    # Close the Pandas Excel writer and output the Excel file.
    if excelOut:
        writer.save()

    shutil.make_archive(ROOT+"//zipped_output", "zip", ROOT+"//output")
    return None

'''
################################################################################
################################################################################
##############################     VASICEK MODEL    ############################
################################################################################
################################################################################
################################################################################

'''

def VasicekNextRate(r, kappa, theta, sigma, dt=1/252):
    # Implements above closed form solution

    val1 = np.exp(-1*kappa*dt)
    val2 = (sigma**2)*(1-val1**2) / (2*kappa)
    out = r*val1 + theta*(1-val1) + (np.sqrt(val2))*np.random.normal()
    return out

def VasicekSim(N, r0, kappa, theta, sigma, dt = 1/252):
    short_r = [0]*N # Create array to store rates
    short_r[0] = r0 # Initialise rates at $r_0$


    for i in range(1,N):
        short_r[i] = VasicekNextRate(short_r[i-1], kappa, theta, sigma, dt)

    return short_r

def VasicekMultiSim(M, N, r0, kappa, theta, sigma, dt = 1/252):
    sim_arr = np.ndarray((N, M))

    for i in range(0,M):
        sim_arr[:, i] = VasicekSim(N, r0, kappa, theta, sigma, dt)

    return sim_arr

def VasicekCalibration(rates, dt=1/252):
    n = len(rates)

    # Implement MLE to calibrate parameters
    Sx = sum(rates[0:(n-1)])
    Sy = sum(rates[1:n])
    Sxx = np.dot(rates[0:(n-1)], rates[0:(n-1)])
    Sxy = np.dot(rates[0:(n-1)], rates[1:n])
    Syy = np.dot(rates[1:n], rates[1:n])

    theta = (Sy * Sxx - Sx * Sxy) / (n * (Sxx - Sxy) - (Sx**2 - Sx*Sy))
    kappa = -np.log((Sxy - theta * Sx - theta * Sy + n * theta**2) / (Sxx - 2*theta*Sx + n*theta**2)) / dt
    a = np.exp(-kappa * dt)
    sigmah2 = (Syy - 2*a*Sxy + a**2 * Sxx - 2*theta*(1-a)*(Sy - a*Sx) + n*theta**2 * (1-a)**2) / n
    sigma = np.sqrt(sigmah2*2*kappa / (1-a**2))
    r0 = rates[n-1]

    return [kappa, theta, sigma, r0]



def prepare_vasicek(no_sc, vector_length, start_rate,alpha, beta,  sig, IRscs):
    # configuration
    excelOut    = True
    curr = "xxx"
    scen ="BE"
    run0   = 1
    cRun   = "RUN_"
    cMonth = "Month"
    cpOK   = 0.7
    NofY = vector_length

    arr_with_rates = VasicekMultiSim(M = no_sc, N = vector_length, r0 = start_rate, kappa = alpha, theta = beta, sigma = sig, dt = 1/252)

    tmpRates = pd.DataFrame(columns=[cRun+str(run0+run) for run in range(no_sc)],index=range(1,NofY+1))
    tmpRates.index.name=cMonth
    tmpRates.loc[tmpRates.index,:]= arr_with_rates


    if excelOut:
        tmpRates.to_excel(ROOT+"//output//vasicek.xlsx")

    #csvOut =  stochSWRfn.replace(".xlsx","-"+scen+"_"+curr+".csv")

    #tmpRates.to_csv(csvOut, sep=';' , float_format='%.14f')

    #transform in FAC
    f = open(os.path.join(ROOT+"//output","Stochastic_ForwardRates"+(("_"+scen) if scen != "BE" else "")+"_"+curr.replace("FWR ","")+".FAC"), 'w')
    f.write('{:}\n'.format(no_sc)) #write number of columns in the first row -> prophet format
    tmpRates.insert(0,"Month",np.arange(1,len(tmpRates)+1))
    tmpRates.insert(0,"!","*")
    tmpRates.to_csv(f, sep=',', index=False, quoting=csv.QUOTE_NONE,float_format='%.14f')#, mode='a'), index=None
    f.close()

    return None

def calib_and_generate_vasicek(no_sc, vector_length,year, currency, whichrates, customrates, IRscs):
    try:
        shutil.rmtree( ROOT+"//output")
        os.mkdir(ROOT+"//output")
    except:
        os.mkdir(ROOT+"//output")
    #configuration
    Y = year
    M = 12
    relCs = []
    i = 0
    curr = []
    curr.append(currency)
    for x in curr:
            relCs.append( curr_adv[x])

    SWP_Cs = [currD[co] for co in relCs]
    FWR_Cs = ["FWR "+ crx for crx in SWP_Cs]

    irScens = []
    for x in IRscs:
        irScens.append( x[0] )

    if whichrates =="EIOPA":
        eiopaSWRfn_temp = os.path.join(ROOT+"//input","EIOPA_RFR_{0:%Y%m%d}_Term_Structures.xlsx")
        stochSWRfn_temp = os.path.join(ROOT+"//output","STOCH_RFR_{0:%Y%m%d}_Forward_rates.xlsx")

        closingDate  = date(Y,M,calendar.monthrange(Y,M)[1])
        eiopaSWRfn   = eiopaSWRfn_temp.format(closingDate)
        stochSWRfn   = stochSWRfn_temp.format(closingDate)
        swapR_pd = {}


        for scen in irScens:
            swapR_pd[scen]=pd.read_excel(eiopaSWRfn,sheetname=scenD[scen],skiprows=1,index_col=None)[8:].set_index("Main menu")
            swapR_pd[scen].index.name="Year"
            swapR_pd[scen]=swapR_pd[scen][relCs]
            swapR_pd[scen].rename(columns=currD,inplace=True)
            swapR_pd[scen]=swapR_pd[scen].join(pd.DataFrame(columns=FWR_Cs))

            # Create Forward Rates:
            swapR_pd[scen][FWR_Cs]=(
                (1+swapR_pd[scen][SWP_Cs].values)**(np.array([swapR_pd[scen].index.tolist()]).transpose())/
                (1+np.append(np.array([len(FWR_Cs)*[0]]),swapR_pd[scen][SWP_Cs].values,axis=0))[:-1]**((np.array([swapR_pd[scen].index.tolist()])-1).transpose())
                    -1
                )

            #print(swapR_pd["BE"][FWR_Cs], file = printlog)
            #print('n/', file = printlog)
        df = swapR_pd["BE"][FWR_Cs]
        rates = df["FWR CHF"].tolist()
            # FWR CHF
            #rates = nprates
            #print(rates, file = printlog)

        params = VasicekCalibration(rates, dt=1/252)

    else:
        rates = swapR_pd["BE"][FWR_Cs]
        params = VasicekCalibration(rates, dt=1/252)

    print(params[0], file = printlog)
    print('n/', file = printlog)

    print(params, file = printlog)
    print('n/', file = printlog)
    prepare_vasicek(no_sc, vector_length, params[3],params[0], params[1],  params[2], IRscs)
    shutil.make_archive(ROOT+"//zipped_output", "zip", ROOT+"//output")
    printlog.close()
    return None

def generate_only_vasicek(no_sc, vector_length, start_rate,alpha, beta,  sig, IRscs):
    try:
        shutil.rmtree( ROOT+"//output//")
        os.mkdir(ROOT+"//output//")
    except:
        os.mkdir(ROOT+"//output//")
    prepare_vasicek(no_sc, vector_length, start_rate,alpha, beta,  sig, IRscs)
    shutil.make_archive(ROOT+"//zipped_output", "zip", ROOT+"//output")
    return None
