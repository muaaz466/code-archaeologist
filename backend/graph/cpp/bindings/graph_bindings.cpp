#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>
#include "fast_graph.hpp"

namespace py = pybind11;
using namespace codearch;

PYBIND11_MODULE(fast_graph, m) {
    m.doc() = "Fast C++ Graph Engine for Code Archaeologist";
    
    // Bind TraceEvent struct
    py::class_<TraceEvent>(m, "TraceEvent")
        .def(py::init<>())
        .def_readwrite("id", &TraceEvent::id)
        .def_readwrite("event", &TraceEvent::event)
        .def_readwrite("function", &TraceEvent::function)
        .def_readwrite("filename", &TraceEvent::filename)
        .def_readwrite("lineno", &TraceEvent::lineno)
        .def_readwrite("code", &TraceEvent::code)
        .def_readwrite("parent", &TraceEvent::parent)
        .def_readwrite("language", &TraceEvent::language)
        .def_readwrite("reads", &TraceEvent::reads)
        .def_readwrite("writes", &TraceEvent::writes);
    
    // Bind FastGraph class
    py::class_<FastGraph>(m, "FastGraph")
        .def(py::init<>())
        .def("buildFromTraces", &FastGraph::buildFromTraces,
             "Build graph from trace events")
        .def("getCallers", &FastGraph::getCallers,
             "Get functions that call the target function",
             py::arg("function"))
        .def("getCallees", &FastGraph::getCallees,
             "Get functions called by the target function",
             py::arg("function"))
        .def("findPath", &FastGraph::findPath,
             "Find call path between two functions",
             py::arg("from"), py::arg("to"))
        .def("getAffected", &FastGraph::getAffected,
             "Get all functions affected by changes to target",
             py::arg("function"))
        .def("findDeadCode", &FastGraph::findDeadCode,
             "Find functions with no callers")
        .def("listFunctions", &FastGraph::listFunctions,
             "List all functions in graph")
        .def("nodeCount", &FastGraph::nodeCount,
             "Get number of nodes")
        .def("edgeCount", &FastGraph::edgeCount,
             "Get number of edges")
        .def("density", &FastGraph::density,
             "Get graph density")
        .def("averageFanOut", &FastGraph::averageFanOut,
             "Get average fan-out")
        .def("getWritesTo", &FastGraph::getWritesTo,
             "Get functions that write to variable",
             py::arg("variable"))
        .def("getReadsFrom", &FastGraph::getReadsFrom,
             "Get functions that read from variable",
             py::arg("variable"))
        .def("dataPath", &FastGraph::dataPath,
             "Find data flow path",
             py::arg("from"), py::arg("to"));
}
