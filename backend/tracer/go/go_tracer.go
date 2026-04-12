package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"runtime/trace"
	"strings"
	"time"
)

// TraceEvent represents a single trace event matching Python format
type TraceEvent struct {
	ID        string   `json:"id"`
	Event     string   `json:"event"`     // "call", "return", "exception", "line"
	Function  string   `json:"function"`
	Filename  string   `json:"filename"`
	Lineno    int      `json:"lineno"`
	Code      string   `json:"code"`
	Parent    *string  `json:"parent"`
	Language  string   `json:"language"`
	Reads     []string `json:"reads"`
	Writes    []string `json:"writes"`
	Timestamp int64    `json:"timestamp_ns"`
	ThreadID  int64    `json:"thread_id"`
}

// TraceOutput represents the complete trace output
type TraceOutput struct {
	Language     string       `json:"language"`
	Version      string       `json:"version"`
	Week         int          `json:"week"`
	EventCount   int          `json:"event_count"`
	MethodCount  int          `json:"method_count"`
	Timestamp    string       `json:"timestamp"`
	Events       []TraceEvent `json:"events"`
	Methods      []MethodInfo `json:"methods"`
}

// MethodInfo represents method metadata
type MethodInfo struct {
	Signature      string `json:"signature"`
	ClassName      string `json:"className"`
	MethodName     string `json:"methodName"`
	ParameterCount int    `json:"parameterCount"`
	Modifiers      int    `json:"modifiers"`
}

var (
	events      []TraceEvent
	methodSet   = make(map[string]MethodInfo)
	callStack   []string
	eventID     int64
)

func init() {
	runtime.SetCPUProfileRate(1000)
}

// hookCall is called when a function is entered
func hookCall(function, filename string, lineno int) {
	eventID++
	id := fmt.Sprintf("go_%d_%d", eventID, time.Now().UnixNano())
	
	var parent *string
	if len(callStack) > 0 {
		p := callStack[len(callStack)-1]
		parent = &p
	}
	
	event := TraceEvent{
		ID:        id,
		Event:     "call",
		Function:  function,
		Filename:  filename,
		Lineno:    lineno,
		Code:      fmt.Sprintf("func %s()", function),
		Parent:    parent,
		Language:  "go",
		Timestamp: time.Now().UnixNano(),
		ThreadID:  int64(runtime.GoID()),
	}
	
	events = append(events, event)
	callStack = append(callStack, id)
	
	// Register method
	if _, ok := methodSet[function]; !ok {
		methodSet[function] = MethodInfo{
			Signature:      fmt.Sprintf("%s.%s", filename, function),
			ClassName:      filepath.Dir(filename),
			MethodName:     function,
			ParameterCount: 0,
			Modifiers:      0,
		}
	}
}

// hookReturn is called when a function returns
func hookReturn(function string) {
	if len(callStack) > 0 {
		parent := callStack[len(callStack)-1]
		callStack = callStack[:len(callStack)-1]
		
		eventID++
		event := TraceEvent{
			ID:        fmt.Sprintf("go_%d_%d", eventID, time.Now().UnixNano()),
			Event:     "return",
			Function:  function,
			Language:  "go",
			Parent:    &parent,
			Timestamp: time.Now().UnixNano(),
			ThreadID:  int64(runtime.GoID()),
		}
		events = append(events, event)
	}
}

// StartTracing begins tracing
func StartTracing() {
	events = nil
	callStack = nil
	fmt.Println("🔍 Go tracing started...")
}

// StopTracing ends tracing and writes output
func StopTracing(outputFile string) {
	// Build methods slice
	methods := make([]MethodInfo, 0, len(methodSet))
	for _, m := range methodSet {
		methods = append(methods, m)
	}
	
	output := TraceOutput{
		Language:    "go",
		Version:     "3.0.0",
		Week:        3,
		EventCount:  len(events),
		MethodCount: len(methods),
		Timestamp:   time.Now().Format(time.RFC3339),
		Events:      events,
		Methods:     methods,
	}
	
	data, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Failed to marshal trace: %v\n", err)
		return
	}
	
	if outputFile == "" {
		outputFile = "go_trace.json"
	}
	
	err = os.WriteFile(outputFile, data, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Failed to write trace: %v\n", err)
		return
	}
	
	fmt.Printf("✅ Trace written: %d events, %d methods\n", len(events), len(methods))
}

// TraceBinary traces a Go binary execution
func TraceBinary(binaryPath string, args []string) error {
	// Use runtime trace
	f, err := os.Create("runtime.trace")
	if err != nil {
		return err
	}
	defer f.Close()
	
	err = trace.Start(f)
	if err != nil {
		return err
	}
	defer trace.Stop()
	
	// Execute the binary
	cmd := exec.Command(binaryPath, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	
	// Set environment for tracing
	cmd.Env = append(os.Environ(),
		"GODEBUG=nettrace=1",
		"GOTRACE=1",
	)
	
	return cmd.Run()
}

// main entry point for standalone tracer
func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go-tracer <command> [args...]")
		fmt.Println("Commands:")
		fmt.Println("  trace <binary> [args...]  - Trace a Go binary")
		fmt.Println("  parse <trace.json>          - Parse existing trace")
		os.Exit(1)
	}
	
	command := os.Args[1]
	
	switch command {
	case "trace":
		if len(os.Args) < 3 {
			fmt.Println("❌ Missing binary path")
			os.Exit(1)
		}
		binaryPath := os.Args[2]
		args := os.Args[3:]
		
		fmt.Printf("🔍 Tracing: %s %s\n", binaryPath, strings.Join(args, " "))
		err := TraceBinary(binaryPath, args)
		if err != nil {
			fmt.Fprintf(os.Stderr, "❌ Trace failed: %v\n", err)
			os.Exit(1)
		}
		
	case "parse":
		if len(os.Args) < 3 {
			fmt.Println("❌ Missing trace file path")
			os.Exit(1)
		}
		traceFile := os.Args[2]
		
		data, err := os.ReadFile(traceFile)
		if err != nil {
			fmt.Fprintf(os.Stderr, "❌ Failed to read trace: %v\n", err)
			os.Exit(1)
		}
		
		var output TraceOutput
		err = json.Unmarshal(data, &output)
		if err != nil {
			fmt.Fprintf(os.Stderr, "❌ Failed to parse trace: %v\n", err)
			os.Exit(1)
		}
		
		fmt.Printf("✅ Parsed trace: %d events, %d methods\n", 
			output.EventCount, output.MethodCount)
		
	default:
		fmt.Printf("❌ Unknown command: %s\n", command)
		os.Exit(1)
	}
}
