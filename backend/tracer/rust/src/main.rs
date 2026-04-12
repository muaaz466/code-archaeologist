use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::io::{self, Write};
use std::path::Path;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};
use chrono::Local;
use tracing::{info, span, Level};
use tracing_subscriber::{fmt, layer::SubscriberExt, util::SubscriberInitExt, Layer};

/// TraceEvent represents a single trace event (Python-compatible format)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceEvent {
    pub id: String,
    pub event: String,      // "call", "return", "exception", "line"
    pub function: String,
    pub filename: String,
    pub lineno: u32,
    pub code: String,
    pub parent: Option<String>,
    pub language: String,
    pub reads: Vec<String>,
    pub writes: Vec<String>,
    #[serde(rename = "timestamp_ns")]
    pub timestamp_ns: u64,
    #[serde(rename = "thread_id")]
    pub thread_id: u64,
}

/// MethodInfo represents method metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MethodInfo {
    pub signature: String,
    pub class_name: String,
    pub method_name: String,
    pub parameter_count: u32,
    pub modifiers: u32,
}

/// TraceOutput represents the complete trace output
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceOutput {
    pub language: String,
    pub version: String,
    pub week: u32,
    #[serde(rename = "event_count")]
    pub event_count: usize,
    #[serde(rename = "method_count")]
    pub method_count: usize,
    pub timestamp: String,
    pub events: Vec<TraceEvent>,
    pub methods: Vec<MethodInfo>,
}

static EVENT_ID: AtomicU64 = AtomicU64::new(0);

fn generate_id() -> String {
    let id = EVENT_ID.fetch_add(1, Ordering::SeqCst);
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos() as u64;
    format!("rust_{}_{}", id, timestamp)
}

fn get_thread_id() -> u64 {
    // Get current thread ID
    std::thread::current().id().as_u64() as u64
}

fn trace_fn<F, R>(name: &str, file: &str, line: u32, f: F) -> R
where
    F: FnOnce() -> R,
{
    let id = generate_id();
    let parent = None; // Simplified - in real implementation, track call stack
    
    // Emit call event
    let call_event = TraceEvent {
        id: id.clone(),
        event: "call".to_string(),
        function: name.to_string(),
        filename: file.to_string(),
        lineno: line,
        code: format!("fn {}()", name),
        parent,
        language: "rust".to_string(),
        reads: vec![],
        writes: vec![],
        timestamp_ns: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos() as u64,
        thread_id: get_thread_id(),
    };
    
    // Log via tracing
    let span = span!(Level::INFO, "function", name = %name, file = %file, line = %line);
    let _enter = span.enter();
    info!(target: "codearch", event = "call", function = %name);
    
    // Execute function
    let result = f();
    
    // Emit return event
    let return_id = generate_id();
    info!(target: "codearch", event = "return", function = %name);
    
    result
}

/// Tracer struct to manage tracing state
pub struct Tracer {
    events: Vec<TraceEvent>,
    methods: HashMap<String, MethodInfo>,
    call_stack: Vec<String>,
}

impl Tracer {
    pub fn new() -> Self {
        Tracer {
            events: Vec::new(),
            methods: HashMap::new(),
            call_stack: Vec::new(),
        }
    }
    
    pub fn hook_call(&mut self, function: &str, filename: &str, lineno: u32) -> String {
        let id = generate_id();
        
        let parent = self.call_stack.last().cloned();
        
        let event = TraceEvent {
            id: id.clone(),
            event: "call".to_string(),
            function: function.to_string(),
            filename: filename.to_string(),
            lineno,
            code: format!("fn {}()", function),
            parent,
            language: "rust".to_string(),
            reads: vec![],
            writes: vec![],
            timestamp_ns: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos() as u64,
            thread_id: get_thread_id(),
        };
        
        self.events.push(event);
        self.call_stack.push(id.clone());
        
        // Register method
        if !self.methods.contains_key(function) {
            self.methods.insert(
                function.to_string(),
                MethodInfo {
                    signature: format!("{}::{}", filename, function),
                    class_name: std::path::Path::new(filename)
                        .parent()
                        .and_then(|p| p.file_name())
                        .and_then(|n| n.to_str())
                        .unwrap_or("")
                        .to_string(),
                    method_name: function.to_string(),
                    parameter_count: 0,
                    modifiers: 0,
                },
            );
        }
        
        id
    }
    
    pub fn hook_return(&mut self, function: &str) {
        if let Some(parent) = self.call_stack.pop() {
            let event = TraceEvent {
                id: generate_id(),
                event: "return".to_string(),
                function: function.to_string(),
                filename: String::new(),
                lineno: 0,
                code: String::new(),
                parent: Some(parent),
                language: "rust".to_string(),
                reads: vec![],
                writes: vec![],
                timestamp_ns: SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_nanos() as u64,
                thread_id: get_thread_id(),
            };
            
            self.events.push(event);
        }
    }
    
    pub fn write_output(&self, output_path: &str) -> io::Result<()> {
        let methods: Vec<MethodInfo> = self.methods.values().cloned().collect();
        
        let output = TraceOutput {
            language: "rust".to_string(),
            version: "3.0.0".to_string(),
            week: 3,
            event_count: self.events.len(),
            method_count: methods.len(),
            timestamp: Local::now().to_rfc3339(),
            events: self.events.clone(),
            methods,
        };
        
        let json = serde_json::to_string_pretty(&output)?;
        fs::write(output_path, json)?;
        
        println!("✅ Trace written: {} events, {} methods", 
                 output.event_count, output.method_count);
        
        Ok(())
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: rust-tracer <command> [args...]");
        eprintln!("Commands:");
        eprintln!("  trace <binary> [args...]  - Trace a Rust binary");
        eprintln!("  parse <trace.json>          - Parse existing trace");
        std::process::exit(1);
    }
    
    let command = &args[1];
    
    match command.as_str() {
        "trace" => {
            if args.len() < 3 {
                eprintln!("❌ Missing binary path");
                std::process::exit(1);
            }
            
            let binary_path = &args[2];
            let binary_args = &args[3..];
            
            println!("🔍 Tracing: {} {:?}", binary_path, binary_args);
            
            // Set up tracing subscriber
            let file_appender = tracing_subscriber::fmt::layer()
                .with_writer(std::io::stdout)
                .with_target(true);
            
            tracing_subscriber::registry()
                .with(file_appender)
                .init();
            
            // Execute and trace
            let output = std::process::Command::new(binary_path)
                .args(binary_args)
                .env("RUST_LOG", "info")
                .env("CODEARCH_TRACE", "1")
                .output()
                .expect("Failed to execute binary");
            
            io::stdout().write_all(&output.stdout).unwrap();
            io::stderr().write_all(&output.stderr).unwrap();
            
            println!("✅ Tracing complete");
        }
        
        "parse" => {
            if args.len() < 3 {
                eprintln!("❌ Missing trace file path");
                std::process::exit(1);
            }
            
            let trace_file = &args[2];
            
            let data = fs::read_to_string(trace_file)
                .expect("Failed to read trace file");
            
            let output: TraceOutput = serde_json::from_str(&data)
                .expect("Failed to parse trace");
            
            println!("✅ Parsed trace: {} events, {} methods",
                     output.event_count, output.method_count);
            
            // Print first 10 functions
            println!("\n📋 Functions detected:");
            for method in output.methods.iter().take(10) {
                println!("  • {}", method.method_name);
            }
            if output.methods.len() > 10 {
                println!("  ... and {} more", output.methods.len() - 10);
            }
        }
        
        _ => {
            eprintln!("❌ Unknown command: {}", command);
            std::process::exit(1);
        }
    }
}

/// Macro to trace function entry/exit
#[macro_export]
macro_rules! trace_fn {
    ($name:expr, $file:expr, $line:expr) => {
        let _tracer_guard = {
            struct TracerGuard;
            impl Drop for TracerGuard {
                fn drop(&mut self) {
                    // Hook return would go here
                }
            }
            // Hook call would go here
            TracerGuard
        };
    };
}
