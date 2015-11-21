# Intended for use by top level scripts like cumin, cumin-web and cumin-data
# for reporting errors during startup.
class CuminErrors(object):
    NO_ERROR = 0
    PARSE_ERROR = 1
    UNHANDLED_ERROR = 2
    DATABASE_ERROR = 3
    SCHEMA_ERROR = 4
    SCHEMA_VER_ERROR = 5
    WEB_SERVER_ERROR = 6
    CERTIFICATE_ERROR = 7

    errors = \
     {NO_ERROR: ("no error", "normal operation"),
      PARSE_ERROR: \
          ("parse error", 
           "error in options, arguments, or config values"),
      UNHANDLED_ERROR: \
          ("unhandled error",
           "*.stderr or *.stdout logs may contain details"),
      DATABASE_ERROR: \
          ("database error", 
           "run 'cumin-database check' as root for more information"),
      SCHEMA_ERROR: \
          ("schema error", 
           "run 'cumin-admin create-schema' as root"),
      SCHEMA_VER_ERROR: \
          ("schema version error", 
           "run 'cumin-admin upgrade-schema' as root"),
      WEB_SERVER_ERROR: \
          ("web server error", 
           "web server process has exited"),
      CERTIFICATE_ERROR: \
          ("certificate error", 
           "certificate or key file is not a valid file or is unreadable")
     }

    @classmethod
    def translate(cls, status):
        s = status
        # low bit indicates wheter error was during init or not.
        # shift right for value (if it's not a signal)
        if s > 0:
            s = s >> 1
        if s in CuminErrors.errors:
            return CuminErrors.errors[s]
        elif s < 0:
            return ("received a signal", "unhandled") 
        else:
            return ("unrecognized error", "check logs for details")
