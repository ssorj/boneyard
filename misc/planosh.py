class PlanoShellCommand(BaseCommand):
    def __init__(self):
        self.parser = BaseArgumentParser()
        self.parser.add_argument("file", metavar="FILE", nargs="?",
                                 help="Read program from FILE")
        self.parser.add_argument("arg", metavar="ARG", nargs="*",
                                 help="Program arguments")
        self.parser.add_argument("-c", "--command",
                                 help="A program passed in as a string")
        self.parser.add_argument("-i", "--interactive", action="store_true",
                                 help="Operate interactively after running the program (if any)")

    def parse_args(self, args):
        return self.parser.parse_args(args)

    def init(self, args):
        self.file = args.file
        self.interactive = args.interactive
        self.command = args.command

    def run(self):
        stdin_isatty = _os.isatty(_sys.stdin.fileno())
        script = None

        if self.file == "-": # pragma: nocover
            script = _sys.stdin.read()
        elif self.file is not None:
            try:
                with open(self.file) as f:
                    script = f.read()
            except IOError as e:
                raise PlanoError(e)
        elif not stdin_isatty: # pragma: nocover
            # Stdin is a pipe
            script = _sys.stdin.read()

        if self.command is not None:
            exec(self.command, globals())

        if script is not None:
            global ARGS
            ARGS = ARGS[1:]

            exec(script, globals())

        if (self.command is None and self.file is None and stdin_isatty) or self.interactive: # pragma: nocover
            repl(locals=globals())

@test
def planosh_command():
    with working_dir():
        write("script1", "garbage")

        with expect_exception(NameError):
            PlanoShellCommand().main(["script1"])

        write("script2", "print_env()")

        PlanoShellCommand().main(["script2"])

        PlanoShellCommand().main(["--command", "print_env()"])

    with expect_system_exit():
        PlanoShellCommand().main(["no-such-file"])
