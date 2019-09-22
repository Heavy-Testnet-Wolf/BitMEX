def clearConsole():
    print(u"{}[2J{}[;H".format(chr(27), chr(27)))

def roundExact(number,decimal_places=0):
    # Round number to given number of decimal places
    factor = 10**(decimal_places + 1)
    rounded_int = int(number * factor)
    if rounded_int % 10 >= 5:
        return (int(rounded_int//10) + 1) / float(factor//10)
    return int(rounded_int//10) / float(factor//10)

def btc2str(number,unit='XBT'):
    # Convert a bitcoin price to a string
    s = '{0:.8f}'.format(number)
    return (s[0:10]).rstrip('0').rstrip('.')

def pct2str(number,decimals=2):
    # Convert a percentage to a string
    return str(roundExact(number,decimals))