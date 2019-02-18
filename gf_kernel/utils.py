def to_display_data(message,omdoc=None):
    """wraps the message into the display_data format"""
    if(omdoc):
        return {
            'data': {
                'text/plain': message,
                'application/omdoc' : omdoc
            },
            'metadata': {},
            'transient': {},
        }
    else:
        return {
            'data': {
                'text/plain': message,
            },
            'metadata': {},
            'transient': {}
        }

def readFile(fn, cursor_pos=0):
    """Reads the file with name `fn` starting at `cursor_pos`"""
    fd = open(fn, 'r')
    fd.seek(cursor_pos)
    line = fd.readline()
    out = ""
    while line:
        if line != '\n':
            out += line
        line = fd.readline()
    fd.close()
    return out