#include <Python.h>
#include <queue>
#include "RtMidi.h"

#ifdef __WINDOWS_MM__
#include <windows.h>
#else
#include <pthread.h>
#endif

#ifndef Py_RETURN_NONE
#define Py_RETURN_NONE Py_INCREF(Py_None); return Py_None;
#endif


extern "C"
{
static PyObject *RtMidiError;


typedef struct 
{
  std::vector<unsigned char> bytes;
  double timestamp;
} midi_message_t;


typedef unsigned int uint;

typedef struct
{
  PyObject_HEAD

  RtMidiIn *rtmidi;
  PyObject *pyCallback;
  int main_thread_id;  
  bool blocking;
  std::queue<midi_message_t> *queue;

#ifdef __WINDOWS_MM__
  HANDLE mutex;
#else
  pthread_mutex_t mutex;
  pthread_cond_t cond;
  pthread_mutex_t cond_mutex;
#endif

} MidiIn;


static void
MidiIn_dealloc(MidiIn *self)
{
#ifdef __WINDOWS_MM__
#else
  pthread_mutex_destroy(&self->mutex);
  pthread_mutex_destroy(&self->cond_mutex);
  pthread_cond_destroy(&self->cond);
#endif
  delete self->rtmidi;
  delete self->queue;
  Py_XDECREF(self->pyCallback);
  self->ob_type->tp_free((PyObject *) self);
}


static PyObject *
MidiIn_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  MidiIn *self;
  self = (MidiIn *) type->tp_alloc(type, 0);
  if(self != NULL) 
    {
      try
        {
          self->rtmidi = new RtMidiIn;
        }
      catch(RtError &error)
        {
          PyErr_SetString(RtMidiError, error.getMessageString());
          Py_DECREF(self);
          return NULL;
        }
    }
  return (PyObject *) self;
}

static int
MidiIn_init(MidiIn *self, PyObject *args, PyObject *kwds)
{
#ifdef __WINDOWS_MM__
#else
  // why??
  pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
  pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
  self->mutex = mutex;
  pthread_mutex_init(&self->mutex, NULL);
  self->cond_mutex = mutex;
  pthread_mutex_init(&self->cond_mutex, NULL);  
  self->cond = cond;
  pthread_cond_init(&self->cond, NULL);
#endif
  self->pyCallback = 0;
  self->main_thread_id = -1;
  self->blocking = false;
  self->queue = new std::queue<midi_message_t>;
  return 0;
}


void rtmidi_blocking_cb(double stamp, 
                        std::vector<unsigned char> *bytes,
                        void *userData)
{
  MidiIn *self = (MidiIn *) userData;
  midi_message_t message;

  for(uint i=0; i < bytes->size(); i++)
    message.bytes.push_back((*bytes)[i]);
  message.timestamp = stamp;


#ifdef __WINDOWS_MM__
#else
  pthread_mutex_lock(&self->mutex);
  self->queue->push(message);
  pthread_mutex_unlock(&self->mutex);
  pthread_cond_broadcast(&self->cond);
#endif
}


static PyObject *
MidiIn_openPort(MidiIn *self, PyObject *args)
{
  int port;
  PyObject *blocking = NULL;

  if(!PyArg_ParseTuple(args, "i|O", &port, &blocking))
    return NULL;

  /*
  if(port == 0)
    return PyErr_Format(RtMidiError, 
			"opening device 0 locks my system, and it may lock yours, too!");
  */
  if(blocking == Py_True)
    {
      self->rtmidi->setCallback(rtmidi_blocking_cb, self);
      self->blocking = true;
    }
  else
    {
      self->blocking = false;
    }

  try
    {
      self->rtmidi->openPort(port);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());
    }

  Py_RETURN_NONE;
}


static PyObject *
MidiIn_openVirtualPort(MidiIn *self, PyObject *args)
{
  char *name = NULL;
  PyObject *blocking = NULL;

  if(!PyArg_ParseTuple(args, "|sO", &name, &blocking))
    return NULL;

  if(blocking == Py_True)
    {
      self->rtmidi->setCallback(rtmidi_blocking_cb, self);
      self->blocking = true;
    }
  else
    {
      self->blocking = false;
    }

  if(name == NULL)
    {
      try
        {
          self->rtmidi->openVirtualPort();
        }
      catch(RtError &error)
        {
          return PyErr_Format(RtMidiError, error.getMessageString());
        }
    }
  else
    {
      try
        {
          self->rtmidi->openVirtualPort(name);
        }
      catch(RtError &error)
        {
          return PyErr_Format(RtMidiError, error.getMessageString());
        }
    }

  Py_RETURN_NONE;
}



void rtmidi_GIL_callback(double timestamp, std::vector<unsigned char> *message, void *opaque)
{
  PyObject *result;
  PyObject *args;
  PyObject *pyTimestamp;
  MidiIn *self = (MidiIn *) opaque;

  PyGILState_STATE gil_state = PyGILState_Ensure();

  args = PyTuple_New(message->size() + 1);
  if(args == 0)
    goto callback_fail;

  for(uint i=0; i < message->size(); i++)
    {
      PyObject *pyByte = Py_BuildValue("B", (*message)[i]);
      if(pyByte == 0)
	goto callback_fail;
      if(PyTuple_SetItem(args, i, pyByte) != 0)
	{
	  Py_DECREF(pyByte);
	  goto callback_fail;
	}
    }

  pyTimestamp = Py_BuildValue("d", timestamp);
  if(pyTimestamp == 0)
    goto callback_fail;
  if(PyTuple_SetItem(args, message->size(), pyTimestamp) != 0)
    {
      Py_DECREF(pyTimestamp);
      goto callback_fail;
    }

  result = PyEval_CallObject(self->pyCallback, args);
  if(result == NULL)
    {
callback_fail:
      printf("error calling callback\n");
      PyErr_Format(RtMidiError, "error calling callback");
      PyThreadState_SetAsyncExc(self->main_thread_id, RtMidiError);
    }

  Py_XDECREF(args);
  PyGILState_Release(gil_state); 
}


static PyObject *
MidiIn_setCallback(MidiIn *self, PyObject *args)
{
  PyObject *pyCallback;

  if(!PyArg_ParseTuple(args, "O:setCallback", &pyCallback))
    return NULL;

  if(!PyCallable_Check(pyCallback))
    {
      PyErr_Format(PyExc_TypeError, "parameter must be a callable");
      return NULL;
    }

  Py_XDECREF(self->pyCallback);
  self->pyCallback = pyCallback;
  Py_INCREF(self->pyCallback);

  self->main_thread_id = PyThreadState_Get()->thread_id;
  self->rtmidi->setCallback(rtmidi_GIL_callback, self);

  Py_RETURN_NONE;
}



static PyObject *
MidiIn_cancelCallback(MidiIn *self, PyObject *args)
{
  self->rtmidi->cancelCallback();
  
  Py_RETURN_NONE;
}


static PyObject *
MidiIn_closePort(MidiIn *self, PyObject *args)
{
  self->rtmidi->closePort();

  Py_RETURN_NONE;
}


static PyObject *
MidiIn_getPortCount(MidiIn *self, PyObject *args)
{
  return Py_BuildValue("i", self->rtmidi->getPortCount());
}


static PyObject *
MidiIn_getPortName(MidiIn *self, PyObject *args)
{
  int port;
  std::string name;

  if(!PyArg_ParseTuple(args, "i", &port))
    return NULL;

  try
    {
      name = self->rtmidi->getPortName(port);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());
    }

  return Py_BuildValue("s", name.c_str());
}


static PyObject *
MidiIn_setQueueSizeLimit(MidiIn *self, PyObject *args)
{
  unsigned int queueSize;

  if(!PyArg_ParseTuple(args, "I", &queueSize))
    return NULL;

  self->rtmidi->setQueueSizeLimit(queueSize);

  Py_RETURN_NONE;
}


static PyObject *
MidiIn_ignoreTypes(MidiIn *self, PyObject *args)
{
  PyObject *omidiSysex = Py_True;
  PyObject *omidiTime = Py_True;
  PyObject *omidiSense = Py_True;

  bool midiSysex;
  bool midiTime;
  bool midiSense;

  if(!PyArg_ParseTuple(args, "|OOO", &omidiSysex, &omidiTime, &omidiSense))
    return NULL;

  midiSysex = (omidiSysex == Py_True);
  midiTime = (omidiTime == Py_True);
  midiSense = (omidiSense = Py_True);

  self->rtmidi->ignoreTypes(midiSysex, midiTime, midiSense);

  Py_RETURN_NONE;
}



/*
int cond_timedwait(pthread_cond_t *cond, pthread_mutex_t *mutex, int ms)
{
  struct timeval now;
  struct timespec timeout;

  pthread_mutex_lock(mutex);
  gettimeofday(&now, NULL);
  timeout.tv_sec = now.tv_sec;
  timeout.tv_nsec = now.tv_usec + ms * 1000000;

  return pthread_cond_timedwait(cond, mutex, &timeout);
}
*/

static PyObject *
MidiIn_getMessage(MidiIn *self, PyObject *args)
{
  PyObject *ret;
  double stamp;
  std::vector<unsigned char> message;

  if(self->blocking == false)
    {  
      try
        {
          stamp = self->rtmidi->getMessage( &message );
        }
      catch(RtError &error)
        {
          return PyErr_Format(RtMidiError, error.getMessageString());
        }
    }
  else
    {
      int q_sz;
      midi_message_t msg;


      Py_BEGIN_ALLOW_THREADS

#ifdef __WINDOWS_MM__
#else
      pthread_mutex_lock(&self->mutex);
#endif
      q_sz = self->queue->size();
#ifdef __WINDOWS_MM__
#else
      pthread_mutex_unlock(&self->mutex);
#endif

      if(q_sz <= 0)
        {
          //int ret = ETIMEDOUT;
          //          while(ret == ETIMEDOUT && !self->deleted)
          //while(ret == ETIMEDOUT)
#ifdef __WINDOWS_MM__
#else          
          pthread_cond_wait(&self->cond, &self->cond_mutex);
#endif
            //ret = cond_timedwait(&self->cond, &self->mutex, 10);
          /*
          if(self->deleted)
            {
	      Py_RETURN_NONE;
            }
          */
        }
#ifdef __WINDOWS_MM__
#else
      pthread_mutex_lock(&self->mutex);
#endif
      msg = self->queue->front();
      self->queue->pop();
#ifdef __WINDOWS_MM__
#else
      pthread_mutex_unlock(&self->mutex);
#endif

      message = msg.bytes;
      stamp = msg.timestamp;

      Py_END_ALLOW_THREADS;
    }


  if(message.size())
    {
      ret = PyTuple_New(message.size()+1);
      for(uint i=0; i < message.size(); i++)
        {
          PyObject *obyte = Py_BuildValue("B", message[i]);
          PyTuple_SetItem(ret, i, obyte);
        }
            
      PyObject *ostamp = Py_BuildValue("d", stamp);
      PyTuple_SetItem(ret, message.size(), ostamp);
    }
  else
    {
      ret = PyTuple_New(0);
    }

  return ret;
}


static PyMethodDef MidiIn_methods[] = {
  {"openPort", (PyCFunction) MidiIn_openPort, METH_VARARGS,
   "Open a MIDI input connection. openPort(port, blocking=False)\n"
   "If the optional blocking parameter is passed getMessage will block until a message is available."},

  {"openVirtualPort", (PyCFunction) MidiIn_openVirtualPort, METH_VARARGS,
   "Create a virtual input port, with optional name, to allow software "
   "connections (OS X and ALSA only)."},

  {"setCallback", (PyCFunction) MidiIn_setCallback, METH_VARARGS,
   "Set a callback function to be invoked for incoming MIDI messages."},

  {"cancelCallback", (PyCFunction) MidiIn_cancelCallback, METH_NOARGS,
   "Cancel use of the current callback function (if one exists)."},

  {"closePort", (PyCFunction) MidiIn_closePort, METH_NOARGS,
   "Close an open MIDI connection (if one exists)."},

  {"getPortCount", (PyCFunction) MidiIn_getPortCount, METH_NOARGS,
   "Return the number of available MIDI input ports."},

  {"getPortName", (PyCFunction) MidiIn_getPortName, METH_VARARGS,
   "Return a string identifier for the specified MIDI input port number."},

  {"setQueueSizeLimit", (PyCFunction) MidiIn_setQueueSizeLimit, METH_VARARGS,
   "Set the maximum number of MIDI messages to be saved in the queue."},
  
  {"ignoreTypes", (PyCFunction) MidiIn_ignoreTypes, METH_VARARGS,
   "Specify whether certain MIDI message types should be queued or ignored "
   "during input."},
  
  {"getMessage", (PyCFunction) MidiIn_getMessage, METH_NOARGS,
   "Return the data bytes for the next available MIDI message in"
   "the input queue and return the event delta-time in seconds.\n"
   "This method will block if openPort() was called in blocking mode"},

  {NULL}
};


static PyTypeObject MidiIn_type = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "midi.RtMidiIn",             /*tp_name*/
    sizeof(MidiIn), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor) MidiIn_dealloc,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "Midi input device",           /* tp_doc */
    0,               /* tp_traverse */
    0,               /* tp_clear */
    0,               /* tp_richcompare */
    0,               /* tp_weaklistoffset */
    0,               /* tp_iter */
    0,               /* tp_iternext */
    MidiIn_methods,             /* tp_methods */
    0,              /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)MidiIn_init,      /* tp_init */
    0,                         /* tp_alloc */
    MidiIn_new,                 /* tp_new */
};






typedef struct {
  PyObject_HEAD
  /* Type-specific fields go here. */
  RtMidiOut *rtmidi;
} MidiOut;


static void
MidiOut_dealloc(MidiOut *self)
{
  delete self->rtmidi;
  self->ob_type->tp_free((PyObject *) self);
}


static PyObject *
MidiOut_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  MidiOut *self;
  self = (MidiOut *) type->tp_alloc(type, 0);
  if(self != NULL) 
    {
      try
        {
          self->rtmidi = new RtMidiOut;
        }
      catch(RtError &error)
        {
          PyErr_Format(RtMidiError, error.getMessageString());
          Py_DECREF(self);
          return NULL;
        }
    }
  return (PyObject *) self;
}

static int
MidiOut_init(MidiOut *self, PyObject *args, PyObject *kwds)
{
  return 0;
}


static PyObject *
MidiOut_openPort(MidiOut *self, PyObject *args)
{
  int port = 0;

  if(!PyArg_ParseTuple(args, "|i", &port))
    return NULL;

  try
    {
      self->rtmidi->openPort(port);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());
    }

  Py_INCREF(Py_None);
  return Py_None;
}


/*
static PyObject *
MidiOut_openVirtualPort(MidiOut *self, PyObject *args)
{
  char *name = NULL;

  if(!PyArg_ParseTuple(args, "|s", &name))
    return NULL;

  if(name == NULL)
    {
      try
        {
          self->rtmidi->openVirtualPort();
        }
      catch(RtError &error)
        {
          return PyErr_Format(RtMidiError, error.getMessageString());
        }
    }
  else
    {
      try
        {
          self->rtmidi->openVirtualPort(name);
        }
      catch(RtError &error)
        {
          return PyErr_Format(RtMidiError, error.getMessageString());
        }
    }

  Py_INCREF(Py_None);
  return Py_None;
}
*/

static PyObject *
MidiOut_closePort(MidiOut *self, PyObject *args)
{
  self->rtmidi->closePort();
  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *
MidiOut_getPortCount(MidiOut *self, PyObject *args)
{
  return Py_BuildValue("i", self->rtmidi->getPortCount());
}


static PyObject *
MidiOut_getPortName(MidiOut *self, PyObject *args)
{
  int port;
  std::string name;

  if(!PyArg_ParseTuple(args, "i", &port))
    return NULL;

  try
    {
      name = self->rtmidi->getPortName(port);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());
    }

  return Py_BuildValue("s", name.c_str());
}


static PyObject *
MidiOut_sendMessage(MidiOut *self, PyObject *args)
{
  int i;
  std::vector<unsigned char> message;
  Py_ssize_t size = PyTuple_Size(args);
  if (size < 1)
    return NULL;
  for (i=0; i<size; i++)
    {
      unsigned long b;
      PyObject* arg;
      arg = PyTuple_GetItem(args, i);
      if (!PyInt_Check(arg))
        return PyErr_Format(RtMidiError, "Error: arguments must be integers");
      b = PyInt_AsUnsignedLongMask(arg);
      if (b > 255)
        {
          return PyErr_Format(RtMidiError, "Error: arguments must be 8-bit integers");
        }
      message.push_back((unsigned char)b);
    }

  try
    {
      self->rtmidi->sendMessage(&message);
    }
  catch(RtError &error)
    {
      return PyErr_Format(RtMidiError, error.getMessageString());      
    }

  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef MidiOut_methods[] = {
  {"openPort", (PyCFunction) MidiOut_openPort, METH_VARARGS,
   "Open a MIDI input connection."},

  {"openVirtualPort", (PyCFunction) MidiIn_openVirtualPort, METH_VARARGS,
   "Create a virtual input port, with optional name, to allow software "
   "connections (OS X and ALSA only)."},

  {"closePort", (PyCFunction) MidiOut_closePort, METH_NOARGS,
   "Close an open MIDI connection (if one exists)."},

  {"getPortCount", (PyCFunction) MidiOut_getPortCount, METH_NOARGS,
   "Return the number of available MIDI output ports."},

  {"getPortName", (PyCFunction) MidiOut_getPortName, METH_VARARGS,
   "Return a string identifier for the specified MIDI port type and number."},

  {"sendMessage", (PyCFunction) MidiOut_sendMessage, METH_VARARGS,
   "Immediately send a single message out an open MIDI output port."},

  {NULL}
};


static PyTypeObject MidiOut_type = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "midi.RtMidiOut",             /*tp_name*/
    sizeof(MidiOut), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor) MidiOut_dealloc,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "Midi output device",           /* tp_doc */
    0,               /* tp_traverse */
    0,               /* tp_clear */
    0,               /* tp_richcompare */
    0,               /* tp_weaklistoffset */
    0,               /* tp_iter */
    0,               /* tp_iternext */
    MidiOut_methods,             /* tp_methods */
    0,              /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)MidiOut_init,      /* tp_init */
    0,                         /* tp_alloc */
    MidiOut_new,                 /* tp_new */
};




static PyMethodDef midi_methods[] = {
    {NULL}  /* Sentinel */
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initrtmidi(void) 
{
  PyEval_InitThreads();

  PyObject* module;
  
  if (PyType_Ready(&MidiIn_type) < 0)
    return;
  if (PyType_Ready(&MidiOut_type) < 0)
    return;
  
  module = Py_InitModule3("rtmidi", midi_methods,
			  "RtMidi wrapper.");
  
  Py_INCREF(&MidiIn_type);
  PyModule_AddObject(module, "RtMidiIn", (PyObject *)&MidiIn_type);
  
  Py_INCREF(&MidiOut_type);
  PyModule_AddObject(module, "RtMidiOut", (PyObject *)&MidiOut_type);
  
  RtMidiError = PyErr_NewException("rtmidi.RtError", NULL, NULL);
  Py_INCREF(RtMidiError);
  PyModule_AddObject(module, "RtError", RtMidiError);
}

} // extern "C"
