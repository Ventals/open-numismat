from PyQt5.QtCore import QSettings


def storeDlgSizeDecorator(original_class):
    # Make a copy of original methods
    orig_init = original_class.__init__
    orig_done = original_class.done

    def __init__(self, *args, **kws):
        orig_init(self, *args, **kws)  # call the original __init__

        settings = QSettings()
        orig_class_name = self.__class__.__name__
        size = settings.value('%s/size' % orig_class_name)
        if size:
            self.resize(size)
        if settings.value('%s/maximized' % orig_class_name, False, type=bool):
            self.showMaximized()

    def done(self, r):
        settings = QSettings()
        orig_class_name = self.__class__.__name__
        settings.setValue('%s/maximized' % orig_class_name, self.isMaximized())
        if not self.isMaximized():
            settings.setValue('%s/size' % orig_class_name, self.size())

        orig_done(self, r)  # call the original done

    # Set the class' methods to the new one
    original_class.__init__ = __init__
    original_class.done = done
    return original_class
