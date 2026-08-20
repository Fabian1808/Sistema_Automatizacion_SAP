class FakeElement:
    def __init__(self, path):
        self.path = path
        self.Text = ""
        self.events = []

    def press(self):
        self.events.append("press")

    def SetFocus(self):
        self.events.append("focus")

    def sendVKey(self, key):
        self.events.append(f"vkey:{key}")

    def maximize(self):
        self.events.append("maximize")

    def __getattr__(self, name):
        return ""


class FakeSession:
    def __init__(self):
        self.Busy = False
        self._elements = {}
        self.ActiveWindow = FakeElement("wnd[0]")
        self.transactions = []

    def findById(self, path):
        if path not in self._elements:
            self._elements[path] = FakeElement(path)
        return self._elements[path]

    def StartTransaction(self, tcode):
        self.transactions.append(tcode)


class FailingSession:
    Busy = False

    def __init__(self):
        self.ActiveWindow = FakeElement("wnd[0]")

    def findById(self, path):
        raise RuntimeError("COM error")

    def StartTransaction(self, tcode):
        raise RuntimeError("COM error")