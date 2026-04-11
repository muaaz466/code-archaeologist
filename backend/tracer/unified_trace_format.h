// unified_trace_format.h - Unified Trace Format for Python and C++
// Week 2: Common format for all language traces

#ifndef UNIFIED_TRACE_FORMAT_H
#define UNIFIED_TRACE_FORMAT_H

#include <string>
#include <vector>
#include <cstdint>

namespace code_archaeologist {

// Trace event types
enum class TraceEventType {
    CALL,
    RETURN,
    LINE,
    FUNCTION_ENTRY,
    FUNCTION_EXIT
};

// Language types
enum class LanguageType {
    PYTHON,
    CPP,
    GO,
    RUST,
    UNKNOWN
};

// Variable access info
struct VariableAccess {
    std::string name;
    bool is_read;
    bool is_write;
    std::string type;  // For C++ variables
    uintptr_t address; // Memory location (C++)
};

// Unified Trace Event - Works for Python and C++
struct UnifiedTraceEvent {
    std::string id;
    TraceEventType event_type;
    std::string function_name;
    std::string filename;
    int lineno;
    std::string code_snippet;
    std::string parent_id;
    LanguageType language;
    
    // Variable tracking (Week 2 feature)
    std::vector<std::string> reads;
    std::vector<std::string> writes;
    std::vector<VariableAccess> variable_access;
    
    // C++ binary specific
    uintptr_t function_address;
    uintptr_t return_address;
    std::string module_name;
    
    // Metadata
    int thread_id;
    uint64_t timestamp;
    
    // Constructor
    UnifiedTraceEvent() 
        : lineno(0), language(LanguageType::UNKNOWN),
          function_address(0), return_address(0),
          thread_id(0), timestamp(0) {}
};

// Trace session containing all events
struct TraceSession {
    std::string session_id;
    std::string binary_path;  // For C++ binaries
    std::string source_path;  // For Python files
    std::vector<UnifiedTraceEvent> events;
    LanguageType primary_language;
    
    TraceSession() : primary_language(LanguageType::UNKNOWN) {}
};

// Parser interface
class ITraceParser {
public:
    virtual ~ITraceParser() = default;
    virtual TraceSession parse(const std::string& input_path) = 0;
    virtual bool supports(const std::string& file_extension) = 0;
};

// JSON trace parser (for both Python and C++ traces)
class JSONTraceParser : public ITraceParser {
public:
    TraceSession parse(const std::string& json_file) override;
    bool supports(const std::string& ext) override {
        return ext == ".json";
    }
};

// Python trace converter
class PythonTraceConverter {
public:
    // Convert Python TraceEvent objects to unified format
    static TraceSession convert_from_python_events(
        const std::vector<std::string>& python_events_json);
};

// C++ binary trace converter
class CppTraceConverter {
public:
    // Convert C++ binary trace (from ptrace/gdb) to unified format
    static TraceSession convert_from_cpp_trace(
        const std::string& binary_path,
        const std::vector<uintptr_t>& call_stack);
};

// Data Flow Graph builder
class DataFlowGraphBuilder {
public:
    // Build data flow graph from trace session
    void build(const TraceSession& session);
    
    // Queries
    std::vector<std::string> get_functions_writing_to(const std::string& variable);
    std::vector<std::string> get_functions_reading_from(const std::string& variable);
    std::vector<std::vector<std::string>> find_data_paths(
        const std::string& start_var, 
        const std::string& end_var);
    
private:
    std::map<std::string, std::vector<std::string>> variable_to_functions_write;
    std::map<std::string, std::vector<std::string>> variable_to_functions_read;
};

// C interface for Python ctypes
extern "C" {
    // Parse trace file and return unified events
    struct CTraceEvent {
        char id[512];
        char event_type[32];
        char function[256];
        char filename[512];
        int lineno;
        char language[32];
        char reads[10][64];
        int num_reads;
        char writes[10][64];
        int num_writes;
    };
    
    int parse_trace_file(const char* filepath, CTraceEvent* out_events, int max_events);
    int get_functions_that_write_to_variable(const char* var_name, 
                                               char** out_functions, 
                                               int max_functions);
    int get_functions_that_read_from_variable(const char* var_name,
                                              char** out_functions,
                                              int max_functions);
    int find_data_path(const char* start_var, 
                       const char* end_var,
                       char** out_path,
                       int max_path_length);
}

} // namespace code_archaeologist

#endif // UNIFIED_TRACE_FORMAT_H
