#ifndef FAST_GRAPH_H
#define FAST_GRAPH_H

#include <vector>
#include <string>
#include <memory>

struct TraceEvent {
    const char* id;
    const char* event;
    const char* function;
    const char* filename;
    int lineno;
    const char* code;
    const char* parent;
    const char* language;
    const char** reads;
    const char** writes;
    size_t reads_count;
    size_t writes_count;
};

class FastGraph {
public:
    void add_node(const std::string& node_id,
                  const std::string& type = "",
                  const std::string& function = "",
                  const std::string& filename = "",
                  int lineno = 0,
                  const std::string& event = "",
                  const std::string& code = "",
                  const std::string& language = "python");

    void add_edge(const std::string& from, const std::string& to, const std::string& type = "call");

    std::vector<std::string> list_functions() const;
    std::vector<std::string> get_callers(const std::string& function_name) const;
    std::vector<std::string> get_callees(const std::string& function_name) const;
    std::vector<std::string> get_affected(const std::string& function_name) const;
    std::vector<std::vector<std::string>> find_paths(const std::string& start, const std::string& end, int max_depth = 10) const;
    std::pair<size_t, size_t> get_stats() const;

    static std::unique_ptr<FastGraph> build_from_events(const std::vector<TraceEvent>& events);
};

// C interface for Python ctypes integration
extern "C" {
    FastGraph* create_graph(const TraceEvent* events, size_t count);
    void delete_graph(FastGraph* graph);
    char** get_functions(FastGraph* graph, size_t* count);
    char** get_callers(FastGraph* graph, const char* function_name, size_t* count);
    char** get_callees(FastGraph* graph, const char* function_name, size_t* count);
    char** get_affected(FastGraph* graph, const char* function_name, size_t* count);
    void free_string_array(char** arr, size_t count);
    size_t get_node_count(FastGraph* graph);
    size_t get_edge_count(FastGraph* graph);
}

#endif // FAST_GRAPH_H