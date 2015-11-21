class Command(object):
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.aliases = ()
        self.arguments = ()
        self.description = None

        self.options = list()
        self.options_by_param = dict()

        self.commands = list()
        self.commands_by_name = dict()

        opt = CommandOption(self, "help", "h")
        opt.description = "Print this message"

        if self.parent:
            self.parent.commands.append(self)
            self.parent.commands_by_name[self.name] = self

    def init(self):
        if self.parent:
            for alias in self.aliases:
                self.parent.commands_by_name[alias] = self

        for option in self.options:
            option.init()

        for command in self.commands:
            command.init()

    def parse_options(self, argv):
        opts = dict()
        opt = None
        remaining = list()

        def find_opt(key):
            try:
                opt = self.options_by_param[key]
                opts[opt.name] = None
                return opt
            except KeyError:
                msg = "Option '%s' is unrecognized" % key
                raise CommandException(self, msg)

        for i, arg in enumerate(argv):
            if arg.startswith("--"):
                opt = find_opt(arg[2:])
            elif arg.startswith("-"):
                opt = find_opt(arg[1])
            elif opt:
                if opt.argument:
                    opts[opt.name] = opt.unmarshal(arg)
                    opt = None
                else:
                    remaining = argv[i:]
                    break
            else:
                remaining = argv[i:]
                break

        return opts, remaining

    def parse(self, argv):
        opts = dict()
        args = list()
        opt = None

        def find_opt(key):
            try:
                opt = self.options_by_param[key]
                opts[opt.name] = True
                return opt
            except KeyError:
                msg = "Option '%s' is unrecognized" % key
                raise CommandException(self, msg)

        for arg in argv:
            if arg.startswith("--"):
                opt = find_opt(arg[2:])
            elif arg.startswith("-"):
                opt = find_opt(arg[1])
            elif opt:
                if opt.argument:
                    opts[opt.name] = opt.unmarshal(arg)
                    opt = None
                else:
                    args.append(arg)
            else:
                args.append(arg)

        return opts, args

    def print_help(self):
        usage = list()

        if self.parent:
            usage.append(self.parent.name)

        usage.append(self.name)

        if self.options:
            usage.append("[OPTIONS]")

        if self.commands:
            usage.append("COMMAND")
        elif self.arguments:
            usage.extend(self.arguments)

        print "Usage: %s" % " ".join(usage)

        if self.description:
            print "Description: %s" % self.description

        if self.options:
            print "Options:"

            for opt in self.options:
                osummary = "--%s" % opt.name

                if opt.char:
                    osummary = osummary + " (-%s)" % opt.char

                if opt.argument:
                    osummary = osummary + " " + opt.argument

                print "  %-30s  %s" % (osummary, opt.description)

        if self.commands:
            print "Commands:"

            for command in self.commands:
                if command.aliases:
                    names = "%s (%s)" % (command.name, ", ".join(command.aliases))
                else:
                    names = command.name

                print "  %-30s  %s" % (names, command.description)

class CommandOption(object):
    def __init__(self, command, name, char=None):
        self.command = command
        self.name = name
        self.char = char
        self.argument = None
        self.description = None
        self.type = str

        self.command.options.append(self)
        self.command.options_by_param[self.name] = self

    def init(self):
        if self.char:
            self.command.options_by_param[self.char] = self

    def unmarshal(self, value):
        return self.type(value)

class CommandException(Exception):
    def __init__(self, command, message):
        Exception.__init__(self, message)

        self.command = command
