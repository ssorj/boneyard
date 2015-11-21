import logging
import math

from wooly import Session, Widget
from wooly.util import StringCatalog
from wooly.widgets import RadioModeSet
from wooly.parameters import StringParameter

from cumin.parameters import RosemaryObjectParameter
from cumin.widgets import StateSwitch
from cumin.stat import FlashFullPage
from cumin.objectselector import ObjectSelector, ObjectLinkColumn,\
    ObjectTableColumn, ObjectTable, SelectableSearchObjectTable

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.slotvis")

class SlotOverview(RadioModeSet):
    def __init__(self, app, name):
        super(SlotOverview, self).__init__(app, name)

        self.add_tab(SlotSelector(app, "slots"))

    def render_title(self, session):
        return "Slots"

class SlotSelector(ObjectSelector):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Slot

        super(SlotSelector, self).__init__(app, name, cls)

        frame = "main.grid.slot"
        col = ObjectLinkColumn(app, "name", cls.Name, cls._id, frame)
        self.add_column(col)

        self.add_attribute_column(cls.Activity)
        self.add_attribute_column(cls.State)

        col = ObjectTableColumn(app, cls.LoadAvg.name, cls.LoadAvg)
        self.add_column(col)
        self.table.set_default_sort_column(col)
        
        self.field_param = StringParameter(app, "field_param")
        self.add_parameter(self.field_param)
        
        self.select_input = self.SlotFieldOptions(app, self.field_param)
        self.add_selectable_search_filter(self.select_input)

        self.enable_csv_export()

    def create_table(self, app, name, cls):
        # avoid the checkboxes
        return SelectableSearchObjectTable(app, name, cls)

    def render_title(self, session):
        return "Slot table"
    
    class SlotFieldOptions(SelectableSearchObjectTable.SearchFieldOptions):
        def __init__(self, app, param):
            super(SlotSelector.SlotFieldOptions, self).__init__(app, param)
            self.cls = app.model.com_redhat_grid.Slot
            
        def do_get_items(self, session):
            return [self.cls.Name, self.cls.Activity, self.cls.State, self.cls.LoadAvg]

