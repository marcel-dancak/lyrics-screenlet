#include <limits.h>
#include <Python.h>
#include <pygtk-2.0/pygobject.h>
#include <gtk/gtk.h>
#include <gdk/gdkx.h>
#include <X11/Xlib.h>
#include <X11/Xatom.h>

static PyObject*
set_icon_geometry  (PyObject *self, PyObject *args)
{
PyGObject *pyGtkWindow;
GdkWindow *window;
int        x;
int        y;
int        width;
int        height;

if (!PyArg_ParseTuple(args, "Oiiii", &pyGtkWindow, &x, &y, &width, &height)) {
		printf("wrong arguments\n");
		return Py_None;
	}
	window = GTK_WIDGET(pyGtkWindow->obj)->window;
	//printf("%d [%d, %d, %d, %d]\n", GDK_WINDOW_XID (window), x, y, width, height);
	
	gulong data[4] = {x, y, width, height};
	
	XChangeProperty (GDK_WINDOW_XDISPLAY(window), GDK_WINDOW_XID (window),
		gdk_x11_get_xatom_by_name_for_display (gdk_drawable_get_display (window),
		"_NET_WM_ICON_GEOMETRY"), XA_CARDINAL, 32, PropModeReplace, (guchar *)&data, 4);
		 
	return Py_None;
}

static PyMethodDef minimize_methods[] = {

    {"set_icon_geometry",  set_icon_geometry, METH_VARARGS, "descriptions later"},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

PyMODINIT_FUNC init_minimize(void)
{
    PyObject *m;

    m = Py_InitModule("_minimize", minimize_methods);
    if (m == NULL)
        return;
}
