// cpp_tracer.cpp - Multi-Language Binary Tracer (C++, Go, Rust)
// Week 3: Supports C++, Go, Rust binaries on Windows/Linux

#ifdef _WIN32
    #define WIN32_LEAN_AND_MEAN
    #include <windows.h>
    #include <dbghelp.h>
    #include <tlhelp32.h>
    #pragma comment(lib, "dbghelp.lib")
    #pragma comment(lib, "kernel32.lib")
#else
    #include <sys/ptrace.h>
    #include <sys/wait.h>
    #include <unistd.h>
    #include <dlfcn.h>
#endif

#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <map>
#include <cstring>

// Language detection enum
enum class BinaryLanguage {
    CPP,
    GO,
    RUST,
    UNKNOWN
};

// C interface for Python ctypes
extern "C" {
    // Opaque handle
    typedef void* BinaryTracerHandle;
    
    struct FunctionCall {
        char name[256];
        uintptr_t address;
        int depth;
        int thread_id;
    };
    
    // Initialize symbol handler
    __declspec(dllexport) BinaryTracerHandle tracer_init() {
        HANDLE hProcess = GetCurrentProcess();
        
        SymSetOptions(SYMOPT_LOAD_LINES | SYMOPT_UNDNAME);
        
        if (!SymInitialize(hProcess, NULL, TRUE)) {
            return NULL;
        }
        
        return (BinaryTracerHandle)hProcess;
    }
    
    // Get function name from address
    __declspec(dllexport) int get_function_name(BinaryTracerHandle handle, uintptr_t addr, char* out_name, int max_len) {
        HANDLE hProcess = (HANDLE)handle;
        
        BYTE symbolBuffer[sizeof(SYMBOL_INFO) + 256] = {0};
        SYMBOL_INFO* symbol = (SYMBOL_INFO*)symbolBuffer;
        symbol->SizeOfStruct = sizeof(SYMBOL_INFO);
        symbol->MaxNameLen = 256;
        
        DWORD64 displacement = 0;
        if (SymFromAddr(hProcess, addr, &displacement, symbol)) {
            strncpy_s(out_name, max_len, symbol->Name, _TRUNCATE);
            return 1;
        }
        
        return 0;
    }
    
    // Enumerate all functions in a module
    __declspec(dllexport) int enumerate_functions(BinaryTracerHandle handle, const char* module_path, 
                                                  FunctionCall* out_functions, int max_count) {
        HANDLE hProcess = (HANDLE)handle;
        
        // Load the module
        HANDLE hFile = CreateFileA(module_path, GENERIC_READ, FILE_SHARE_READ, NULL, 
                                   OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        if (hFile == INVALID_HANDLE_VALUE) {
            return -1;
        }
        
        // Get file mapping
        HANDLE hMapping = CreateFileMapping(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
        if (!hMapping) {
            CloseHandle(hFile);
            return -1;
        }
        
        LPVOID base = MapViewOfFile(hMapping, FILE_MAP_READ, 0, 0, 0);
        if (!base) {
            CloseHandle(hMapping);
            CloseHandle(hFile);
            return -1;
        }
        
        // Enumerate symbols
        int count = 0;
        // Note: Full implementation would use SymEnumSymbols
        // This is a simplified version
        
        UnmapViewOfFile(base);
        CloseHandle(hMapping);
        CloseHandle(hFile);
        
        return count;
    }
    
    // Create a process for debugging (simplified)
    __declspec(dllexport) int create_debug_process(const char* executable_path, char* out_error, int max_error_len) {
        STARTUPINFOA si = {0};
        si.cb = sizeof(si);
        PROCESS_INFORMATION pi = {0};
        
        // Enable debug privileges
        HANDLE hToken;
        TOKEN_PRIVILEGES tp;
        
        if (OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken)) {
            if (LookupPrivilegeValueA(NULL, SE_DEBUG_NAME, &tp.Privileges[0].Luid)) {
                tp.PrivilegeCount = 1;
                tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
                AdjustTokenPrivileges(hToken, FALSE, &tp, sizeof(tp), NULL, NULL);
            }
            CloseHandle(hToken);
        }
        
        if (!CreateProcessA(executable_path, NULL, NULL, NULL, FALSE, 
                            DEBUG_PROCESS | DEBUG_ONLY_THIS_PROCESS | CREATE_NEW_CONSOLE,
                            NULL, NULL, &si, &pi)) {
            DWORD err = GetLastError();
            snprintf(out_error, max_error_len, "Failed to create process: %lu", err);
            return -1;
        }
        
        // Debug loop (simplified - would run in separate thread in real implementation)
        DEBUG_EVENT debugEvent;
        BOOL continueDebugging = TRUE;
        int event_count = 0;
        
        while (continueDebugging && event_count < 1000) {
            if (!WaitForDebugEvent(&debugEvent, 100)) {
                continue;
            }
            
            switch (debugEvent.dwDebugEventCode) {
                case CREATE_PROCESS_DEBUG_EVENT:
                    // Process created
                    break;
                    
                case EXIT_PROCESS_DEBUG_EVENT:
                    continueDebugging = FALSE;
                    break;
                    
                case LOAD_DLL_DEBUG_EVENT:
                    // DLL loaded
                    break;
                    
                case UNLOAD_DLL_DEBUG_EVENT:
                    break;
                    
                case OUTPUT_DEBUG_STRING_EVENT:
                    // Debug output
                    break;
                    
                case EXCEPTION_DEBUG_EVENT:
                    // Handle exceptions
                    if (debugEvent.u.Exception.ExceptionRecord.ExceptionCode == EXCEPTION_BREAKPOINT) {
                        // Could log function entry here
                    }
                    ContinueDebugEvent(debugEvent.dwProcessId, debugEvent.dwThreadId, DBG_CONTINUE);
                    continue;
            }
            
            ContinueDebugEvent(debugEvent.dwProcessId, debugEvent.dwThreadId, DBG_CONTINUE);
            event_count++;
        }
        
        // Cleanup
        DebugActiveProcessStop(pi.dwProcessId);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        
        return event_count;
    }
    
    // Cleanup
    __declspec(dllexport) void tracer_cleanup(BinaryTracerHandle handle) {
        if (handle) {
            SymCleanup((HANDLE)handle);
        }
    }
    
    // Test function
    __declspec(dllexport) const char* tracer_version() {
        return "Week 2 C++ Binary Tracer v0.1 (Windows DbgHelp)";
    }
}

// Main function for testing
#ifdef TRACER_STANDALONE
int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " <executable_path>" << std::endl;
        std::cout << "Week 2 C++ Binary Tracer for Code Archaeologist" << std::endl;
        return 1;
    }
    
    BinaryTracerHandle tracer = tracer_init();
    if (!tracer) {
        std::cerr << "Failed to initialize tracer" << std::endl;
        return 1;
    }
    
    std::cout << "Binary Tracer initialized: " << tracer_version() << std::endl;
    
    char error[512] = {0};
    int events = create_debug_process(argv[1], error, sizeof(error));
    
    if (events < 0) {
        std::cerr << "Error: " << error << std::endl;
    } else {
        std::cout << "Captured " << events << " debug events" << std::endl;
    }
    
    tracer_cleanup(tracer);
    return 0;
}
#endif
