# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals, division

from astropy.coordinates import Longitude, SkyCoord, Angle
from astropy import units as u
import hcam_drivers.utils.widgets as w

import six
if not six.PY3:
    import Tkinter as tk
else:
    import tkinter as tk


class PABox(w.RangedFloat):
    def set(self, value):
        new_val = Longitude(value*u.deg).deg
        w.RangedFloat.set(self, new_val)


class Sexagesimal(tk.Entry):
    def __init__(self, master, ival=0, callback=None, unit='hms', **kw):
        tk.Entry.__init__(self, master, **kw)
        if unit == 'hms':
            self.unit = u.hourangle
        else:
            self.unit = u.deg
        # variable is the thing that's shown in the widget
        self._variable = tk.StringVar()
        # value is the thing that tracks the value, and has a unit
        self._value = Angle(ival, unit=u.deg)
        self._variable.set(self.as_string())
        self._variable.trace("w", self._callback)
        self.config(textvariable=self._variable)
        self.checker = callback
        self.set_unbind()
        self.set_bind()

    def as_string(self):
        if self.unit == u.hourangle:
            return self._value.to_string(unit=self.unit, sep=':', precision=2)
        else:
            return self._value.to_string(unit=self.unit, sep=':', precision=1, alwayssign=True)

    def validate(self, value):
        """
        Applies the validation criteria.
        Returns value, new value, or None if invalid.
        """
        try:
            Angle(value, unit=self.unit)
            return value
        except ValueError:
            return None

    def value(self):
        """
        Returns float value in degrees, if possible, None if not.
        """
        try:
            return self._value.deg
        except:
            return None

    def set(self, num):
        """
        Sets the current value equal to num
        """
        self._value = Angle(num, unit=u.deg)
        self._variable.set(self.as_string())

    @u.quantity_input(quantity=u.deg)
    def add(self, quantity):
        """
        Adds an angle to the value
        """
        newvalue = self._value + quantity
        self.set(newvalue.deg)

    @u.quantity_input(quantity=u.deg)
    def sub(self, quantity):
        """
        Subtracts an angle from the value
        """
        newvalue = self._value - quantity
        self.set(newvalue.deg)

    def ok(self):
        """
        Returns True if OK to use, else False
        """
        try:
            Angle(self._value, unit=u.deg)
            return True
        except ValueError:
            return False

    def enable(self):
        self.configure(state='normal')
        self.set_bind()

    def disable(self):
        self.configure(state='disable')
        self.set_unbind()

    def set_bind(self):
        """
        Sets key bindings.
        """
        self.bind('<Button-1>', lambda e: self.add(0.1*u.arcsec))
        self.bind('<Button-3>', lambda e: self.sub(0.1*u.arcsec))
        self.bind('<Up>', lambda e: self.add(0.1*u.arcsec))
        self.bind('<Down>', lambda e: self.sub(0.1*u.arcsec))
        self.bind('<Shift-Up>', lambda e: self.add(1*u.arcsec))
        self.bind('<Shift-Down>', lambda e: self.sub(1*u.arcsec))
        self.bind('<Control-Up>', lambda e: self.add(10*u.arcsec))
        self.bind('<Control-Down>', lambda e: self.sub(10*u.arcsec))
        self.bind('<Double-Button-1>', self._dadd)
        self.bind('<Double-Button-3>', self._dsub)
        self.bind('<Shift-Button-1>', lambda e: self.add(1*u.arcsec))
        self.bind('<Shift-Button-3>', lambda e: self.sub(1*u.arcsec))
        self.bind('<Control-Button-1>', lambda e: self.add(10*u.arcsec))
        self.bind('<Control-Button-3>', lambda e: self.sub(10*u.arcsec))
        self.bind('<Enter>', self._enter)

    def set_unbind(self):
        """
        Unsets key bindings.
        """
        self.unbind('<Button-1>')
        self.unbind('<Button-3>')
        self.unbind('<Up>')
        self.unbind('<Down>')
        self.unbind('<Shift-Up>')
        self.unbind('<Shift-Down>')
        self.unbind('<Control-Up>')
        self.unbind('<Control-Down>')
        self.unbind('<Double-Button-1>')
        self.unbind('<Double-Button-3>')
        self.unbind('<Shift-Button-1>')
        self.unbind('<Shift-Button-3>')
        self.unbind('<Control-Button-1>')
        self.unbind('<Control-Button-3>')
        self.unbind('<Enter>')

    def _callback(self, *dummy):
        """
        This gets called on any attempt to change the value
        """
        # retrieve the value from the Entry
        value = self._variable.get()
        # run the validation. Returns None if no good
        newvalue = self.validate(value)
        if newvalue is None:
            # Invalid: restores previously stored value
            # no checker run.
            self._variable.set(self.as_string())
        else:
            # Store new value
            self._value = Angle(value, unit=self.unit)
            if self.checker:
                self.checker(*dummy)

    # following are callbacks for bindings
    def _dadd(self, event):
        self.add(0.1*u.arcsec)
        return 'break'

    def _dsub(self, event):
        self.sub(0.1*u.arcsec)
        return 'break'

    def _enter(self, event):
        self.focus()
        self.icursor(tk.END)
