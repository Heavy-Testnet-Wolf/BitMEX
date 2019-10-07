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

def seconds2str(seconds):
    seconds = round(seconds)
    h = seconds//(60*60)
    m = (seconds-h*60*60)//60
    s = seconds-(h*60*60)-(m*60)
    if h > 0:
        return num2strPostFix(h,'hour')+' and '+num2strPostFix(m,'minute')
    if m > 0:
        return num2strPostFix(m,'minute')+' and '+num2strPostFix(s,'second')
    return num2strPostFix(s,'second')

def num2strPostFix(number,string):
    if abs(number) != 1:
        string += 's'
    return str(number)+' '+string

def extractSubstring(raw_string, start_marker, end_marker):
    start = raw_string.find(start_marker) + len(start_marker)
    end = raw_string.find(end_marker, start)
    if start == -1 or end == -1:
        return ''
    return raw_string[start:end]

def extractSubstringFromRight(raw_string, start_marker, end_marker):
    start = raw_string.rfind(start_marker) + len(start_marker)
    end = raw_string.rfind(end_marker, start)
    if start == -1 or end == -1:
        return ''
    return raw_string[start:end]
