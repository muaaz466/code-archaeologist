#include "fast_graph.hpp"
#include <queue>
#include <stack>
#include <algorithm>

namespace codearch {

FastGraph::FastGraph() {}
FastGraph::~FastGraph() {}

void FastGraph::buildFromTraces(const std::vector<TraceEvent>& events) {
    std::stack<std::string> callStack;
    
    for (const auto& event : events) {
        if (event.event == "call") {
            // Create node if doesn't exist
            if (nodes_.find(event.function) == nodes_.end()) {
                GraphNode node;
                node.name = event.function;
                node.filename = event.filename;
                node.lineno = event.lineno;
                node.language = event.language;
                nodes_[event.function] = node;
            }
            
            // Add caller relationship
            if (!callStack.empty()) {
                std::string caller = callStack.top();
                nodes_[event.function].callers.insert(caller);
                nodes_[caller].callees.insert(event.function);
                edges_[caller].insert(event.function);
            }
            
            // Track data flow
            for (const auto& read : event.reads) {
                nodes_[event.function].reads.push_back(read);
                reads_from_[read].push_back(event.function);
            }
            for (const auto& write : event.writes) {
                nodes_[event.function].writes.push_back(write);
                writes_to_[write].push_back(event.function);
            }
            
            callStack.push(event.function);
        }
        else if (event.event == "return" && !callStack.empty()) {
            callStack.pop();
        }
    }
}

std::vector<std::string> FastGraph::getCallers(const std::string& function) const {
    auto it = nodes_.find(function);
    if (it == nodes_.end()) return {};
    return std::vector<std::string>(it->second.callers.begin(), it->second.callers.end());
}

std::vector<std::string> FastGraph::getCallees(const std::string& function) const {
    auto it = nodes_.find(function);
    if (it == nodes_.end()) return {};
    return std::vector<std::string>(it->second.callees.begin(), it->second.callees.end());
}

std::vector<std::string> FastGraph::findPath(const std::string& from, const std::string& to) const {
    if (nodes_.find(from) == nodes_.end() || nodes_.find(to) == nodes_.end()) {
        return {};
    }
    
    std::unordered_map<std::string, std::string> parent;
    std::queue<std::string> queue;
    std::unordered_set<std::string> visited;
    
    queue.push(from);
    visited.insert(from);
    
    while (!queue.empty()) {
        std::string current = queue.front();
        queue.pop();
        
        if (current == to) {
            // Reconstruct path
            std::vector<std::string> path;
            std::string node = to;
            while (node != from) {
                path.push_back(node);
                node = parent[node];
            }
            path.push_back(from);
            std::reverse(path.begin(), path.end());
            return path;
        }
        
        auto it = edges_.find(current);
        if (it != edges_.end()) {
            for (const auto& neighbor : it->second) {
                if (visited.find(neighbor) == visited.end()) {
                    visited.insert(neighbor);
                    parent[neighbor] = current;
                    queue.push(neighbor);
                }
            }
        }
    }
    
    return {};
}

std::vector<std::string> FastGraph::getAffected(const std::string& function) const {
    std::unordered_set<std::string> affected;
    std::queue<std::string> queue;
    std::unordered_set<std::string> visited;
    
    queue.push(function);
    visited.insert(function);
    
    while (!queue.empty()) {
        std::string current = queue.front();
        queue.pop();
        
        auto it = nodes_.find(current);
        if (it != nodes_.end()) {
            for (const auto& callee : it->second.callees) {
                if (visited.find(callee) == visited.end()) {
                    visited.insert(callee);
                    affected.insert(callee);
                    queue.push(callee);
                }
            }
        }
    }
    
    return std::vector<std::string>(affected.begin(), affected.end());
}

std::vector<std::string> FastGraph::findDeadCode() const {
    std::vector<std::string> dead;
    for (const auto& [name, node] : nodes_) {
        if (node.callers.empty() && !node.name.empty()) {
            dead.push_back(name);
        }
    }
    return dead;
}

std::vector<std::string> FastGraph::listFunctions() const {
    std::vector<std::string> functions;
    for (const auto& [name, _] : nodes_) {
        functions.push_back(name);
    }
    return functions;
}

int FastGraph::nodeCount() const {
    return static_cast<int>(nodes_.size());
}

int FastGraph::edgeCount() const {
    int count = 0;
    for (const auto& [_, edges] : edges_) {
        count += static_cast<int>(edges.size());
    }
    return count;
}

double FastGraph::density() const {
    int n = nodeCount();
    if (n <= 1) return 0.0;
    int e = edgeCount();
    return static_cast<double>(e) / (n * (n - 1));
}

double FastGraph::averageFanOut() const {
    if (nodes_.empty()) return 0.0;
    int total = 0;
    for (const auto& [_, node] : nodes_) {
        total += static_cast<int>(node.callees.size());
    }
    return static_cast<double>(total) / nodes_.size();
}

std::vector<std::string> FastGraph::getWritesTo(const std::string& variable) const {
    auto it = writes_to_.find(variable);
    if (it == writes_to_.end()) return {};
    return it->second;
}

std::vector<std::string> FastGraph::getReadsFrom(const std::string& variable) const {
    auto it = reads_from_.find(variable);
    if (it == reads_from_.end()) return {};
    return it->second;
}

std::vector<std::string> FastGraph::dataPath(const std::string& from, const std::string& to) const {
    // Find path through data flow graph
    auto writers = writes_to_.find(from);
    if (writers == writes_to_.end()) return {};
    
    auto readers = reads_from_.find(to);
    if (readers == reads_from_.end()) return {};
    
    // Find common functions
    std::vector<std::string> path;
    for (const auto& writer : writers->second) {
        if (std::find(readers->second.begin(), readers->second.end(), writer) != readers->second.end()) {
            path.push_back(writer);
        }
    }
    
    return path;
}

} // namespace codearch
