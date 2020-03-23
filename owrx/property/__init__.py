from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Subscription(object):
    def __init__(self, subscriptee, name, subscriber):
        self.subscriptee = subscriptee
        self.name = name
        self.subscriber = subscriber

    def getName(self):
        return self.name

    def call(self, *args, **kwargs):
        self.subscriber(*args, **kwargs)

    def cancel(self):
        self.subscriptee.unwire(self)


class PropertyManager(ABC):
    def __init__(self):
        self.subscribers = []

    @abstractmethod
    def __getitem__(self, item):
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        pass

    @abstractmethod
    def __contains__(self, item):
        pass

    @abstractmethod
    def __dict__(self):
        pass

    def collect(self, *props):
        return PropertyFilter(self, *props)

    def wire(self, callback):
        sub = Subscription(self, None, callback)
        self.subscribers.append(sub)
        return sub

    def wireProperty(self, name, callback):
        sub = Subscription(self, name, callback)
        self.subscribers.append(sub)
        if name in self:
            sub.call(self[name])
        return sub

    def unwire(self, sub):
        try:
            self.subscribers.remove(sub)
        except ValueError:
            # happens when already removed before
            pass
        return self

    def _fireCallbacks(self, name, value):
        for c in self.subscribers:
            try:
                if c.getName() is None:
                    c.call(name, value)
                elif c.getName() == name:
                    c.call(value)
            except Exception as e:
                logger.exception(e)


class PropertyLayer(PropertyManager):
    def __init__(self):
        super().__init__()
        self.properties = {}

    def __contains__(self, name):
        return name in self.properties

    def __getitem__(self, name):
        return self.properties[name]

    def __setitem__(self, name, value):
        if name in self.properties and self.properties[name] == value:
            return
        logger.debug("property change: %s => %s", name, value)
        self.properties[name] = value
        self._fireCallbacks(name, value)

    def __dict__(self):
        return {k: v for k, v in self.properties.items()}


class PropertyFilter(PropertyManager):
    def __init__(self, pm: PropertyManager, *props: str):
        super().__init__()
        self.pm = pm
        self.props = props
        self.pm.wire(self.receiveEvent)

    def receiveEvent(self, name, value):
        if name not in self.props:
            return
        self._fireCallbacks(name, value)

    def __getitem__(self, item):
        if item not in self.props:
            raise KeyError(item)
        return self.pm.__getitem__(item)

    def __setitem__(self, key, value):
        if key not in self.props:
            raise KeyError(key)
        return self.pm.__setitem__(key, value)

    def __contains__(self, item):
        if item not in self.props:
            return False
        return self.pm.__contains__(item)

    def __dict__(self):
        return {k: v for k, v in self.pm.__dict__().items() if k in self.props}


class PropertyStack(PropertyManager):
    def __init__(self):
        super().__init__()
        self.layers = []

    def addLayer(self, priority: int, pm: PropertyManager):
        """
        highest priority = 0
        """
        self.layers.append({"priority": priority, "props": pm})

        def eventClosure(name, value):
            self.receiveEvent(pm, name, value)

        pm.wire(eventClosure)

    def receiveEvent(self, layer, name, value):
        if layer != self._getTopLayer(name):
            return
        self._fireCallbacks(name, value)

    def removeLayer(self, pm: PropertyManager):
        for layer in self.layers:
            if layer["props"] == pm:
                self.layers.remove(layer)

    def _getTopLayer(self, item):
        layers = [la["props"] for la in sorted(self.layers, key=lambda l: l["priority"])]
        for m in layers:
            if item in m:
                return m
        # return top layer by default
        return layers[0]

    def __getitem__(self, item):
        layer = self._getTopLayer(item)
        return layer.__getitem__(item)

    def __setitem__(self, key, value):
        layer = self._getTopLayer(key)
        return layer.__setitem__(key, value)

    def __contains__(self, item):
        layer = self._getTopLayer(item)
        return layer.__contains__(item)

    def __dict__(self):
        keys = [key for l in self.layers for key in l["props"].__dict__().keys()]
        return {k: self.__getitem__(k) for k in keys}
