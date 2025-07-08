def state_of_charge(voltage):
    pct_charged = round((float(voltage) - 3) / 0.012, 2)
    if pct_charged >= 88:
        return 100.0
    elif pct_charged >= 85:
        return 95.0
    elif pct_charged >= 83:
        return 90.0
    elif pct_charged >= 10:
        return pct_charged
    return 1.0
