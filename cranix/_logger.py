try:
    import cranixconfig
    debug = cranixconfig.CRANIX_DEBUG.lower() == "yes"
except:
    debug = True

class Logger:
    log_file = ""
    def __init__(self, logfile: str = '/tmp/cranix.log'):
        global log_file
        log_file = open(logfile,"w")

    def debug(msg: str):
        if debug:
            print(msg)

    def error(msg: str):
        print(msg)

    def log(msg: str):
        log_file.write(msg)

    def print_error(msg):
        return '<tr><td colspan="2"><font color="red">{0}</font></td></tr>\n'.format(msg)

    def print_msg(title, msg):
        return '<tr><td>{0}</td><td>{1}</td></tr>\n'.format(title,msg)


