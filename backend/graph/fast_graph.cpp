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
    FastGraph* create_graph(const TraceEvent* events, size_t count) {
        std::vector<TraceEvent> event_vec(events, events + count);
        return FastGraph::build_from_events(event_vec).release();
    }

    void delete_graph(FastGraph* graph) {
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

    char** get_functions(FastGraph* graph, size_t* count) {
        auto functions = graph->list_functions();
        return allocate_string_array(functions, count);
    }

    char** get_callers(FastGraph* graph, const char* function_name, size_t* count) {
        auto callers = graph->get_callers(function_name ? function_name : "");
        return allocate_string_array(callers, count);
    }

    char** get_callees(FastGraph* graph, const char* function_name, size_t* count) {
        auto callees = graph->get_callees(function_name ? function_name : "");
        return allocate_string_array(callees, count);
    }

    char** get_affected(FastGraph* graph, const char* function_name, size_t* count) {
        auto affected = graph->get_affected(function_name ? function_name : "");
        return allocate_string_array(affected, count);
    }

    void free_string_array(char** arr, size_t count) {
        for (size_t i = 0; i < count; ++i) {
            delete[] arr[i];
        }
        delete[] arr;
    }

    size_t get_node_count(FastGraph* graph) {
        return graph->get_stats().first;
    }

    size_t get_edge_count(FastGraph* graph) {
        return graph->get_stats().second;
    }
}