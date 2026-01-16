class Logger:

    def __init__(self, logfile: str = '/tmp/cranix.log'):

        self.log_file = open(logfile, "w")
        self.debug = self.check_cranixconfig()

    @staticmethod
    def debug(msg: str):
        if debug:
            print(msg)

    @staticmethod
    def error(msg: str):
        print(msg)

    @staticmethod
    def log(msg: str):
        log_file.write(msg)

    @staticmethod
    def print_error(msg):
        return '<tr><td colspan="2"><font color="red">{0}</font></td></tr>\n'.format(msg)

    @staticmethod
    def print_msg(title, msg):
        return '<tr><td>{0}</td><td>{1}</td></tr>\n'.format(title,msg)

    @staticmethod
    def check_cranixconfig() -> bool:
        try:
            import cranixconfig
            return cranixconfig.CRANIX_DEBUG.lower() == "yes"
        except:
            return True