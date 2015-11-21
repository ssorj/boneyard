from new import instancemethod
from threading import RLock

class Model(object):
    def __init__(self):
        self.indexes = dict()
        self.mclasses = dict()
        self.__lock = RLock();

    def get_index(self, cls):
        return self.indexes.setdefault(cls, dict())

    def lock(self):
        self.__lock.acquire()

    def unlock(self):
        self.__lock.release()

    def get_object(self, mclass, id):
        self.get_index(mclass).get(id)

class ModelClass(object):
    def __init__(self, model, name):
        self.model = model
        self.name = name
        self.endpoints = set()

class ModelAssociation(object):
    def __init__(self, model, name):
        self.model = model
        self.name = name
        self.endpoints = set()

    def add_endpoint(self, mclass, name, multiplicity):
        if not isinstance(mclass, ModelClass):
            raise TypeError()

        if multiplicity not in ("0..1", "0..n"):
            raise Exception("Multiplicity not recognized")

        if len(self.endpoints) > 1:
            raise Exception("Too many endpoints")

        endpoint = self.Endpoint()
        endpoint.name = name
        endpoint.multiplicity = multiplicity

        self.endpoints.add(endpoint)
        endpoint.association = self

        mclass.endpoints.add(endpoint)
        endpoint.mclass = mclass

        return endpoint

    class Endpoint(object):
        def __init__(self):
            self.association = None
            self.mclass = None

            self.name = None
            self.multiplicity = None

        def other(self):
            for end in self.association.endpoints:
                if end is not self:
                    return end

        def is_scalar(self):
            return self.multiplicity == "0..1"

        def set_scalar(self, this, that):
            this.__dict__[self.name] = that

        def get_scalar(self, this):
            return this.__dict__[self.name]

        def items(self, this):
            return this.__dict__[self.name + "_set"]

        def add(self, this, that):
            if self.is_scalar():
                self.set_scalar(this, that)
            else:
                self.items(this).add(that)

        def remove(self, this, that):
            if self.is_scalar():
                self.set_scalar(this, None)
            else:
                self.items(this).remove(that)

        def object_items(self, this):
            return self.items(this)

        def add_object(self, this, that):
            this.lock()
            try:
                self.add(this, that)

                that.lock()
                try:
                    self.other().add(that, this)
                finally:
                    that.unlock()
            finally:
                this.unlock()

        def remove_object(self, this, that):
            this.lock()
            try:
                self.remove(this, that)

                that.lock()
                try:
                    self.other().remove(that, this)
                finally:
                    that.unlock()
            finally:
                this.unlock()

        def get_object(self, this):
            return self.get_scalar(this)

        def set_object(self, this, new_that):
            this.lock()
            try:
                old_that = self.get_scalar(this)

                if old_that != None:
                    old_that.lock()
                    try:
                        self.other().remove(old_that, this)
                    finally:
                        old_that.unlock()

                self.set_scalar(this, new_that)

                if new_that != None:
                    new_that.lock()
                    try:
                        self.other().add(new_that, this)
                    finally:
                        new_that.unlock()
            finally:
                this.unlock()

class ModelObject(object):
    sequence = 100

    def __init__(self, model, mclass):
        self.model = model
        self.mclass = mclass
        self.__lock = RLock()

        for end in self.mclass.endpoints:
            if end.is_scalar():
                self.add_scalar_attributes(end)
            else:
                self.add_set_attributes(end)

        self.lock()
        try:
            self.__class__.sequence += 1
            self.id = self.__class__.sequence
            model.get_index(self.mclass)[self.id] = self
        finally:
            self.unlock()

    def lock(self):
        self.__lock.acquire()

    def unlock(self):
        self.__lock.release()

    def setmethod(self, name, func):
        if not hasattr(self, name):
            method = instancemethod(func, self, self.__class__)
            setattr(self, name, method)

    def add_set_attributes(this, end):
        setattr(this, end.name + "_set", set())

        def items_method(self): return end.object_items(this)
        this.setmethod(end.name + "_items", items_method)

        def do_add_method(self, that):
            if that == None:
                raise Exception()

            end.add_object(this, that)

        this.setmethod("do_add_" + end.name, do_add_method)

        def add_method(self, that): do_add_method(self, that)
        this.setmethod("add_" + end.name, add_method)

        def do_remove_method(self, that):
            if that == None:
                raise Exception()

            end.remove_object(this, that)

        this.setmethod("do_remove_" + end.name, do_remove_method)

        def remove_method(self, that): do_remove_method(self, that)
        this.setmethod("remove_" + end.name, remove_method)

    def add_scalar_attributes(this, end):
        end.set_scalar(this, None)

        def get_method(self): return end.get_object(this)
        this.setmethod("get_" + end.name, get_method)

        def set_method(self, that): end.set_object(this, that)
        this.setmethod("set_" + end.name, set_method)

    # Note that this doesn't go through the add_someobject methods
    def remove(self):
        self.lock()
        try:
            for end in self.mclass.endpoints:
                this = self

                if end.is_scalar():
                    end.set_object(this, None)
                else:
                    for that in end.items(this).copy():
                        end.remove_object(this, that)

            del self.model.get_index(self.mclass)[self.id]
        finally:
            self.unlock()

    def __str__(self):
        return self.__class__.__name__ + "(" + str(self.id) + ")"

class TestModel(Model):
    def __init__(self):
        super(TestModel, self).__init__()

        self.order = ModelClass(self, self.Order)
        self.item = ModelClass(self, self.Item)

        self.assoc = ModelAssociation(self, "order_item")
        self.assoc.add_endpoint(self.order, "item", "0..n")
        self.assoc.add_endpoint(self.item, "order", "0..1")

    class Order(ModelObject):
        def __init__(self, model):
            super(TestModel.Order, self).__init__(model, model.order)

    class Item(ModelObject):
        def __init__(self, model):
            super(TestModel.Item, self).__init__(model, model.item)

    def test(self):
        def results(heading):
            print heading
            for item in order.item_set:
                print "  item", item, "item.order", item.order

        item0 = self.Item(self)
        item1 = self.Item(self)
        item2 = self.Item(self)

        order = self.Order(self)

        order.add_item(item0)
        order.add_item(item1)
        order.add_item(item2)

        results("beginning state")

        order.remove_item(item0)

        results("remove item0 from order.items")

        item1.set_order(order)

        results("remove order from item1.order")

        order.add_item(item1)

        results("a")

        item1.set_order(None)

        results("b")

        item1.set_order(order)

        results("c")

        item1.remove()

        results("d")

if __name__ == "__main__":
    TestModel().test()
