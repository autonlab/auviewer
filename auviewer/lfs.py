

def SvO2_mean_condition(pig):
    target = min(pig['baseline_SvO2'], 65)
    target = max(target, 60)
    
    if pig['SvO2_mean [2 min]'] >= target:
        return 1
    else:
        return 0

def HR_mean_upperbound(pig):
    if pig['HR_mean [2 min]'] < 110:
        return 1
    else:
        return 0