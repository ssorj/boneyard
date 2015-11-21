from util import *

log = logging.getLogger("rosemary.sqlfilter")

class SqlFilter(object):
    pass

class SqlComparisonFilter(SqlFilter):
    '''
    Emit a comparison filter for a SQL query.
    
    The filter will be of the form 'this op that'.

    If a cursor generation callback is provided and
    'mogrify' indicates that any of the three arguments
    may need special quoting, the psycopg2.cursor.mogrify()
    routine will be used to produce a filter with
    correctly quoted values.

    If 'gen_cursor' is None or 'mogrify' does not specify
    any values to be quoted, simple concatenation will be done.

    gen_cursor -- callback to retreive a pyscopg2
    cursor, invoked as gen_cursor()

    mogrify -- which values need to be quoted.  This is an
    ordered tuple of booleans corresponding to 'this', 'operator', 
    and 'that'.  The default is False, False, True since 'this'
    and 'operator' typically come directly from code but 'that'
    may originate outside of the program.
    '''
    def __init__(self, this, that, 
                 operator="=", 
                 gen_cursor=None, 
                 mogrify=(False,False,True)):
        
        super(SqlComparisonFilter, self).__init__()

        assert isinstance(operator, str)
        assert len(mogrify) == 3

        self.this = getattr(this, "identifier", this)
        self.that = getattr(that, "identifier", that)
        self.operator = operator
        self.gen_cursor = gen_cursor
        self.mogrify = mogrify
    
    def _mogrify(self):
        pattern = []
        vals = []
        for elem in zip((self.this, self.operator, self.that), self.mogrify):
            if elem[1]:
                # We want to mogrify this
                pattern.append("%s")
                vals.append(elem[0])
            else:
                # make this a literal
                pattern.append(elem[0])
        pattern = " ".join(pattern)
        cursor = self.gen_cursor()
        return cursor.mogrify(pattern, vals)

    def emit(self):
        if self.gen_cursor and True in self.mogrify:
            return self._mogrify()

        return "%s %s %s" % (self.this, 
                             self.operator, 
                             self.that)

class SqlValueFilter(SqlComparisonFilter):
    def __init__(self, this, operator="="):
        that = "%%(%s)s" % this.name
        super(SqlValueFilter, self).__init__(this, that, operator)

class SqlExistenceFilter(SqlFilter):
    def __init__(self, subquery, operator="exists"):
        super(SqlExistenceFilter, self).__init__()

        self.subquery = subquery
        self.operator = operator

    def emit(self):
        return "%s (%s)" % (self.operator, self.subquery)

class SqlLikeFilter(SqlValueFilter):
    BEGINS = "B"
    CONTAINS = "C"
    def __init__(self, this, operator="like"):
        super(SqlLikeFilter, self).__init__(this, operator)

class SqlDateValueFilter(SqlFilter):
    def __init__(self, this, that, operator="="):
        super(SqlDateValueFilter, self).__init__()

        assert isinstance(operator, str)

        self.this = getattr(this, "identifier", this)
        self.that = getattr(that, "identifier", that)
        self.operator = operator

    def emit(self):
        return "date_trunc('day', %s) %s date_trunc('day', date('%s'))" % (self.this, self.operator, self.that)