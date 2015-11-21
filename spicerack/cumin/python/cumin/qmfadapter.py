from operator import itemgetter
from wooly.datatable import DataAdapter, DataAdapterField
import logging

log = logging.getLogger("cumin.qmfadapter")
class QmfAdapter(DataAdapter):
    def __init__(self, app):
        super(QmfAdapter, self).__init__()

        self.app = app
        self.default = list()
        self.columns = list()
        self.max_sortable_records = app.max_qmf_table_sort

    def get_count(self, values):
        # This used to make a Qmf call, but all descendent
        # classes overloaded this method and the argument passed in to
        # the constructor that named the method was not a Qmf method
        # name in any case.  Broken somewhere in history, but unused,
        # hence removed.
        raise Exception("Not implemented")

    def get_data(self, values, options):
        data = self.do_get_data(values)

        if isinstance(data, dict):
            rows = self.process_results(data)
        elif isinstance(data, list):
            rows = self.process_list_results(data)
        else:
            rows = []

        rows = self.filter_rows(rows, values, options)
        rows = self.sort_rows(rows, options)
        rows = self.limit_rows(rows, options)

        return rows

    def do_get_data(self, values):
        # This used to make a Qmf call, but all descendent
        # classes overloaded this method and the argument passed in to
        # the constructor that named the method was not a Qmf method
        # name in any case.  Broken somewhere in history, but unused,
        # hence removed.
        raise Exception("Not implemented")

    def process_results(self, results):
        """ take the dict response from the qmf call and return a list of lists """

        records = list()

        if results:
            for key in results:
                row = self.process_record(key, results[key])
                records.append(row)

        return records

    def process_list_results(self, results):
        # the results for this call is a list
        records = list()

        if results:
            for rec in results:
                row = self.process_record(None, rec)
                records.append(row)

        return records

    def process_record(self, key, record):
        field_data = list()
        for column in self.columns:
            try:
                val = record[column.name]
            except KeyError:
                val = 0
            field_data.append(val)
        return field_data

    def filter_rows(self, rows, values, options):
        filtered =  list(rows)
        try:
            session = values["session"]
            for column, vattr, type in options.like_specs:
                compare = vattr.get(session)
                index = column.field.index
                #TODO: handle more than the CONTAINS filter type
                filtered = [x for x in rows 
                                if compare in x[index]]
            rows = filtered
        except:
            log.debug("Filtering rows failed", exc_info=True)

        return rows

    def sort_rows(self, rows, options):
        if len(rows) > self.max_sortable_records:
            return rows

        sort_field = options.sort_field
        rev = options.sort_ascending == False

        return sorted(rows, key=itemgetter(sort_field.index), reverse=rev)

    def limit_rows(self, rows, options):
        # return only the current page
        first_index = options.offset
        last_index = len(rows)
        if options.limit:
            last_index = options.offset + options.limit

        page = rows[first_index:last_index]

        return page
    
    def get_sort_limit(self):
        return self.max_sortable_records

class ObjectQmfAdapter(QmfAdapter):
    def __init__(self, app, cls):
        super(ObjectQmfAdapter, self).__init__(app)

        self.cls = cls
        self.default_field_cls = ObjectQmfField

        self.fields_by_attr = dict()

    def add_like_filter(self, attr):
        # qmf adapters don't need to add the like filter
        # since the filtering is done after the records
        # are returned in filter_rows
        pass

class QmfField(DataAdapterField):
    def __init__(self, adapter, column):
        python_type = column.type.python_type

        super(QmfField, self).__init__(adapter, column.name, python_type)

        self.column = column

        self.adapter.columns.append(column)

class ObjectQmfField(QmfField):
    def __init__(self, adapter, attr):
        assert isinstance(adapter, ObjectQmfAdapter), adapter

        super(ObjectQmfField, self).__init__(adapter, attr.sql_column)

        self.attr = attr

        self.adapter.fields_by_attr[self.attr] = self

    def get_title(self, session):
        return self.attr.title or self.attr.name
