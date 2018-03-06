from metar import Metar

Original_kt = 3
Original_W_k = 3* math.log(6/0.0984)/math.log(10/0.0984)
Original_W_k_MF = 3* math.log(6,0.0984)/math.log(10,0.0984)
tenpdown_w = 3* 0.9* math.log(6/0.0984)/math.log(10/0.0984)
print "Wind in knots from report:                  ",Original_kt
print "Wind in knots with Corey's method:          ",Original_W_k
print "Wind in knots 10% down with Corey's method: ",tenpdown_w
print "Wind in knots With the Math.log base method:",Original_W_k_MF

Original_W_MPH = 3*1.15077944802
Original_W_MPH_COREY = 3*1.15077944802 * math.log(6/0.0984)/math.log(10/0.0984)
Original_W_MPH_COREY_MF = 3*1.15077944802 * math.log(6,0.0984)/math.log(10,0.0984)
print "Wind in MPH without Corey's method:         ",Original_W_MPH
print "Wind in MPH with Corey's method:            ",Original_W_MPH_COREY
print "Wind in MPH With the Math.log base changed: ",Original_W_MPH_COREY_MF

report = 'KDHT 131753Z AUTO VRB03KT 8SM CLR 26/04 A3016 RMK AO2 SLP170 T02560044 10256 20072 58004'
X=Metar.Metar(report)
#print X.string()




