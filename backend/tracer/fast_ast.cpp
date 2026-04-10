#include <windows.h>
#include <dbghelp.h>
#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <stack>
#include <sstream>
#include <iomanip>

#pragma comment(lib, "dbghelp.lib")

struct CallEvent {
    std::string caller;
    std::string callee;
    DWORD threadId;
    ULONGLONG timestamp;
};

class CppTracer {
private:
    HANDLE hProcess;
    DWORD processId;
    std::map<DWORD, std::stack<std::string>> threadStacks; // Thread -> Call stack
    std::vector<CallEvent> events;
    ULONGLONG startTime;
    bool running;
    
    // Symbol handling
    bool symbolsInitialized;

public:
    CppTracer() : hProcess(NULL), processId(0), running(false), symbolsInitialized(false) {
        startTime = GetTickCount64();
    }
    
    ~CppTracer() {
        if (symbolsInitialized) {
            SymCleanup(hProcess);
        }
    }

    bool LoadBinary(const char* exePath, const char* args) {
        STARTUPINFOA si = { sizeof(si) };
        PROCESS_INFORMATION pi;
        
        // Create process in debug mode
        BOOL created = CreateProcessA(
            exePath,
            (LPSTR)args,
            NULL, NULL, FALSE,
            DEBUG_PROCESS | DEBUG_ONLY_THIS_PROCESS,  // Key flag
            NULL, NULL, &si, &pi
        );
        
        if (!created) {
            std::cerr << "Failed to create process: " << GetLastError() << std::endl;
            return false;
        }
        
        hProcess = pi.hProcess;
        processId = pi.dwProcessId;
        
        // Initialize symbol handler
        if (SymInitialize(hProcess, NULL, TRUE)) {
            symbolsInitialized = true;
            SymSetOptions(SYMOPT_LOAD_LINES | SYMOPT_UNDNAME);
        }
        
        running = true;
        return true;
    }

    void Run() {
        DEBUG_EVENT debugEvent;
        
        while (running) {
            // Wait for debug event (breakpoint, exception, etc.)
            if (!WaitForDebugEvent(&debugEvent, 100)) {
                continue; // Timeout, check if we should stop
            }

            DWORD continueStatus = DBG_CONTINUE;
            
            switch (debugEvent.dwDebugEventCode) {
                case EXCEPTION_DEBUG_EVENT: {
                    HandleException(&debugEvent.u.Exception);
                    break;
                }
                
                case CREATE_THREAD_DEBUG_EVENT: {
                    // New thread created
                    break;
                }
                
                case EXIT_THREAD_DEBUG_EVENT: {
                    // Thread exited
                    if (threadStacks.count(debugEvent.dwThreadId)) {
                        threadStacks.erase(debugEvent.dwThreadId);
                    }
                    break;
                }
                
                case LOAD_DLL_DEBUG_EVENT: {
                    // DLL loaded - could hook functions here
                    break;
                }
                
                case EXIT_PROCESS_DEBUG_EVENT: {
                    running = false;
                    break;
                }
            }
            
            ContinueDebugEvent(debugEvent.dwProcessId, debugEvent.dwThreadId, continueStatus);
        }
    }

    void HandleException(EXCEPTION_DEBUG_INFO* exception) {
        if (exception->ExceptionRecord.ExceptionCode == EXCEPTION_BREAKPOINT) {
            // We hit a breakpoint (function entry)
            HANDLE hThread = OpenThread(THREAD_ALL_ACCESS, FALSE, GetCurrentThreadId());
            
            if (hThread) {
                CONTEXT context;
                context.ContextFlags = CONTEXT_CONTROL;
                
                if (GetThreadContext(hThread, &context)) {
                    // Get current instruction pointer
                    #ifdef _WIN64
                    DWORD64 ip = context.Rip;
                    #else
                    DWORD ip = context.Eip;
                    #endif
                    
                    // Resolve symbol
                    std::string funcName = ResolveSymbol(ip);
                    
                    // Record call
                    CallEvent event;
                    event.callee = funcName;
                    event.threadId = GetCurrentThreadId();
                    event.timestamp = GetTickCount64() - startTime;
                    
                    // Get caller from stack
                    if (!threadStacks[GetCurrentThreadId()].empty()) {
                        event.caller = threadStacks[GetCurrentThreadId()].top();
                    } else {
                        event.caller = "entry_point";
                    }
                    
                    events.push_back(event);
                    threadStacks[GetCurrentThreadId()].push(funcName);
                    
                    // TODO: Set breakpoint on RET instruction to capture return
                    // This requires disassembly or symbol lookup for function end
                }
                
                CloseHandle(hThread);
            }
        }
    }

    std::string ResolveSymbol(DWORD64 address) {
        char buffer[sizeof(SYMBOL_INFO) + MAX_SYM_NAME * sizeof(TCHAR)];
        PSYMBOL_INFO symbol = (PSYMBOL_INFO)buffer;
        symbol->SizeOfStruct = sizeof(SYMBOL_INFO);
        symbol->MaxNameLen = MAX_SYM_NAME;
        
        DWORD64 displacement;
        if (SymFromAddr(hProcess, address, &displacement, symbol)) {
            return std::string(symbol->Name);
        }
        
        // Fallback to address
        std::stringstream ss;
        ss << "0x" << std::hex << address;
        return ss.str();
    }

    void SetBreakpoint(const char* functionName) {
        // Find function address by name and set INT 3 breakpoint
        // This requires enumerating symbols or knowing address ahead of time
        
        SYMBOL_INFO symbol;
        symbol.SizeOfStruct = sizeof(SYMBOL_INFO);
        symbol.MaxNameLen = 0;
        
        // Note: SymEnumSymbols would be better here
        // For now, placeholder - you'd enumerate all symbols and set breakpoints
    }

    std::vector<CallEvent> GetEvents() {
        return events;
    }
    
    void Stop() {
        running = false;
    }
};

// C interface for Python ctypes
extern "C" {
    __declspec(dllexport) CppTracer* tracer_create() {
        return new CppTracer();
    }
    
    __declspec(dllexport) int tracer_load(CppTracer* tracer, const char* exe, const char* args) {
        if (!tracer) return 0;
        return tracer->LoadBinary(exe, args) ? 1 : 0;
    }
    
    __declspec(dllexport) void tracer_run(CppTracer* tracer) {
        if (tracer) tracer->Run();
    }
    
    __declspec(dllexport) int tracer_get_event_count(CppTracer* tracer) {
        if (!tracer) return 0;
        return tracer->GetEvents().size();
    }
    
    __declspec(dllexport) void tracer_get_events(CppTracer* tracer, CallEvent* buffer, int maxCount) {
        if (!tracer) return;
        auto events = tracer->GetEvents();
        int count = (maxCount < events.size()) ? maxCount : events.size();
        for (int i = 0; i < count; i++) {
            buffer[i] = events[i];
        }
    }
    
    __declspec(dllexport) void tracer_destroy(CppTracer* tracer) {
        delete tracer;
    }
}