from util import *
try:
    import ldap
    import ldapurl
    have_ldap = True
except:
    have_ldap = False

import subprocess
from subprocess import PIPE
from psycopg2 import IntegrityError
import syslog

# Send sensitive authentication logs to syslog
# but use this for other stuff.  We want to keep
# all user and password information out of the 
# publically readable log file.
log = logging.getLogger("cumin.authenticator")


class _syslog(object):
    log_auth = False
    @classmethod
    def log(cls, msg):
        if _syslog.log_auth:
            syslog.syslog(msg)

class CuminAuthenticatorLDAP(object):
    def __init__(self, url, app):
        self.valid = False
        log.info("Initializing %s", self)
        scheme, myurl = url.split("=",1)
        err_msg = ""

        self.tls_cacertdir = app.ldap_tls_cacertdir
        self.tls_cacertfile = app.ldap_tls_cacertfile
        self.ldap_timeout = app.ldap_timeout
        has_cert = self.tls_cacertdir or self.tls_cacertfile

        if has_cert and not ldap.TLS_AVAIL:
            err_msg = "Authenticator: SSL is not supported by this python-ldap module."

        elif not has_cert and scheme == "ldaps":
            err_msg = "Authenticator: scheme is ldaps but no tls_cacertdir set."

        else:
            if self.tls_cacertdir:
                if not os.path.isdir(self.tls_cacertdir):
                    err_msg = "Authenticator: '%s' is not a valid directory." \
                        % self.tls_cacertdir
                else:
                    try:
                        os.listdir(self.tls_cacertdir)
                    except Exception, e:
                        err_msg = "Authenticator, exception reading " \
                            "tls_cacertdir, %s" % e

            if not err_msg and self.tls_cacertfile:
                if not os.path.isfile(self.tls_cacertfile):
                    err_msg = "Authenticator: '%s' is not a valid file." \
                        % self.tls_cacertfile
                else:
                    try:
                        open(self.tls_cacertfile, "r")
                    except Exception, e:
                        err_msg = "Authenticator, exception reading " \
                            "tls_cacertfile, %s" % e
        if not err_msg:
            # If the scheme is just "ldap" but cert dir is set then we will use
            # the StartTLS mechanism for password binds
            self.start_tls = has_cert and scheme == "ldap"
            if scheme == "ldap":
                log.info("Authenticator: using StartTLS for ldap: %s" % \
                             self.start_tls)  
            try:
                self.url = ldapurl.LDAPUrl(myurl, 
                                           scope=ldapurl.LDAP_SCOPE_SUBTREE,
                                           filterstr="uid=%s")
                log.info("Authenticator: parsed LDAP url successfully, " \
                             "scheme is %s" % scheme)
                self.valid = True
            except Exception,e:
                err_msg = "Authenticator: cannot parse LDAP url %s" % e

        if err_msg:
            log.error(err_msg)

    def _set_ldap_options(self):
        if self.tls_cacertdir:
            ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, self.tls_cacertdir)

        if self.tls_cacertfile:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.tls_cacertfile)

        if self.tls_cacertfile or self.tls_cacertdir:
            # Always demand a certificate if the cacert is set
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)

    def _start_tls(self, conn):
        if self.start_tls and not conn.start_tls_called:
            conn.start_tls_called = True
            log.debug("Authenticator: calling conn.start_tls_s() on ldap connection")
            try:
                conn.start_tls_s()
            except Exception, e:
                log.error("Authenticator: StartTLS failed, %s" % e)
                return False
        return True

    def __prep_con(self):
        try:
            self._set_ldap_options()
            conn = ldap.initialize(self.url.urlscheme + "://" +self.url.hostport)
            if self.ldap_timeout is not None:
                # ldap.set_option(OPT_TIMEOUT, val) doesn't seem to work on 
                # older versions of python_ldap.  Instead, you have to set the
                # value explicitly on the connection object after creation.
                conn.timeout = self.ldap_timeout
            conn.start_tls_called = False
        except Exception,e:
            log.error("Authenticator: cannot contact ldap server %s",e)
            return False

        if self.url.who and self.url.cred:
            if not self._start_tls(conn):
                return False
            try:
                conn.simple_bind_s(self.url.who, self.url.cred)
            except:
                log.error("Authenticator: cannot authenticate as service %s", 
                          self.url.who)
                return False
        return conn

    def _gen_filter(self, filterstr, value):
        count = filterstr.count("%s")
        if count > 0:
            vals = (value,) * count
            return filterstr % vals
        return filterstr

    def _find_user(self, user):
        res = False
        conn = self.__prep_con()
        if conn:
            filter = self._gen_filter(self.url.filterstr, user)
            try:
                res = conn.search_s(self.url.dn, self.url.scope, filter)
            except Exception, e:
                msg = str(e)
                if not msg:
                    msg = repr(e)
                log.error("Authenticator: find_user, "\
                          "query returned exception %s" % msg)
        return conn, res

    def find_user(self, user):
        conn, res = self._find_user(user)
        if res:
            return True
        return False

    def change_pw(self, user, oldpass, newpass):
        conn, res = self._find_user(user)
        if not res:
           log.info("Authenticator: update password, "\
                    "query returned no results in %s", self.__class__.__name__)
        else:
            res = False
            if self._start_tls(conn):
                dn,ent = res[0]
                conn.simple_bind_s(dn,oldpass)
                conn.passwd_s(dn,oldpass,newpass)
                log.info("Authenticator: update password succeeded in %s", 
                         self.__class__.__name__)
                _syslog.log("cumin: updated password via LDAP for user %s" % dn)
                res = True
        return res

    def batch_import(self):
        log.debug("Authenticator: batch import in %s", self.__class__.__name__)
        userlist = res = []
        conn = self.__prep_con()
        error = not conn
        if not error:
            filter = self._gen_filter(self.url.filterstr, "*")
            try:
                res = conn.search_s(self.url.dn, self.url.scope, filter)
            except Exception, e:
                log.error("Authenticator:, batch import, "\
                          "query returned exception %s", e) 
                error = True
        if not res:
            log.info("Authenticator: batch import failed, "\
                     "query returned no results in %s", self.__class__.__name__)
        else:
            for dn,ent in res:
                dn_arr = ldap.dn.explode_rdn(dn)
                naming_attr = dn_arr[0].split('=')[0]
                userlist.append(ent[naming_attr][0])
        return userlist, error

    def authenticate(self, username, password):
        log.debug("Authenticating against %s", self.__class__.__name__)
        conn, res = self._find_user(username)
        if not res:
            log.info("Authenticator: authentication failed, "\
                     "query returned no results in %s", self.__class__.__name__)
        else:
            # We need to check for zero length passwords here and disallow.
            # This is because an LDAP directory server MAY allow unauthenticated
            # binds, which are indicated by a zero length password.  Red Hat Directory 
            # Services turns unauthenticated binds off by default, for example,
            # but who knows how this particular server may be configured? 

            # If unauthenticated binds are allowed by the server, then simple_bind_s 
            # below will succeed with a zero lengh password and cumin will think that 
            # password authentication has succeeded when it really hasn't.
            if password == "":
                log.error("Authenticator: zero length password is not allowed for "\
                              "ldap users")
                return False

            if self._start_tls(conn):
                for dn,ent in res:
                    try:
                        conn.simple_bind_s(dn,password)
                        _syslog.log("cumin: authenticated user %s via LDAP" % dn)
                        return True
                    except Exception, e:
                        log.info("Authenticator: LDAP authentication "\
                                     "returned exception %s" % e)
        return False

class CuminAuthenticatorScript(object):
    def __init__(self, commandline, *args):
        self.valid = False
        self.params = {}
        self.cap = []
        me = self.__class__.__name__
        for a in commandline.split(','):
            # Allow capability with a null value
            args = a.split('=')
            if len(args) == 1:
                args.append("")
            param,val = args
            self.params[param] = val

        if self.params.has_key('script') and \
           os.access(self.params['script'], os.X_OK):

            # Allow default with all operations and no specific
            # parameters per operation.  The convention here is
            # to store the first letter in self.cap, but anything
            # unambiguous would do.
            if len(self.params) == 1:
                self.cap = ['a','c','l','f']
                log.debug("Authenticator: adding all capabilities to %s", me)
            else:
                msg = "Authenticator: adding %s capability to %s"
                for cap in ("auth", "change", "list", "find"):
                    if self.params.has_key(cap):
                        log.debug(msg % (cap, me))
                        self.cap.append(cap[0])
            self.valid = True
        else:
            log.error('Authenticator: script parameter missing or target file '\
                      'not executable in %s', me)

    def _gen_input(self, op, *args):
        if op in self.params and len(self.params[op]) > 0:
            args = (self.params[op],)+args
        return ",".join(["%s" % x for x in args])

    def authenticate(self, username, password):
        me = self.__class__.__name__
        if 'a' in self.cap:
            log.debug("Authenticator: authenticate in %s" % me)
            # Use nameless pipes to pass parameters.  
            # If they are passed as arguments they show up in the output 
            # of ps, etc.  This way is secure.
            # Note, the call to communicate causes an EOF on stdin
            try:
                cmd = [self.params['script']]
                args = self._gen_input("auth", username, password)
                res = subprocess.Popen(cmd, 
                                       stdin=PIPE, stdout=PIPE, stderr=PIPE)
                out, err = res.communicate(input=args)
                log.debug("Authenticator: authenticate, script returned "\
                              "%s, %s, exitcode %s", out, err, res.returncode)
            except:
                log.error("Authenticator: authenticate, "\
                          "exception running script, return False")
                return False

            if res.returncode == 0:
                _syslog.log("cumin: authenticated user %s via script" % username)
                return True
        else:
            log.debug("Authenticator: 'auth' not supported by script")
        return False

    def find_user(self, username):
        me = self.__class__.__name__
        if 'f' in self.cap:
            log.debug("Authenticator: executing find_user in %s" % me)
            # Use nameless pipes to pass parameters.  
            # If they are passed as arguments they show up in the output 
            # of ps, etc.  This way is secure.
            # Note, the call to communicate causes an EOF on stdin
            try:
                cmd = [self.params['script']]
                args = self._gen_input("find", username)
                res = subprocess.Popen(cmd, 
                                       stdin=PIPE, stdout=PIPE, stderr=PIPE)
                out, err = res.communicate(input=args)
                log.debug("Authenticator: find_user, script returned "\
                              "%s, %s, exitcode %s", out, err, res.returncode)
            except:
                log.error("Authenticator: find_user, "\
                          "exception running script, return False")
                return False

            if res.returncode == 0:
                return True
        else:
            log.debug("Authenticator: 'find' not supported by script")
        return False

    def batch_import(self):
        if 'l' in self.cap:
            log.debug("Authenticator: batch import in %s",
                      self.__class__.__name__)
            # Use nameless pipes to pass parameters.  
            # If they are passed as arguments they show up in the output 
            # of ps, etc.  This way is secure.
            # Note, the call to communicate causes an EOF on stdin
            try:
                cmd = [self.params['script']]
                args = self._gen_input("list")
                res = subprocess.Popen(cmd, 
                                       stdin=PIPE, stdout=PIPE, stderr=PIPE)
                out, err = res.communicate(input=args)
                log.debug("Authenticator: batch import, script returned "\
                      "%s, %s, exitcode %s", out, err, res.returncode)
            except:
                log.error("Authenticator: batch_import, "\
                          "exception running script, return False")
                return []. False

            return out.split(','), False
        else:
            log.debug("Authenticator: 'list' not supported by script")
        return [], False

    def change_pw(self, user, newpass, oldpass):
        if 'c' in self.cap:
            me = self.__class__.__name__
            log.debug("Authenticator: change password in %s" % me)

            # Use nameless pipes to pass parameters.  
            # If they are passed as arguments they show up in the output 
            # of ps, etc.  This way is secure.
            # Note, the call to communicate causes an EOF on stdin
            try:
                cmd = [self.params['script']]
                args = self._gen_input("change", user, newpass, oldpass)
                res = subprocess.Popen(cmd, 
                                       stdin=PIPE, stdout=PIPE, stderr=PIPE)
                out, err = res.communicate(args)
                log.debug("Authenticator: change password, script returned "\
                          "%s, %s, exitcode %s", out, err, res.returncode)
            except:
                log.error("Authenticator: change_pw, "\
                          "exception running script, return False")
                return False

            if res.returncode == 0:
                _syslog.log("cumin: change password via script for user %s" % user)
                return True
        else:
            log.debug("Authenticator: 'change' not supported by script")
        return False

if have_ldap:
    authen_map = {'ldap': CuminAuthenticatorLDAP,
                  'ldaps': CuminAuthenticatorLDAP,
                  'script': CuminAuthenticatorScript}
else:
    authen_map = {'script': CuminAuthenticatorScript}

class CuminAuthenticator(object):
    def __init__(self, app, log_authentication=True):
        self.authenticators=[]
        self.app = app
        _syslog.log_auth = log_authentication
        log.info("Initializing %s", self)
        if not have_ldap:
            log.info("Authenticator: import of ldap modules failed, "\
                     "ldap mechanism not available")
        for authmech in app.authmech:
            # let the 'internal' word be used here since it has been
            # on the trunk for a while.  It means nothing, since the
            # internal database will always be consulted first.
            if authmech not in ("internal", ""):
                # Allow initial ldap= to be skipped
                try:
                    if authmech.startswith("ldap://"): 
                        mechname = "ldap"
                        authmech = "ldap=" + authmech
                    elif authmech.startswith("ldaps://"):
                        mechname = "ldaps"
                        authmech = "ldaps=" + authmech
                    else:
                        mechname = authmech.split('=',1)[0]
                    classname = authen_map[mechname]
                except KeyError:
                    log.error("Authenticator: unsupported authenticator type %s",
                              mechname)
                    continue

                c = classname(authmech, self.app)
                if c.valid:
                    self.authenticators.append(c)
                log.info("Authenticator: adding auth mechanism %s %s" \
                          % (mechname, c.valid and "succeeded" or "failed"))

    def batch_import(self, backend, output_on=False):
        numusers = 0
        numconflicts = 0
        errors = False
        import_list = []
        log.debug("Authenticator: calling batch import")
        try:
            classname = authen_map[backend]
        except KeyError:
            log.error("Authenticator: batch import, unsupported authenticator "\
                      "type '%s'", backend)
            errors = True

        if not errors:
            try:
                idx = [x.__class__.__name__ for x in self.authenticators]
                idx = idx.index(classname.__name__)
            except ValueError:
                log.error("Authenticator: batch import, authenticator "\
                          "not configured '%s'", backend)
                errors = True

        if not errors:
            users, errors = self.authenticators[idx].batch_import()
            for imp in users:
                import_list.append(imp)

        if len(import_list) > 0:
            try:
                conn = self.app.database.get_connection()
                cursor = conn.cursor()
                role = self.app.admin.get_role(cursor, "user")
                for importuser in import_list:
                    try:
                        user = self.app.admin.add_user(cursor, importuser, "")
                        if output_on:
                            print("Importing user %s" % importuser)
                        self.app.admin.add_assignment(cursor, user, role)
                        conn.commit()
                        numusers += 1
                    except IntegrityError:
                        if output_on:
                            print("Import failed, a user called '%s' "\
                                      "already exists" % importuser)
                        numconflicts += 1
                        conn.rollback()                        
            finally:
                conn.close()
        return numusers, numconflicts, errors

    def authenticate(self, username, password):
        cursor = self.app.database.get_read_cursor()
        cls = self.app.model.com_redhat_cumin.User
        user = cls.get_object(cursor, name=username)
        if user is None or len(user.password) == 0:
            res = False
            log.debug("Authenticator: authenticating external user")
            if len(self.authenticators) == 0:
                log.debug("Authenticator: no external mechanisms available")
            for authenticator in self.authenticators:
                log.debug("Authenticator: authenticate, try %s", authenticator)
                res = authenticator.authenticate(username, password)
                if res:
                    break
            log.debug("Authenticator: authentication %s for external user" \
                      % (res and "succeeded" or "failed"))
            msg = "cumin: authentication %s for external user %s" \
                    % (res and "succeeded" or "failed", username)
        else:
            res = crypt(password, user.password) == user.password
            log.debug("Authenticator: authentication %s for user" \
                      % (res and "succeeded" or "failed"))
            msg = "cumin: authentication %s for user %s" \
                    % (res and "succeeded" or "failed", username)
        _syslog.log(msg)
        return user, res

    def find_user(self, username):
        # Like authenticate, but find_user only confirms the
        # existence of a user.  We are not concerned with password here.
        log.debug("Authenticator: calling find_user")
        cursor = self.app.database.get_read_cursor()
        cls = self.app.model.com_redhat_cumin.User
        user = cls.get_object(cursor, name=username)
        res = user and len(user.password) > 0
        if not res:
            # Try to find the user externally
            log.debug("Authenticator: finding external user")
            if len(self.authenticators) == 0:
                log.debug("Authenticator: no external mechanisms available")
            for authenticator in self.authenticators:
                log.debug("Authenticator: find_user, try %s", authenticator)
                res = authenticator.find_user(username)
                if res:
                    break
        return user, res

    def update_password(self, username, oldpassword, newpassword):
        status = False
        message = ""
        log.debug("Authenticator: calling update_password")
        conn = self.app.database.get_connection()
        try:
            cursor = conn.cursor()
            cls = self.app.model.com_redhat_cumin.User
            user = cls.get_object(cursor, name=username)
            if user is None or user.password == "":
                # Disable change password for external users
                message = "Change password is not allowed for external users"

                #for authenticator in self.authenticators:
                #    status = authenticator.authenticate(username, oldpassword)
                #    if status:
                #        status = authenticator.change_pw(username, 
                #                                        oldpassword, newpassword)
                #        if not status:
                #            message = "Could not change password"
                #        break
                #if not status and message == "":
                #    message = "The password is incorrect"

            else:
                status = crypt(oldpassword, user.password) == user.password
                if status:
                    user.password = crypt_password(newpassword)
                    user.save(cursor)
                    conn.commit()
                    _syslog.log("cumin: updated password for user %s" % username)
                else:
                    message = "The password is incorrect"
        finally:
            conn.close()
        return status, message
