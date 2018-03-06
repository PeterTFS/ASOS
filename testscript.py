
#Here is part of what I was testing at one time
import os
import csv

#define your workspace
ws = ""

#input percentile table, will need to change path
infile1 = os.path.join(ws, "ec_percentile_range.csv")
infile2 = os.path.join(ws, "hu_hr_percentile_range.csv")
infile3 = os.path.join(ws, "ten_hr_percentile_range.csv")
infile4 = os.path.join(ws, "th_hr_percentile_range.csv")

filteredcsv = os.path.join(ws, "tx_nfdr_obs_2015060223.csv")
		
with open(infile1) as ec_perc, open(infile2) as hu_perc, open(infile3) as ten_perc, open(infile4) as th_perc, open(filteredcsv) as filt_csv:
	
	reader1 = csv.DictReader(ec_perc)
	reader2 = csv.DictReader(hu_perc)
	reader3 = csv.DictReader(ten_perc)
	reader4 = csv.DictReader(th_perc)
	reader5 = csv.DictReader(filt_csv)
	
	myDict1 = list(reader1)
	myDict2 = list(reader2)
	myDict3 = list(reader3)
	myDict4 = list(reader4)
	myDict5 = list(reader5)

#Testing with erc percentile and observations
sortmyDict1 = sorted(myDict1, key=lambda k: k['sta_id'])
sortmyDict5 = sorted(myDict5, key=lambda k: k['sta_id'])

keys_a = set(item['sta_id'] for item in myDict1)
keys_b = set(item['sta_id'] for item in myDict5)
intersection = keys_a & keys_b

# functions to reclassify fire danger, ten hour percentile, hundred hour percentile, thousand hour percentile, and dryness
def adj_reclass(adj):
    if adj == 'L':
        return 1
    elif adj == 'M':
        return 2
    elif adj == 'H':
        return 3
    elif adj == 'V':
        return 4
    elif adj == 'E':
        return 5

def ten_percentile(ten_hr, C97, C90_96, C75_89, C50_74, C0_49):
    if ten_hr <= C97:
        return 1
    elif ten_hr < C75_89:
        return 2
    elif ten_hr < C50_74:
        return 3
    elif ten_hr < C0_49:
        return 4
    else:
        return 5

def hu_percentile(hu_hr, C3, C4_10 , C11_25, C26_50, C51_100):
    if hu_hr <= C3:
        return 1
    elif hu_hr < C11_25:
        return 2
    elif hu_hr < C26_50:
        return 3
    elif hu_hr < C51_100:
        return 4
    else:
        return 5

def th_percentile(th_hr, C97, C90_96, C75_89, C50_74, C0_49):
    if th_hr <= C97:
        return 1
    elif th_hr < C75_89:
        return 2
    elif th_hr < C50_74:
        return 3
    elif th_hr < C0_49:
        return 4
    else:
        return 5

def ec_percentile(ec, C97, C90_96, C75_89, C50_74, C0_49):
    if ec >= C97:
        return 5
    elif ec >= C90_96:
        return 4
    elif ec >= C75_89:
        return 3
    elif ec >= C50_74:
        return 2
    else:
        return 1

def dryness(hu_hr_p, ec_p):
    if hu_hr_p == 5 and ec_p == 1:
        return 1
    elif hu_hr_p <= 4 and ec_p == 1:
        return 2
    elif hu_hr_p >= 3 and ec_p == 2:
        return 2
    elif hu_hr_p <= 2 and ec_p == 2:
        return 3
    elif hu_hr_p == 5 and ec_p == 3:
        return 2
    elif hu_hr_p <= 4 and ec_p == 3:
        return 3
    elif hu_hr_p >= 3 and ec_p == 4:
        return 3
    elif hu_hr_p <= 2 and ec_p == 4:
        return 4
    elif hu_hr_p >= 3 and ec_p == 5:
        return 3
    elif hu_hr_p == 2 and ec_p == 5:
        return 4
    elif hu_hr_p == 1 and ec_p == 5:
        return 5
    else :
        return 100
		
		