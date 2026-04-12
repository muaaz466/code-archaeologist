#pragma once
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <memory>

namespace codearch {

struct TraceEvent {
    std::string id;
    std::string event;
    std::string function;
    std::string filename;
    int lineno;
    std::string code;
    std::string parent;
    std::string language;
    std::vector<std::string> reads;
    std::vector<std::string> writes;
};

struct GraphNode {
    std::string name;
    std::string filename;
    int lineno;
    std::string language;
    std::unordered_set<std::string> callers;
    std::unordered_set<std::string> callees;
    std::vector<std::string> reads;
    std::vector<std::string> writes;
};

class FastGraph {
public:
    FastGraph();
    ~FastGraph();
    
    // Build graph from trace events
    void buildFromTraces(const std::vector<TraceEvent>& events);
    
    // Query operations
    std::vector<std::string> getCallers(const std::string& function) const;
    std::vector<std::string> getCallees(const std::string& function) const;
    std::vector<std::string> findPath(const std::string& from, const std::string& to) const;
    std::vector<std::string> getAffected(const std::string& function) const;
    std::vector<std::string> findDeadCode() const;
    std::vector<std::string> listFunctions() const;
    
    // Graph metrics
    int nodeCount() const;
    int edgeCount() const;
    double density() const;
    double averageFanOut() const;
    
    // Data flow
    std::vector<std::string> getWritesTo(const std::string& variable) const;
    std::vector<std::string> getReadsFrom(const std::string& variable) const;
    std::vector<std::string> dataPath(const std::string& from, const std::string& to) const;
    
private:
    std::unordered_map<std::string, GraphNode> nodes_;
    std::unordered_map<std::string, std::unordered_set<std::string>> edges_;
    std::unordered_map<std::string, std::vector<std::string>> writes_to_;
    std::unordered_map<std::string, std::vector<std::string>> reads_from_;
};

} // namespace codearch
