#include <iostream>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <algorithm>
#include <queue>
#include <stack>
#include <memory>
#include <cstring>

// Fast C++ implementation of graph operations for Code Archaeologist
// This provides high-performance graph building and queries

// DLL Export macro for Windows
#ifdef _WIN32
    #define DLL_EXPORT __declspec(dllexport)
#else
    #define DLL_EXPORT
#endif

// Trace event structure matching Python
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
private:
    std::unordered_map<std::string, std::unordered_set<std::string>> adj_list;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> node_attrs;
    std::unordered_map<std::string, std::unordered_map<std::string, std::string>> edge_attrs;

public:
    void add_node(const std::string& node_id,
                  const std::string& type = "",
                  const std::string& function = "",
                  const std::string& filename = "",
                  int lineno = 0,
                  const std::string& event = "",
                  const std::string& code = "",
                  const std::string& language = "python") {
        if (adj_list.find(node_id) == adj_list.end()) {
            adj_list[node_id] = std::unordered_set<std::string>();
        }
        node_attrs[node_id]["type"] = type;
        node_attrs[node_id]["function"] = function;
        node_attrs[node_id]["filename"] = filename;
        node_attrs[node_id]["lineno"] = std::to_string(lineno);
        node_attrs[node_id]["event"] = event;
        node_attrs[node_id]["code"] = code;
        node_attrs[node_id]["language"] = language;
    }

    void add_edge(const std::string& from, const std::string& to, const std::string& type = "call") {
        adj_list[from].insert(to);
        edge_attrs[from + "->" + to]["type"] = type;
    }

    // Fast function listing
    std::vector<std::string> list_functions() const {
        std::vector<std::string> functions;
        for (const auto& [node_id, attrs] : node_attrs) {
            auto type_it = attrs.find("type");
            auto func_it = attrs.find("function");
            if (type_it != attrs.end() && func_it != attrs.end() &&
                type_it->second == "event" && !func_it->second.empty()) {
                functions.push_back(func_it->second);
            }
        }
        // Remove duplicates
        std::sort(functions.begin(), functions.end());
        auto last = std::unique(functions.begin(), functions.end());
        functions.erase(last, functions.end());
        return functions;
    }

    // Fast callers query
    std::vector<std::string> get_callers(const std::string& function_name) const {
        std::vector<std::string> callers;
        for (const auto& [node_id, neighbors] : adj_list) {
            for (const std::string& neighbor : neighbors) {
                if (node_attrs.find(neighbor) != node_attrs.end()) {
                    const auto& attrs = node_attrs.at(neighbor);
                    auto func_it = attrs.find("function");
                    if (func_it != attrs.end() && func_it->second == function_name) {
                        if (node_attrs.find(node_id) != node_attrs.end()) {
                            const auto& caller_attrs = node_attrs.at(node_id);
                            auto caller_func_it = caller_attrs.find("function");
                            if (caller_func_it != caller_attrs.end() && !caller_func_it->second.empty()) {
                                callers.push_back(caller_func_it->second);
                            }
                        }
                    }
                }
            }
        }
        std::sort(callers.begin(), callers.end());
        auto last = std::unique(callers.begin(), callers.end());
        callers.erase(last, callers.end());
        return callers;
    }

    std::vector<std::string> get_callees(const std::string& function_name) const {
        std::vector<std::string> callees;
        for (const auto& [node_id, neighbors] : adj_list) {
            if (node_attrs.find(node_id) == node_attrs.end()) {
                continue;
            }
            const auto& attrs = node_attrs.at(node_id);
            auto func_it = attrs.find("function");
            auto type_it = attrs.find("type");
            if (func_it == attrs.end() || type_it == attrs.end()) {
                continue;
            }
            if (type_it->second != "event" || func_it->second != function_name) {
                continue;
            }

            for (const std::string& neighbor : neighbors) {
                if (node_attrs.find(neighbor) == node_attrs.end()) {
                    continue;
                }
                const auto& neighbor_attrs = node_attrs.at(neighbor);
                auto neighbor_type_it = neighbor_attrs.find("type");
                auto neighbor_func_it = neighbor_attrs.find("function");
                if (neighbor_type_it != neighbor_attrs.end() && neighbor_func_it != neighbor_attrs.end() &&
                    neighbor_type_it->second == "event" && !neighbor_func_it->second.empty()) {
                    callees.push_back(neighbor_func_it->second);
                }
            }
        }
        std::sort(callees.begin(), callees.end());
        auto last = std::unique(callees.begin(), callees.end());
        callees.erase(last, callees.end());
        return callees;
    }

    std::vector<std::string> get_affected(const std::string& function_name) const {
        std::vector<std::string> affected;
        std::unordered_set<std::string> visited;
        std::queue<std::string> q;

        for (const auto& [node_id, attrs] : node_attrs) {
            auto func_it = attrs.find("function");
            auto type_it = attrs.find("type");
            if (func_it != attrs.end() && type_it != attrs.end() &&
                type_it->second == "event" && func_it->second == function_name) {
                q.push(node_id);
                visited.insert(node_id);
            }
        }

        while (!q.empty()) {
            std::string current = q.front();
            q.pop();

            if (adj_list.find(current) == adj_list.end()) {
                continue;
            }

            for (const auto& neighbor : adj_list.at(current)) {
                if (visited.find(neighbor) != visited.end()) {
                    continue;
                }
                visited.insert(neighbor);
                q.push(neighbor);

                if (node_attrs.find(neighbor) != node_attrs.end()) {
                    const auto& attrs = node_attrs.at(neighbor);
                    auto func_it = attrs.find("function");
                    auto type_it = attrs.find("type");
                    if (func_it != attrs.end() && type_it != attrs.end() &&
                        type_it->second == "event" && !func_it->second.empty() &&
                        func_it->second != function_name) {
                        affected.push_back(func_it->second);
                    }
                }
            }
        }

        std::sort(affected.begin(), affected.end());
        auto last = std::unique(affected.begin(), affected.end());
        affected.erase(last, affected.end());
        return affected;
    }

    // Fast path finding using BFS
    std::vector<std::vector<std::string>> find_paths(const std::string& start, const std::string& end, int max_depth = 10) const {
        std::vector<std::vector<std::string>> paths;
        if (adj_list.find(start) == adj_list.end() || adj_list.find(end) == adj_list.end()) {
            return paths;
        }

        std::queue<std::vector<std::string>> q;
        std::unordered_set<std::string> visited;
        q.push({start});

        while (!q.empty() && paths.size() < 100) {  // Limit results
            std::vector<std::string> current_path = q.front();
            q.pop();

            std::string current = current_path.back();

            if (current_path.size() > max_depth) continue;

            if (current == end) {
                paths.push_back(current_path);
                continue;
            }

            if (visited.find(current) != visited.end()) continue;
            visited.insert(current);

            if (adj_list.find(current) != adj_list.end()) {
                for (const std::string& neighbor : adj_list.at(current)) {
                    std::vector<std::string> new_path = current_path;
                    new_path.push_back(neighbor);
                    q.push(new_path);
                }
            }
        }

        return paths;
    }

    // Get graph statistics
    std::pair<size_t, size_t> get_stats() const {
        size_t nodes = adj_list.size();
        size_t edges = 0;
        for (const auto& [_, neighbors] : adj_list) {
            edges += neighbors.size();
        }
        return {nodes, edges};
    }

    // ===== DATA FLOW QUERIES (Week 2) =====

    // Find all functions that write to a specific variable
    std::vector<std::string> get_functions_that_write_to_variable(const std::string& var_name) const {
        std::vector<std::string> functions;
        for (const auto& [node_id, attrs] : node_attrs) {
            auto type_it = attrs.find("type");
            if (type_it == attrs.end() || type_it->second != "variable") continue;

            auto name_it = attrs.find("name");
            if (name_it == attrs.end() || name_it->second != var_name) continue;

            // This is the variable node, find functions that write to it
            for (const auto& [func_id, func_neighbors] : adj_list) {
                if (func_neighbors.find(node_id) != func_neighbors.end()) {
                    // Check if this is a "write" edge
                    auto edge_type_it = edge_attrs.find(func_id + "->" + node_id);
                    if (edge_type_it != edge_attrs.end()) {
                        auto edge_type = edge_type_it->second.find("type");
                        if (edge_type != edge_type_it->second.end() && edge_type->second == "write") {
                            auto func_name_it = node_attrs.find(func_id);
                            if (func_name_it != node_attrs.end()) {
                                auto func_attr = func_name_it->second.find("function");
                                if (func_attr != func_name_it->second.end() && !func_attr->second.empty()) {
                                    functions.push_back(func_attr->second);
                                }
                            }
                        }
                    }
                }
            }
        }
        std::sort(functions.begin(), functions.end());
        auto last = std::unique(functions.begin(), functions.end());
        functions.erase(last, functions.end());
        return functions;
    }

    // Find all functions that read from a specific variable
    std::vector<std::string> get_functions_that_read_from_variable(const std::string& var_name) const {
        std::vector<std::string> functions;
        for (const auto& [node_id, attrs] : node_attrs) {
            auto type_it = attrs.find("type");
            if (type_it == attrs.end() || type_it->second != "variable") continue;

            auto name_it = attrs.find("name");
            if (name_it == attrs.end() || name_it->second != var_name) continue;

            // This is the variable node, find functions that read from it
            for (const auto& [func_id, func_neighbors] : adj_list) {
                if (func_neighbors.find(node_id) != func_neighbors.end()) {
                    // Check if this is a "read" edge
                    auto edge_type_it = edge_attrs.find(func_id + "->" + node_id);
                    if (edge_type_it != edge_attrs.end()) {
                        auto edge_type = edge_type_it->second.find("type");
                        if (edge_type != edge_type_it->second.end() && edge_type->second == "read") {
                            auto func_name_it = node_attrs.find(func_id);
                            if (func_name_it != node_attrs.end()) {
                                auto func_attr = func_name_it->second.find("function");
                                if (func_attr != func_name_it->second.end() && !func_attr->second.empty()) {
                                    functions.push_back(func_attr->second);
                                }
                            }
                        }
                    }
                }
            }
        }
        std::sort(functions.begin(), functions.end());
        auto last = std::unique(functions.begin(), functions.end());
        functions.erase(last, functions.end());
        return functions;
    }

    // Find data path from input variable to output variable
    std::vector<std::vector<std::string>> find_data_path(const std::string& start_var, const std::string& end_var, int max_depth = 10) const {
        std::vector<std::vector<std::string>> paths;

        // Find start and end variable nodes
        std::string start_node, end_node;
        for (const auto& [node_id, attrs] : node_attrs) {
            auto type_it = attrs.find("type");
            if (type_it == attrs.end() || type_it->second != "variable") continue;

            auto name_it = attrs.find("name");
            if (name_it != attrs.end()) {
                if (name_it->second == start_var) start_node = node_id;
                if (name_it->second == end_var) end_node = node_id;
            }
        }

        if (start_node.empty() || end_node.empty()) return paths;

        // BFS to find paths through functions
        std::queue<std::pair<std::vector<std::string>, int>> q;
        q.push({{start_node}, 0});
        std::unordered_set<std::string> visited;

        while (!q.empty() && paths.size() < 100) {
            auto [current_path, depth] = q.front();
            q.pop();

            if (depth > max_depth) continue;

            std::string current = current_path.back();

            if (current == end_node) {
                // Convert node IDs to readable names
                std::vector<std::string> readable_path;
                for (const auto& node : current_path) {
                    auto it = node_attrs.find(node);
                    if (it != node_attrs.end()) {
                        auto name_it = it->second.find("name");
                        auto func_it = it->second.find("function");
                        if (name_it != it->second.end()) {
                            readable_path.push_back(name_it->second);
                        } else if (func_it != it->second.end()) {
                            readable_path.push_back(func_it->second);
                        } else {
                            readable_path.push_back(node);
                        }
                    } else {
                        readable_path.push_back(node);
                    }
                }
                paths.push_back(readable_path);
                continue;
            }

            if (visited.find(current) != visited.end()) continue;
            visited.insert(current);

            auto adj_it = adj_list.find(current);
            if (adj_it != adj_list.end()) {
                for (const auto& neighbor : adj_it->second) {
                    std::vector<std::string> new_path = current_path;
                    new_path.push_back(neighbor);
                    q.push({new_path, depth + 1});
                }
            }
        }

        return paths;
    }

    // Build graph from trace events
    static std::unique_ptr<FastGraph> build_from_events(const std::vector<TraceEvent>& events) {
        auto graph = std::make_unique<FastGraph>();

        for (const auto& event : events) {
            std::string id_str = event.id ? event.id : "";
            std::string event_str = event.event ? event.event : "";
            std::string function_str = event.function ? event.function : "";
            std::string filename_str = event.filename ? event.filename : "";
            std::string code_str = event.code ? event.code : "";
            std::string parent_str = event.parent ? event.parent : "";
            std::string language_str = event.language ? event.language : "python";

            graph->add_node(id_str, "event", function_str, filename_str,
                          event.lineno, event_str, code_str, language_str);

            if (!parent_str.empty()) {
                graph->add_edge(parent_str, id_str, "call");
            }

            // Add variable nodes and data flow edges
            for (size_t i = 0; i < event.writes_count; ++i) {
                if (event.writes && event.writes[i]) {
                    std::string var = event.writes[i];
                    std::string var_id = "var:" + var;
                    graph->add_node(var_id, "variable", "", "", 0, "", "", "variable");
                    graph->add_edge(id_str, var_id, "writes");
                }
            }

            for (size_t i = 0; i < event.reads_count; ++i) {
                if (event.reads && event.reads[i]) {
                    std::string var = event.reads[i];
                    std::string var_id = "var:" + var;
                    graph->add_node(var_id, "variable", "", "", 0, "", "", "variable");
                    graph->add_edge(var_id, id_str, "reads");
                }
            }
        }

        return graph;
    }
};

// C interface for Python integration
extern "C" {
    DLL_EXPORT FastGraph* create_graph(const TraceEvent* events, size_t count) {
        std::vector<TraceEvent> event_vec(events, events + count);
        return FastGraph::build_from_events(event_vec).release();
    }

    DLL_EXPORT void delete_graph(FastGraph* graph) {
        delete graph;
    }

    static char** allocate_string_array(const std::vector<std::string>& items, size_t* count) {
        *count = items.size();
        char** result = new char*[*count];
        for (size_t i = 0; i < *count; ++i) {
            result[i] = new char[items[i].size() + 1];
            strcpy(result[i], items[i].c_str());
        }
        return result;
    }

    DLL_EXPORT char** get_functions(FastGraph* graph, size_t* count) {
        auto functions = graph->list_functions();
        return allocate_string_array(functions, count);
    }

    DLL_EXPORT char** get_callers(FastGraph* graph, const char* function_name, size_t* count) {
        auto callers = graph->get_callers(function_name ? function_name : "");
        return allocate_string_array(callers, count);
    }

    DLL_EXPORT char** get_callees(FastGraph* graph, const char* function_name, size_t* count) {
        auto callees = graph->get_callees(function_name ? function_name : "");
        return allocate_string_array(callees, count);
    }

    DLL_EXPORT char** get_affected(FastGraph* graph, const char* function_name, size_t* count) {
        auto affected = graph->get_affected(function_name ? function_name : "");
        return allocate_string_array(affected, count);
    }

    DLL_EXPORT void free_string_array(char** arr, size_t count) {
        for (size_t i = 0; i < count; ++i) {
            delete[] arr[i];
        }
        delete[] arr;
    }

    DLL_EXPORT size_t get_node_count(FastGraph* graph) {
        return graph->get_stats().first;
    }

    DLL_EXPORT size_t get_edge_count(FastGraph* graph) {
        return graph->get_stats().second;
    }

    // ===== DATA FLOW C INTERFACE (Week 2) =====
    DLL_EXPORT char** get_functions_that_write_to_variable(FastGraph* graph, const char* var_name, size_t* count) {
        auto functions = graph->get_functions_that_write_to_variable(var_name ? var_name : "");
        return allocate_string_array(functions, count);
    }
    
    DLL_EXPORT char** get_functions_that_read_from_variable(FastGraph* graph, const char* var_name, size_t* count) {
        auto functions = graph->get_functions_that_read_from_variable(var_name ? var_name : "");
        return allocate_string_array(functions, count);
    }
    
    DLL_EXPORT char** find_data_path(FastGraph* graph, const char* start_var, const char* end_var, size_t* path_count, size_t** path_lengths) {
        auto paths = graph->find_data_path(start_var ? start_var : "", end_var ? end_var : "", 10);
        
        *path_count = paths.size();
        if (paths.empty()) {
            *path_lengths = nullptr;
            return nullptr;
        }
        
        // Calculate total items
        size_t total_items = 0;
        for (const auto& path : paths) {
            total_items += path.size();
        }
        
        // Allocate result array (flattened)
        char** result = new char*[total_items];
        *path_lengths = new size_t[paths.size()];
        
        size_t idx = 0;
        for (size_t i = 0; i < paths.size(); ++i) {
            (*path_lengths)[i] = paths[i].size();
            for (const auto& item : paths[i]) {
                result[idx] = new char[item.size() + 1];
                strcpy(result[idx], item.c_str());
                ++idx;
            }
        }
        
        return result;
    }
}